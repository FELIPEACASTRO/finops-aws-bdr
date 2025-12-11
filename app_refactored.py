#!/usr/bin/env python3
"""
FinOps AWS - Web Server para Deploy (Refatorado)
Serve o dashboard e API de análise de custos AWS.
Cobertura: 200+ serviços AWS via ServiceFactory
"""
import os
import sys
import json
import logging
import functools
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Callable

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

# JWT import - optional dependency
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    jwt = None
    JWT_AVAILABLE = False

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import FinOps modules
from finops_aws.core.factories import ServiceFactory, AWSClientFactory
from finops_aws.dashboard import (
    get_dashboard_analysis,
    get_all_regions_analysis,
    get_region_costs,
    get_compute_optimizer_recommendations,
    get_cost_explorer_ri_recommendations,
    get_trusted_advisor_recommendations,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app setup
frontend_dist = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')
app = Flask(__name__, static_folder=frontend_dist, static_url_path='')

# CORS configuration - restrict in production
allowed_origins = os.getenv('CORS_ORIGINS', '*').split(',')
CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

# Rate limiting configuration
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # 1 hour

# Simple in-memory rate limiter
_rate_limit_store: Dict[str, Dict[str, Any]] = {}


def get_client_ip() -> str:
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr or 'unknown'


def rate_limit_check() -> Optional[tuple]:
    """Check rate limit for current client"""
    if not RATE_LIMIT_ENABLED:
        return None
    
    client_ip = get_client_ip()
    now = datetime.now(timezone.utc)
    
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = {
            'count': 1,
            'window_start': now
        }
        return None
    
    client_data = _rate_limit_store[client_ip]
    window_elapsed = (now - client_data['window_start']).total_seconds()
    
    if window_elapsed > RATE_LIMIT_WINDOW:
        # Reset window
        _rate_limit_store[client_ip] = {
            'count': 1,
            'window_start': now
        }
        return None
    
    if client_data['count'] >= RATE_LIMIT_REQUESTS:
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': f'Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s',
            'retry_after': int(RATE_LIMIT_WINDOW - window_elapsed)
        }), 429
    
    client_data['count'] += 1
    return None


def rate_limited(f: Callable) -> Callable:
    """Decorator to apply rate limiting to routes"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        limit_response = rate_limit_check()
        if limit_response:
            return limit_response
        return f(*args, **kwargs)
    return decorated_function


# JWT Authentication (optional - enabled via environment variable)
JWT_SECRET = os.getenv('JWT_SECRET')
JWT_ENABLED = JWT_SECRET is not None and len(JWT_SECRET) > 0 and JWT_AVAILABLE


def jwt_required(f: Callable) -> Callable:
    """Decorator to require JWT authentication"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not JWT_ENABLED:
            return f(*args, **kwargs)
        
        if not JWT_AVAILABLE:
            logger.warning("JWT authentication enabled but PyJWT not installed")
            return f(*args, **kwargs)
        
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


# Cache configuration
_analysis_cache: Dict[str, Any] = {
    'data': None,
    'timestamp': None,
    'ttl_seconds': int(os.getenv('CACHE_TTL', '300'))
}


def get_cached_analysis() -> Dict[str, Any]:
    """Returns cached analysis or executes new one if expired"""
    now = datetime.now(timezone.utc)
    
    if (_analysis_cache['data'] is not None and 
        _analysis_cache['timestamp'] is not None):
        age = (now - _analysis_cache['timestamp']).total_seconds()
        if age < _analysis_cache['ttl_seconds']:
            logger.info(f"Returning cached analysis (age: {age:.0f}s)")
            return _analysis_cache['data']
    
    logger.info("Cache miss - executing new analysis")
    analysis = execute_analysis()
    
    _analysis_cache['data'] = analysis
    _analysis_cache['timestamp'] = now
    
    return analysis


def invalidate_cache() -> None:
    """Invalidates cache to force new analysis"""
    _analysis_cache['data'] = None
    _analysis_cache['timestamp'] = None
    logger.info("Cache invalidated")


def execute_analysis() -> Dict[str, Any]:
    """Execute FinOps analysis using ServiceFactory"""
    try:
        region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        
        # Use existing dashboard analysis
        analysis = get_dashboard_analysis(region=region)
        
        # Add AWS integrations
        integrations = {}
        
        try:
            integrations['compute_optimizer'] = get_compute_optimizer_recommendations()
        except Exception as e:
            logger.warning(f"Compute Optimizer unavailable: {e}")
            integrations['compute_optimizer'] = {'error': str(e)}
        
        try:
            integrations['cost_explorer'] = get_cost_explorer_ri_recommendations()
        except Exception as e:
            logger.warning(f"Cost Explorer RI unavailable: {e}")
            integrations['cost_explorer'] = {'error': str(e)}
        
        try:
            integrations['trusted_advisor'] = get_trusted_advisor_recommendations()
        except Exception as e:
            logger.warning(f"Trusted Advisor unavailable: {e}")
            integrations['trusted_advisor'] = {'error': str(e)}
        
        analysis['integrations'] = integrations
        analysis['generated_at'] = datetime.now(timezone.utc).isoformat()
        analysis['region'] = region
        
        return analysis
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return {
            'error': str(e),
            'status': 'failed',
            'generated_at': datetime.now(timezone.utc).isoformat()
        }


# =============================================================================
# API Routes
# =============================================================================

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


@app.route('/')
def index():
    """Serve React frontend"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/v1/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'version': os.getenv('APP_VERSION', '2.1.0'),
        'jwt_enabled': JWT_ENABLED,
        'rate_limit_enabled': RATE_LIMIT_ENABLED
    })


@app.route('/api/v1/analysis')
@rate_limited
@jwt_required
def get_analysis():
    """Get FinOps analysis results"""
    force_refresh = request.args.get('refresh', 'false').lower() == 'true'
    
    if force_refresh:
        invalidate_cache()
    
    analysis = get_cached_analysis()
    return jsonify(analysis)


@app.route('/api/v1/analysis/refresh', methods=['POST'])
@rate_limited
@jwt_required
def refresh_analysis():
    """Force refresh of analysis cache"""
    invalidate_cache()
    analysis = get_cached_analysis()
    return jsonify({
        'status': 'refreshed',
        'analysis': analysis
    })


@app.route('/api/v1/costs')
@rate_limited
@jwt_required
def get_costs():
    """Get cost data"""
    try:
        factory = ServiceFactory()
        cost_service = factory.get_cost_service()
        
        period = request.args.get('period', '30')
        costs = cost_service.get_all_period_costs()
        
        return jsonify({
            'costs': costs,
            'period_days': int(period),
            'generated_at': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Cost retrieval failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/recommendations')
@rate_limited
@jwt_required
def get_recommendations():
    """Get optimization recommendations"""
    try:
        factory = ServiceFactory()
        optimizer = factory.get_optimizer_service()
        
        recommendations = optimizer.get_all_recommendations()
        
        return jsonify({
            'recommendations': recommendations,
            'count': sum(len(r) for r in recommendations.values() if isinstance(r, list)),
            'generated_at': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Recommendations retrieval failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/multi-region')
@rate_limited
@jwt_required
def get_multi_region():
    """Get multi-region analysis"""
    try:
        regions = get_all_regions_analysis()
        return jsonify({
            'regions': regions,
            'generated_at': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Multi-region analysis failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/notifications')
@rate_limited
@jwt_required
def get_notifications():
    """Get notifications from Cost Anomaly Detection and Budgets"""
    try:
        factory = ServiceFactory()
        notifications = []
        
        # Cost Anomaly Detection
        try:
            anomaly_service = factory.get_costanomalydetection_service()
            if hasattr(anomaly_service, 'get_anomalies'):
                anomalies = anomaly_service.get_anomalies()
                for anomaly in anomalies:
                    notifications.append({
                        'type': 'cost_anomaly',
                        'severity': 'high',
                        'message': f"Cost anomaly detected: {anomaly.get('message', 'Unusual spending pattern')}",
                        'timestamp': anomaly.get('timestamp', datetime.now(timezone.utc).isoformat())
                    })
        except Exception as e:
            logger.warning(f"Cost Anomaly Detection unavailable: {e}")
        
        # Budgets
        try:
            budgets_service = factory.get_budgets_service()
            if hasattr(budgets_service, 'get_budget_alerts'):
                alerts = budgets_service.get_budget_alerts()
                for alert in alerts:
                    notifications.append({
                        'type': 'budget_alert',
                        'severity': 'medium',
                        'message': alert.get('message', 'Budget threshold exceeded'),
                        'timestamp': alert.get('timestamp', datetime.now(timezone.utc).isoformat())
                    })
        except Exception as e:
            logger.warning(f"Budgets service unavailable: {e}")
        
        return jsonify({
            'notifications': notifications,
            'count': len(notifications),
            'generated_at': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Notifications retrieval failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/services')
@rate_limited
@jwt_required
def get_services_list():
    """Get list of analyzed AWS services"""
    from finops_aws.core.factories import AWSServiceType
    
    services = [
        {'name': s.name, 'value': s.value}
        for s in AWSServiceType
    ]
    
    return jsonify({
        'services': services,
        'count': len(services)
    })


@app.route('/api/v1/settings', methods=['GET'])
@rate_limited
@jwt_required
def get_settings():
    """Get current settings"""
    return jsonify({
        'settings': {
            'cache_ttl': _analysis_cache['ttl_seconds'],
            'rate_limit_enabled': RATE_LIMIT_ENABLED,
            'rate_limit_requests': RATE_LIMIT_REQUESTS,
            'rate_limit_window': RATE_LIMIT_WINDOW,
            'jwt_enabled': JWT_ENABLED,
            'default_region': os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }
    })


@app.route('/api/v1/settings', methods=['PUT'])
@rate_limited
@jwt_required
def update_settings():
    """Update settings (runtime only)"""
    try:
        data = request.get_json()
        
        if 'cache_ttl' in data:
            _analysis_cache['ttl_seconds'] = int(data['cache_ttl'])
        
        return jsonify({
            'status': 'updated',
            'settings': {
                'cache_ttl': _analysis_cache['ttl_seconds']
            }
        })
    except Exception as e:
        logger.error(f"Settings update failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 400


# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors - serve React app for client-side routing"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return send_from_directory(app.static_folder, 'index.html')


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}", exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting FinOps AWS server on port {port}")
    logger.info(f"JWT authentication: {'enabled' if JWT_ENABLED else 'disabled'}")
    logger.info(f"Rate limiting: {'enabled' if RATE_LIMIT_ENABLED else 'disabled'}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
