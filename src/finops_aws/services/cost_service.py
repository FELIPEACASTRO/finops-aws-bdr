"""
Serviço para coleta de dados de custo via AWS Cost Explorer
"""
import boto3
from datetime import datetime, timedelta
from typing import Dict, List
from botocore.exceptions import ClientError

from ..models.finops_models import CostData
from ..utils.logger import setup_logger, log_api_call, log_error
from ..utils.aws_helpers import retry_with_backoff, safe_get_nested

logger = setup_logger(__name__)

# Cliente global para reutilização
_cost_explorer_client = None


def get_cost_explorer_client():
    """Obtém cliente Cost Explorer (singleton)"""
    global _cost_explorer_client
    if _cost_explorer_client is None:
        _cost_explorer_client = boto3.client('ce', region_name='us-east-1')
    return _cost_explorer_client


class CostService:
    """Serviço para coleta e análise de custos AWS"""
    
    def __init__(self):
        self.client = get_cost_explorer_client()
        
    @retry_with_backoff(max_retries=3)
    def get_costs_by_service(self, days: int) -> Dict[str, float]:
        """
        Obtém custos por serviço AWS para um período específico
        
        Args:
            days: Número de dias para análise (7, 15, 30)
            
        Returns:
            Dicionário com custos por serviço
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        params = {
            'TimePeriod': {
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            'Granularity': 'DAILY',
            'Metrics': ['UnblendedCost'],
            'GroupBy': [
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        }
        
        logger.info(f"Fetching costs for last {days} days", 
                   extra={'extra_data': {'period': f"{start_date} to {end_date}"}})
        
        try:
            start_time = datetime.now()
            response = self.client.get_cost_and_usage(**params)
            duration = (datetime.now() - start_time).total_seconds()
            
            log_api_call(logger, 'Cost Explorer', 'get_cost_and_usage', params, duration)
            
            return self._process_cost_response(response)
            
        except ClientError as e:
            log_error(logger, e, {'operation': 'get_cost_and_usage', 'days': days})
            raise
    
    def _process_cost_response(self, response: Dict) -> Dict[str, float]:
        """
        Processa resposta do Cost Explorer
        
        Args:
            response: Resposta da API
            
        Returns:
            Dicionário com custos agregados por serviço
        """
        service_costs = {}
        
        for result_by_time in response.get('ResultsByTime', []):
            for group in result_by_time.get('Groups', []):
                service_name = safe_get_nested(group, ['Keys', 0], 'Unknown Service')
                amount = safe_get_nested(group, ['Metrics', 'UnblendedCost', 'Amount'], '0')
                
                try:
                    cost_amount = float(amount)
                    if service_name in service_costs:
                        service_costs[service_name] += cost_amount
                    else:
                        service_costs[service_name] = cost_amount
                except (ValueError, TypeError):
                    logger.warning(f"Invalid cost amount for {service_name}: {amount}")
                    continue
        
        # Remove serviços com custo zero
        service_costs = {k: v for k, v in service_costs.items() if v > 0.01}
        
        logger.info(f"Processed costs for {len(service_costs)} services", 
                   extra={'extra_data': {'total_services': len(service_costs)}})
        
        return service_costs
    
    def get_all_period_costs(self) -> Dict[str, Dict[str, float]]:
        """
        Obtém custos para todos os períodos (7, 15, 30 dias)
        
        Returns:
            Dicionário com custos por período
        """
        periods = [7, 15, 30]
        all_costs = {}
        
        for days in periods:
            try:
                period_key = f"last_{days}_days"
                all_costs[period_key] = self.get_costs_by_service(days)
                logger.info(f"Successfully fetched costs for {days} days")
            except Exception as e:
                log_error(logger, e, {'period': days})
                all_costs[f"last_{days}_days"] = {}
        
        return all_costs
    
    def get_top_services_by_cost(self, costs: Dict[str, float], limit: int = 10) -> List[Dict[str, any]]:
        """
        Obtém os serviços com maior custo
        
        Args:
            costs: Dicionário de custos por serviço
            limit: Número máximo de serviços a retornar
            
        Returns:
            Lista ordenada dos serviços com maior custo
        """
        sorted_services = sorted(costs.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'service': service,
                'cost': cost,
                'percentage': (cost / sum(costs.values())) * 100 if costs else 0
            }
            for service, cost in sorted_services[:limit]
        ]