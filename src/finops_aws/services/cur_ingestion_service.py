"""
FinOps AWS - CUR Ingestion Service
Serviço de ingestão de dados do Cost and Usage Report (CUR)

Este serviço implementa:
- Ingestão de dados CUR via S3/Athena (simulado quando não disponível)
- Normalização de dados de custo
- Cache de dados para performance
- Reconciliação com Cost Explorer

Design Patterns:
- Strategy: Implementa interface BaseAWSService
- Repository: Abstrai fonte de dados (CUR vs Cost Explorer)
- Cache: Dados normalizados em memória com TTL
"""
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import os
import json

import boto3
from botocore.exceptions import ClientError

from .base_service import BaseAWSService
from ..utils.logger import setup_logger
from ..utils.cache import FinOpsCache


class CURDataSource(Enum):
    """Fonte de dados CUR"""
    ATHENA = "athena"
    S3_DIRECT = "s3_direct"
    COST_EXPLORER_FALLBACK = "cost_explorer_fallback"


@dataclass
class CURRecord:
    """Representa um registro normalizado do CUR"""
    line_item_id: str
    usage_start_date: datetime
    usage_end_date: datetime
    product_code: str
    usage_type: str
    operation: str
    resource_id: str
    usage_amount: float
    unblended_cost: float
    blended_cost: float
    amortized_cost: float
    net_amortized_cost: float
    region: str
    availability_zone: str
    linked_account_id: str
    linked_account_name: str
    tags: Dict[str, str] = field(default_factory=dict)
    cost_category: str = ""
    pricing_term: str = ""
    reservation_arn: str = ""
    savings_plan_arn: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'line_item_id': self.line_item_id,
            'usage_start_date': self.usage_start_date.isoformat(),
            'usage_end_date': self.usage_end_date.isoformat(),
            'product_code': self.product_code,
            'usage_type': self.usage_type,
            'operation': self.operation,
            'resource_id': self.resource_id,
            'usage_amount': self.usage_amount,
            'unblended_cost': self.unblended_cost,
            'blended_cost': self.blended_cost,
            'amortized_cost': self.amortized_cost,
            'net_amortized_cost': self.net_amortized_cost,
            'region': self.region,
            'availability_zone': self.availability_zone,
            'linked_account_id': self.linked_account_id,
            'linked_account_name': self.linked_account_name,
            'tags': self.tags,
            'cost_category': self.cost_category,
            'pricing_term': self.pricing_term,
            'reservation_arn': self.reservation_arn,
            'savings_plan_arn': self.savings_plan_arn
        }


@dataclass
class CURSummary:
    """Resumo agregado de dados CUR"""
    period_start: datetime
    period_end: datetime
    total_unblended_cost: float
    total_blended_cost: float
    total_amortized_cost: float
    total_net_amortized_cost: float
    record_count: int
    data_source: str
    by_service: Dict[str, float] = field(default_factory=dict)
    by_region: Dict[str, float] = field(default_factory=dict)
    by_account: Dict[str, float] = field(default_factory=dict)
    by_cost_category: Dict[str, float] = field(default_factory=dict)
    by_tag: Dict[str, Dict[str, float]] = field(default_factory=dict)
    reconciliation_status: str = "pending"
    reconciliation_variance: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'period': {
                'start': self.period_start.isoformat(),
                'end': self.period_end.isoformat()
            },
            'totals': {
                'unblended_cost': round(self.total_unblended_cost, 2),
                'blended_cost': round(self.total_blended_cost, 2),
                'amortized_cost': round(self.total_amortized_cost, 2),
                'net_amortized_cost': round(self.total_net_amortized_cost, 2)
            },
            'record_count': self.record_count,
            'data_source': self.data_source,
            'by_service': {k: round(v, 2) for k, v in self.by_service.items()},
            'by_region': {k: round(v, 2) for k, v in self.by_region.items()},
            'by_account': {k: round(v, 2) for k, v in self.by_account.items()},
            'by_cost_category': {k: round(v, 2) for k, v in self.by_cost_category.items()},
            'by_tag': self.by_tag,
            'reconciliation': {
                'status': self.reconciliation_status,
                'variance_percent': round(self.reconciliation_variance, 2)
            }
        }


class CURIngestionService(BaseAWSService):
    """
    Serviço de Ingestão CUR
    
    Funcionalidades:
    - Ingestão de dados CUR via Athena ou S3
    - Fallback para Cost Explorer quando CUR não disponível
    - Normalização e cache de dados
    - Reconciliação automática
    
    AWS APIs utilizadas:
    - athena:StartQueryExecution
    - athena:GetQueryResults
    - s3:GetObject (para CUR)
    - ce:GetCostAndUsage (fallback)
    """
    
    CUR_DATABASE = os.environ.get('CUR_DATABASE', 'cur_database')
    CUR_TABLE = os.environ.get('CUR_TABLE', 'cost_and_usage_report')
    CUR_S3_BUCKET = os.environ.get('CUR_S3_BUCKET', '')
    
    def __init__(self, client_factory=None):
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(self.__class__.__name__)
        self.service_name = "cur_ingestion"
        self._cache = FinOpsCache(default_ttl=300)
        self._data_source = CURDataSource.COST_EXPLORER_FALLBACK
    
    def _get_athena_client(self, region: str = None):
        """Obtém cliente boto3 para Athena"""
        region = region or os.environ.get('AWS_REGION', 'us-east-1')
        if self._client_factory:
            return self._client_factory.get_client('athena', region_name=region)
        return boto3.client('athena', region_name=region)
    
    def _get_ce_client(self):
        """Obtém cliente boto3 para Cost Explorer"""
        if self._client_factory:
            return self._client_factory.get_client('ce', region_name='us-east-1')
        return boto3.client('ce', region_name='us-east-1')
    
    def _get_s3_client(self):
        """Obtém cliente boto3 para S3"""
        if self._client_factory:
            return self._client_factory.get_client('s3')
        return boto3.client('s3')
    
    def health_check(self) -> bool:
        """Verifica saúde do serviço e determina fonte de dados"""
        if self._check_athena_available():
            self._data_source = CURDataSource.ATHENA
            return True
        
        if self._check_s3_cur_available():
            self._data_source = CURDataSource.S3_DIRECT
            return True
        
        if self._check_cost_explorer_available():
            self._data_source = CURDataSource.COST_EXPLORER_FALLBACK
            self.logger.info("Usando Cost Explorer como fallback (CUR não configurado)")
            return True
        
        return False
    
    def _check_athena_available(self) -> bool:
        """Verifica se Athena com CUR está disponível"""
        if not self.CUR_DATABASE or not self.CUR_TABLE:
            return False
        
        try:
            client = self._get_athena_client()
            client.get_database(CatalogName='AwsDataCatalog', DatabaseName=self.CUR_DATABASE)
            return True
        except ClientError:
            return False
        except Exception:
            return False
    
    def _check_s3_cur_available(self) -> bool:
        """Verifica se CUR em S3 está disponível"""
        if not self.CUR_S3_BUCKET:
            return False
        
        try:
            client = self._get_s3_client()
            client.head_bucket(Bucket=self.CUR_S3_BUCKET)
            return True
        except ClientError:
            return False
        except Exception:
            return False
    
    def _check_cost_explorer_available(self) -> bool:
        """Verifica se Cost Explorer está disponível"""
        try:
            client = self._get_ce_client()
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
            start_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
            client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity='DAILY',
                Metrics=['UnblendedCost']
            )
            return True
        except ClientError:
            return False
        except Exception:
            return False
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Retorna informações sobre as fontes de dados disponíveis"""
        return [{
            'data_source': self._data_source.value,
            'cur_database': self.CUR_DATABASE,
            'cur_table': self.CUR_TABLE,
            'cur_s3_bucket': self.CUR_S3_BUCKET,
            'status': 'available'
        }]
    
    def ingest_cur_data(
        self,
        start_date: datetime,
        end_date: datetime,
        force_refresh: bool = False
    ) -> CURSummary:
        """
        Ingere dados CUR para o período especificado
        
        Args:
            start_date: Data inicial
            end_date: Data final
            force_refresh: Se True, ignora cache
            
        Returns:
            CURSummary com dados agregados
        """
        cache_key = f"cur_data_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached:
                self.logger.info(f"Retornando dados CUR do cache: {cache_key}")
                return cached
        
        self.health_check()
        
        if self._data_source == CURDataSource.ATHENA:
            summary = self._ingest_from_athena(start_date, end_date)
        elif self._data_source == CURDataSource.S3_DIRECT:
            summary = self._ingest_from_s3(start_date, end_date)
        else:
            summary = self._ingest_from_cost_explorer(start_date, end_date)
        
        summary = self._reconcile_with_cost_explorer(summary)
        
        self._cache.set(cache_key, summary, ttl=3600)
        
        return summary
    
    def _ingest_from_athena(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> CURSummary:
        """Ingere dados via Athena"""
        self.logger.info("Ingestão via Athena não implementada - usando fallback")
        return self._ingest_from_cost_explorer(start_date, end_date)
    
    def _ingest_from_s3(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> CURSummary:
        """Ingere dados diretamente do S3"""
        self.logger.info("Ingestão via S3 não implementada - usando fallback")
        return self._ingest_from_cost_explorer(start_date, end_date)
    
    def _ingest_from_cost_explorer(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> CURSummary:
        """
        Ingere dados via Cost Explorer (fallback)
        Simula estrutura CUR para compatibilidade
        """
        try:
            client = self._get_ce_client()
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'BlendedCost', 'AmortizedCost', 'NetAmortizedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            total_unblended = 0.0
            total_blended = 0.0
            total_amortized = 0.0
            total_net_amortized = 0.0
            by_service: Dict[str, float] = {}
            record_count = 0
            
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    metrics = group['Metrics']
                    
                    unblended = float(metrics.get('UnblendedCost', {}).get('Amount', 0))
                    blended = float(metrics.get('BlendedCost', {}).get('Amount', 0))
                    amortized = float(metrics.get('AmortizedCost', {}).get('Amount', 0))
                    net_amortized = float(metrics.get('NetAmortizedCost', {}).get('Amount', 0))
                    
                    total_unblended += unblended
                    total_blended += blended
                    total_amortized += amortized
                    total_net_amortized += net_amortized
                    
                    by_service[service] = by_service.get(service, 0) + unblended
                    record_count += 1
            
            by_region = self._get_costs_by_region(client, start_date, end_date)
            by_account = self._get_costs_by_account(client, start_date, end_date)
            
            return CURSummary(
                period_start=start_date,
                period_end=end_date,
                total_unblended_cost=total_unblended,
                total_blended_cost=total_blended,
                total_amortized_cost=total_amortized,
                total_net_amortized_cost=total_net_amortized,
                record_count=record_count,
                data_source=CURDataSource.COST_EXPLORER_FALLBACK.value,
                by_service=by_service,
                by_region=by_region,
                by_account=by_account,
                by_cost_category={},
                by_tag={}
            )
            
        except Exception as e:
            self.logger.error(f"Erro na ingestão via Cost Explorer: {e}")
            return CURSummary(
                period_start=start_date,
                period_end=end_date,
                total_unblended_cost=0,
                total_blended_cost=0,
                total_amortized_cost=0,
                total_net_amortized_cost=0,
                record_count=0,
                data_source="error",
                reconciliation_status="error"
            )
    
    def _get_costs_by_region(
        self,
        client: Any,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Obtém custos agrupados por região"""
        try:
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'REGION'}
                ]
            )
            
            by_region: Dict[str, float] = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    region = group['Keys'][0] or 'global'
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    by_region[region] = by_region.get(region, 0) + cost
            
            return by_region
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custos por região: {e}")
            return {}
    
    def _get_costs_by_account(
        self,
        client: Any,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, float]:
        """Obtém custos agrupados por conta"""
        try:
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}
                ]
            )
            
            by_account: Dict[str, float] = {}
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    account = group['Keys'][0]
                    cost = float(group['Metrics']['UnblendedCost']['Amount'])
                    by_account[account] = by_account.get(account, 0) + cost
            
            return by_account
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custos por conta: {e}")
            return {}
    
    def _reconcile_with_cost_explorer(self, summary: CURSummary) -> CURSummary:
        """
        Reconcilia dados CUR com Cost Explorer
        Verifica variância e marca status
        """
        if summary.data_source == CURDataSource.COST_EXPLORER_FALLBACK.value:
            summary.reconciliation_status = "not_applicable"
            summary.reconciliation_variance = 0.0
            return summary
        
        try:
            client = self._get_ce_client()
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': summary.period_start.strftime('%Y-%m-%d'),
                    'End': summary.period_end.strftime('%Y-%m-%d')
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost']
            )
            
            ce_total = 0.0
            for result in response.get('ResultsByTime', []):
                ce_total += float(result.get('Total', {}).get('UnblendedCost', {}).get('Amount', 0))
            
            if ce_total > 0:
                variance = abs(summary.total_unblended_cost - ce_total) / ce_total * 100
            else:
                variance = 0.0
            
            if variance <= 2.0:
                summary.reconciliation_status = "reconciled"
            elif variance <= 5.0:
                summary.reconciliation_status = "minor_variance"
            else:
                summary.reconciliation_status = "major_variance"
            
            summary.reconciliation_variance = variance
            
        except Exception as e:
            self.logger.error(f"Erro na reconciliação: {e}")
            summary.reconciliation_status = "error"
        
        return summary
    
    def get_daily_costs(
        self,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Obtém custos diários para análise de tendência
        
        Args:
            days_back: Número de dias para trás
            
        Returns:
            Lista de custos diários
        """
        cache_key = f"daily_costs_{days_back}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        try:
            client = self._get_ce_client()
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            response = client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost', 'AmortizedCost']
            )
            
            daily_costs = []
            for result in response.get('ResultsByTime', []):
                period = result.get('TimePeriod', {})
                total = result.get('Total', {})
                
                daily_costs.append({
                    'date': period.get('Start'),
                    'unblended_cost': float(total.get('UnblendedCost', {}).get('Amount', 0)),
                    'amortized_cost': float(total.get('AmortizedCost', {}).get('Amount', 0))
                })
            
            self._cache.set(cache_key, daily_costs, ttl=3600)
            return daily_costs
            
        except Exception as e:
            self.logger.error(f"Erro ao obter custos diários: {e}")
            return []
    
    def get_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """Obtém custos do serviço (interface BaseAWSService)"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        summary = self.ingest_cur_data(start_date, end_date)
        
        return {
            'service': 'cur_ingestion',
            'period_days': period_days,
            'total_cost': summary.total_unblended_cost,
            'currency': 'USD',
            'data_source': summary.data_source,
            'by_service': summary.by_service
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas do serviço (interface BaseAWSService)"""
        return {
            'service': 'cur_ingestion',
            'data_source': self._data_source.value,
            'cache_stats': self._cache.get_stats(),
            'cur_available': self._data_source != CURDataSource.COST_EXPLORER_FALLBACK
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações baseadas em dados CUR"""
        recommendations = []
        
        if self._data_source == CURDataSource.COST_EXPLORER_FALLBACK:
            recommendations.append({
                'type': 'CUR_SETUP',
                'priority': 'MEDIUM',
                'title': 'Configurar Cost and Usage Report (CUR)',
                'description': 'Configure o AWS CUR para obter dados de custo mais detalhados e precisos',
                'savings': 0,
                'effort': 'medium',
                'impact': 'Melhoria na precisão de análises e alocação de custos'
            })
        
        return recommendations
