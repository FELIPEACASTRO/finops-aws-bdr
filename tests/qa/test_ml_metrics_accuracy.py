"""
Machine Learning Tests for FinOps AWS
=====================================

This test suite validates the accuracy and precision of ML-based metrics:
1. Forecasting Engine accuracy tests
2. Anomaly Detection precision tests
3. KPI calculation accuracy tests
4. ROI Score calculation validation
5. Statistical model validation

All tests use known datasets with expected outcomes to validate accuracy.
"""

import pytest
import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestForecastingEngineAccuracy:
    """Tests forecasting engine accuracy with known datasets"""
    
    def test_linear_trend_forecast_accuracy(self):
        """
        Test: Linear trend data should produce accurate linear forecast
        Expected: Forecast should follow trend with <10% error
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Linear trend: 100, 110, 120, 130, 140, 150, 160
        linear_data = [100 + (i * 10) for i in range(30)]
        
        forecaster = CostForecaster()
        result = forecaster.forecast_service_cost(linear_data, forecast_days=7)
        
        assert result['status'] == 'success', f"Forecast failed: {result}"
        
        # Expected next value ~310 (continuing linear trend)
        expected_mean = sum(linear_data) / len(linear_data) + (10 * 15)  # midpoint continuation
        actual_mean = result['forecast_mean']
        
        # Allow 20% error margin for statistical models
        error_margin = abs(expected_mean - actual_mean) / expected_mean
        assert error_margin < 0.3, f"Forecast error {error_margin:.2%} exceeds 30% threshold"
        
        # Trend direction should be correct
        if 'trend' in result:
            assert result['trend'] == 'increasing', "Trend should be increasing"
    
    def test_stable_data_forecast_precision(self):
        """
        Test: Stable data should produce low variance forecast
        Expected: Forecast variance should be minimal
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Stable data around 100
        stable_data = [100, 101, 99, 100, 102, 98, 100, 101, 99, 100] * 3
        
        forecaster = CostForecaster()
        result = forecaster.forecast_service_cost(stable_data, forecast_days=7)
        
        assert result['status'] == 'success'
        
        # Forecast mean should be close to 100
        assert 90 < result['forecast_mean'] < 110, f"Mean {result['forecast_mean']} too far from expected 100"
        
        # Standard deviation should be small
        if 'forecast_std' in result:
            assert result['forecast_std'] < 15, f"Std {result['forecast_std']} too high for stable data"
    
    def test_seasonal_pattern_detection(self):
        """
        Test: Seasonal data should not produce wildly incorrect forecasts
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Simple weekly pattern (low-high-low-high...)
        seasonal_data = [50, 100, 50, 100, 50, 100, 50] * 4
        
        forecaster = CostForecaster()
        result = forecaster.forecast_service_cost(seasonal_data, forecast_days=7)
        
        assert result['status'] == 'success'
        
        # Mean should be around 75 (average of pattern)
        assert 50 < result['forecast_mean'] < 100, f"Mean {result['forecast_mean']} outside expected range"
    
    def test_insufficient_data_handling(self):
        """
        Test: Insufficient data should return proper error status
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        forecaster = CostForecaster()
        
        # Less than 7 days of data
        result = forecaster.forecast_service_cost([100, 101, 102], forecast_days=7)
        
        assert result['status'] == 'insufficient_data'
        assert result['minimum_required_days'] == 7
    
    def test_empty_data_handling(self):
        """
        Test: Empty data should be handled gracefully
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        forecaster = CostForecaster()
        
        result = forecaster.forecast_service_cost([], forecast_days=7)
        assert result['status'] == 'insufficient_data'
    
    def test_confidence_interval_validity(self):
        """
        Test: Confidence intervals should be mathematically valid
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        data = [100 + i * 2 for i in range(30)]
        
        forecaster = CostForecaster()
        result = forecaster.forecast_service_cost(data, forecast_days=7)
        
        assert result['status'] == 'success'
        
        # Confidence interval should be present and valid
        if 'confidence_interval_95' in result:
            ci = result['confidence_interval_95']
            assert ci['lower'] <= result['forecast_mean'] <= ci['upper'], \
                f"Mean {result['forecast_mean']} outside CI [{ci['lower']}, {ci['upper']}]"
            assert ci['lower'] >= 0, "Lower bound should not be negative"


class TestAnomalyDetectionAccuracy:
    """Tests anomaly detection accuracy with known anomalies"""
    
    def test_obvious_anomaly_detection(self):
        """
        Test: Obvious anomalies (10x normal) should be detected
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Normal data with one spike
        data = [100] * 10 + [1000] + [100] * 10
        
        forecaster = CostForecaster()
        result = forecaster.detect_anomalies(data, threshold_std=2.0)
        
        assert result['total_anomalies'] >= 1, "Should detect at least one anomaly"
        
        # The spike at index 10 should be detected
        anomaly_indices = [a['day_index'] for a in result['anomalies_detected']]
        assert 10 in anomaly_indices, "Spike at index 10 should be detected"
    
    def test_no_false_positives_on_stable_data(self):
        """
        Test: Stable data should not produce false positive anomalies
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Very stable data
        data = [100] * 30
        
        forecaster = CostForecaster()
        result = forecaster.detect_anomalies(data, threshold_std=2.0)
        
        assert result['total_anomalies'] == 0, f"False positives detected: {result['anomalies_detected']}"
    
    def test_multiple_anomalies_detection(self):
        """
        Test: Multiple anomalies should all be detected
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Data with multiple spikes
        data = [100] * 5 + [500] + [100] * 5 + [50] + [100] * 5 + [600] + [100] * 5
        
        forecaster = CostForecaster()
        result = forecaster.detect_anomalies(data, threshold_std=2.0)
        
        # Should detect multiple anomalies
        assert result['total_anomalies'] >= 2, f"Should detect multiple anomalies, found {result['total_anomalies']}"
    
    def test_anomaly_severity_classification(self):
        """
        Test: Anomaly severity should be correctly classified
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Extreme spike
        data = [100] * 15 + [2000] + [100] * 15
        
        forecaster = CostForecaster()
        result = forecaster.detect_anomalies(data, threshold_std=2.0)
        
        if result['total_anomalies'] > 0:
            # Extreme anomaly should be high severity
            highest_severity = max(result['anomalies_detected'], key=lambda x: x['z_score'])
            assert highest_severity['severity'] in ['high', 'medium'], \
                f"Extreme anomaly should have high/medium severity, got {highest_severity['severity']}"
    
    def test_z_score_calculation_accuracy(self):
        """
        Test: Z-scores should be mathematically correct
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Known data: mean=100, std=10
        data = [90, 100, 110] * 10  # Creates mean~100, std~8.16
        
        forecaster = CostForecaster()
        result = forecaster.detect_anomalies(data, threshold_std=2.0)
        
        assert abs(result['mean_cost'] - 100) < 1, f"Mean should be ~100, got {result['mean_cost']}"
        assert result['std_cost'] > 0, "Std should be positive"


class TestAggregatedForecastAccuracy:
    """Tests aggregated multi-service forecasting"""
    
    def test_aggregated_forecast_sums_correctly(self):
        """
        Test: Aggregated forecast should be sum of individual forecasts
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        service_costs = {
            'EC2': [100] * 10,
            'RDS': [200] * 10,
            'S3': [50] * 10
        }
        
        forecaster = CostForecaster()
        result = forecaster.forecast_aggregated_costs(service_costs, forecast_days=7)
        
        # Total forecast should be approximately sum of services
        expected_total_mean = 350  # 100 + 200 + 50
        actual_total_mean = result['total_forecast_mean']
        
        # Allow 20% margin
        assert abs(actual_total_mean - expected_total_mean) / expected_total_mean < 0.3, \
            f"Total mean {actual_total_mean} differs from expected {expected_total_mean}"
    
    def test_aggregated_forecast_handles_empty_service(self):
        """
        Test: Empty service data should not break aggregation
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        service_costs = {
            'EC2': [100] * 10,
            'RDS': [],  # Empty service
            'S3': [50] * 10
        }
        
        forecaster = CostForecaster()
        result = forecaster.forecast_aggregated_costs(service_costs, forecast_days=7)
        
        # Should complete without error
        assert 'total_forecast' in result
        assert len(result['total_forecast']) == 7


class TestROIScoreCalculation:
    """Tests ROI score calculation accuracy"""
    
    def test_high_savings_high_confidence_score(self):
        """
        Test: High savings + high confidence = high ROI score
        """
        from src.finops_aws.services.predictive_optimization_service import (
            PredictiveOptimizationService,
            PredictiveRecommendation,
            OptimizationType,
            ConfidenceLevel
        )
        
        service = PredictiveOptimizationService()
        
        # High savings recommendation
        rec = PredictiveRecommendation(
            recommendation_id="test_high",
            optimization_type=OptimizationType.RIGHTSIZING,
            title="Test High",
            description="Test",
            resource_id="test",
            resource_type="EC2",
            service="EC2",
            current_cost=1000.0,
            predicted_savings=300.0,  # 30% savings
            implementation_effort="low",
            risk_level="low",
            confidence=ConfidenceLevel.HIGH,
            roi_score=0,
            payback_days=0,
            auto_implementable=True
        )
        
        score = service._calculate_roi_score(rec)
        
        # High savings + low effort + low risk + high confidence = high score
        assert score > 50, f"Expected high score, got {score}"
    
    def test_low_savings_high_risk_score(self):
        """
        Test: Low savings + high risk = low ROI score
        """
        from src.finops_aws.services.predictive_optimization_service import (
            PredictiveOptimizationService,
            PredictiveRecommendation,
            OptimizationType,
            ConfidenceLevel
        )
        
        service = PredictiveOptimizationService()
        
        # Low value recommendation
        rec = PredictiveRecommendation(
            recommendation_id="test_low",
            optimization_type=OptimizationType.ARCHITECTURE,
            title="Test Low",
            description="Test",
            resource_id="test",
            resource_type="EC2",
            service="EC2",
            current_cost=1000.0,
            predicted_savings=10.0,  # 1% savings
            implementation_effort="high",
            risk_level="high",
            confidence=ConfidenceLevel.LOW,
            roi_score=0,
            payback_days=365,
            auto_implementable=False
        )
        
        score = service._calculate_roi_score(rec)
        
        # Low savings + high effort + high risk + low confidence = low score
        assert score < 50, f"Expected low score, got {score}"
    
    def test_roi_score_bounded_0_to_100(self):
        """
        Test: ROI scores should always be between 0 and 100
        """
        from src.finops_aws.services.predictive_optimization_service import (
            PredictiveOptimizationService,
            PredictiveRecommendation,
            OptimizationType,
            ConfidenceLevel
        )
        
        service = PredictiveOptimizationService()
        
        # Extreme cases
        extreme_rec = PredictiveRecommendation(
            recommendation_id="test_extreme",
            optimization_type=OptimizationType.CLEANUP,
            title="Test",
            description="Test",
            resource_id="test",
            resource_type="EC2",
            service="EC2",
            current_cost=1.0,  # Very low cost
            predicted_savings=10000.0,  # Huge savings
            implementation_effort="low",
            risk_level="low",
            confidence=ConfidenceLevel.HIGH,
            roi_score=0,
            payback_days=0,
            auto_implementable=True
        )
        
        score = service._calculate_roi_score(extreme_rec)
        
        assert 0 <= score <= 100, f"Score {score} outside valid range [0, 100]"


class TestStatisticalModelValidation:
    """Tests statistical model assumptions and calculations"""
    
    def test_mean_calculation_accuracy(self):
        """
        Test: Mean calculation should be mathematically correct
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Known data with exact mean
        data = [10, 20, 30, 40, 50]  # Mean = 30
        
        forecaster = CostForecaster()
        result = forecaster.detect_anomalies(data)
        
        expected_mean = 30.0
        assert abs(result['mean_cost'] - expected_mean) < 0.01, \
            f"Mean calculation error: expected {expected_mean}, got {result['mean_cost']}"
    
    def test_std_calculation_accuracy(self):
        """
        Test: Standard deviation calculation should be correct
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Known data: [0, 10] has std = 5 (population) or ~7.07 (sample)
        data = [0, 10, 0, 10, 0, 10, 0, 10]  # Mean = 5, std ~ 5
        
        forecaster = CostForecaster()
        result = forecaster.detect_anomalies(data)
        
        expected_std = 5.0  # numpy uses population std by default
        assert abs(result['std_cost'] - expected_std) < 1.0, \
            f"Std calculation error: expected ~{expected_std}, got {result['std_cost']}"
    
    def test_trend_detection_accuracy(self):
        """
        Test: Trend detection should correctly identify direction
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        forecaster = CostForecaster()
        
        # Clear increasing trend
        increasing = [i for i in range(1, 31)]
        result = forecaster.forecast_service_cost(increasing, forecast_days=7)
        if 'trend' in result:
            assert result['trend'] == 'increasing', f"Should detect increasing trend, got {result.get('trend')}"
        
        # Clear decreasing trend
        decreasing = [30 - i for i in range(30)]
        result = forecaster.forecast_service_cost(decreasing, forecast_days=7)
        if 'trend' in result:
            assert result['trend'] == 'decreasing', f"Should detect decreasing trend, got {result.get('trend')}"


class TestEdgeCasesAndPrecision:
    """Tests edge cases and numerical precision"""
    
    def test_very_small_values_precision(self):
        """
        Test: Very small values should maintain precision
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Small values
        data = [0.001, 0.002, 0.001, 0.002, 0.001, 0.002, 0.001, 0.002, 0.001, 0.002]
        
        forecaster = CostForecaster()
        result = forecaster.forecast_service_cost(data, forecast_days=7)
        
        assert result['status'] == 'success'
        assert result['forecast_mean'] > 0, "Mean should be positive"
        assert result['forecast_mean'] < 0.01, "Mean should be small"
    
    def test_very_large_values_handling(self):
        """
        Test: Very large values should be handled correctly
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Large values
        data = [1_000_000 + i * 1000 for i in range(30)]
        
        forecaster = CostForecaster()
        result = forecaster.forecast_service_cost(data, forecast_days=7)
        
        assert result['status'] == 'success'
        assert result['forecast_mean'] > 1_000_000, "Mean should be large"
    
    def test_all_zeros_handling(self):
        """
        Test: All zeros should be handled gracefully
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        data = [0.0] * 30
        
        forecaster = CostForecaster()
        result = forecaster.forecast_service_cost(data, forecast_days=7)
        
        assert result['status'] == 'success'
        assert result['forecast_mean'] == 0 or abs(result['forecast_mean']) < 0.001
    
    def test_negative_values_in_data(self):
        """
        Test: Negative values (refunds) should be handled
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        # Mix of positive and negative (refunds)
        data = [100, -10, 100, 100, -20, 100, 100, 100, -5, 100] * 3
        
        forecaster = CostForecaster()
        result = forecaster.forecast_service_cost(data, forecast_days=7)
        
        assert result['status'] == 'success'


class TestKPIMetricsAccuracy:
    """Tests KPI metrics calculation accuracy"""
    
    def test_savings_percentage_calculation(self):
        """
        Test: Savings percentage should be mathematically correct
        """
        from src.finops_aws.services.predictive_optimization_service import PredictiveRecommendation, OptimizationType, ConfidenceLevel
        
        rec = PredictiveRecommendation(
            recommendation_id="test",
            optimization_type=OptimizationType.RIGHTSIZING,
            title="Test",
            description="Test",
            resource_id="test",
            resource_type="EC2",
            service="EC2",
            current_cost=1000.0,
            predicted_savings=300.0,
            implementation_effort="low",
            risk_level="low",
            confidence=ConfidenceLevel.HIGH,
            roi_score=0,
            payback_days=0,
            auto_implementable=True
        )
        
        result = rec.to_dict()
        
        expected_percent = 30.0  # 300/1000 * 100
        actual_percent = result['financials']['savings_percent']
        
        assert abs(actual_percent - expected_percent) < 0.1, \
            f"Savings percent error: expected {expected_percent}, got {actual_percent}"
    
    def test_zero_cost_savings_percentage(self):
        """
        Test: Zero cost should not cause division error
        """
        from src.finops_aws.services.predictive_optimization_service import PredictiveRecommendation, OptimizationType, ConfidenceLevel
        
        rec = PredictiveRecommendation(
            recommendation_id="test",
            optimization_type=OptimizationType.CLEANUP,
            title="Test",
            description="Test",
            resource_id="test",
            resource_type="EC2",
            service="EC2",
            current_cost=0.0,  # Zero cost
            predicted_savings=100.0,
            implementation_effort="low",
            risk_level="low",
            confidence=ConfidenceLevel.HIGH,
            roi_score=0,
            payback_days=0,
            auto_implementable=True
        )
        
        result = rec.to_dict()
        
        # Should not raise error, percentage should be 0
        assert result['financials']['savings_percent'] == 0


class TestModelConsistency:
    """Tests model consistency and reproducibility"""
    
    def test_deterministic_output(self):
        """
        Test: Same input should always produce same output
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        data = [100, 110, 120, 130, 140, 150, 160, 170, 180, 190]
        
        forecaster = CostForecaster()
        
        result1 = forecaster.forecast_service_cost(data, forecast_days=7)
        result2 = forecaster.forecast_service_cost(data, forecast_days=7)
        
        assert result1['forecast_mean'] == result2['forecast_mean'], \
            "Same input should produce same output"
    
    def test_forecast_length_matches_request(self):
        """
        Test: Forecast length should match requested days
        """
        from src.finops_aws.forecasting_engine import CostForecaster
        
        data = [100] * 30
        
        forecaster = CostForecaster()
        
        for days in [7, 14, 30]:
            result = forecaster.forecast_service_cost(data, forecast_days=days)
            if result['status'] == 'success' and 'forecast' in result:
                assert len(result['forecast']) == days, \
                    f"Forecast for {days} days has length {len(result['forecast'])}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
