"""
Analytics Analyzer - Análise de serviços de analytics AWS

Serviços cobertos:
- EMR
- Kinesis
- Glue
- Athena
- Redshift
- OpenSearch
- QuickSight

Design Pattern: Strategy
"""
from typing import Dict, List, Any
from datetime import datetime
import logging

from .base_analyzer import (
    BaseAnalyzer,
    Recommendation,
    Priority,
    Impact
)

logger = logging.getLogger(__name__)


class AnalyticsAnalyzer(BaseAnalyzer):
    """Analyzer para serviços de analytics AWS."""
    
    name = "AnalyticsAnalyzer"
    
    def _get_client(self, region: str) -> Any:
        """Retorna clientes boto3 para analytics."""
        import boto3
        return {
            'emr': boto3.client('emr', region_name=region),
            'kinesis': boto3.client('kinesis', region_name=region),
            'glue': boto3.client('glue', region_name=region),
            'redshift': boto3.client('redshift', region_name=region),
        }
    
    def _collect_resources(self, clients: Dict[str, Any]) -> Dict[str, Any]:
        """Coleta recursos de analytics."""
        resources = {}
        
        emr = clients.get('emr')
        if emr:
            try:
                resources['emr_clusters'] = emr.list_clusters(
                    ClusterStates=['RUNNING', 'WAITING']
                )
            except Exception as e:
                logger.warning(f"Erro coletando EMR: {e}")
        
        kinesis = clients.get('kinesis')
        if kinesis:
            try:
                resources['kinesis_streams'] = kinesis.list_streams()
            except Exception as e:
                logger.warning(f"Erro coletando Kinesis: {e}")
        
        glue = clients.get('glue')
        if glue:
            try:
                resources['glue_jobs'] = glue.list_jobs()
                resources['glue_crawlers'] = glue.list_crawlers()
            except Exception as e:
                logger.warning(f"Erro coletando Glue: {e}")
        
        redshift = clients.get('redshift')
        if redshift:
            try:
                resources['redshift_clusters'] = redshift.describe_clusters()
            except Exception as e:
                logger.warning(f"Erro coletando Redshift: {e}")
        
        return resources
    
    def _analyze_resources(
        self, 
        resources: Dict[str, Any], 
        region: str
    ) -> tuple[List[Recommendation], Dict[str, int]]:
        """Analisa recursos e gera recomendações."""
        recommendations = []
        metrics = {}
        
        recommendations.extend(self._analyze_emr(resources, metrics))
        recommendations.extend(self._analyze_kinesis(resources, metrics))
        recommendations.extend(self._analyze_glue(resources, metrics))
        recommendations.extend(self._analyze_redshift(resources, metrics))
        
        return recommendations, metrics
    
    def _analyze_emr(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa clusters EMR."""
        recommendations = []
        clusters_data = resources.get('emr_clusters', {})
        
        clusters = clusters_data.get('Clusters', [])
        metrics['emr_clusters'] = len(clusters)
        
        for cluster in clusters:
            cluster_id = cluster.get('Id', '')
            name = cluster.get('Name', '')
            
            recommendations.append(self._create_recommendation(
                rec_type='EMR_RUNNING',
                resource_id=cluster_id,
                description=f'EMR cluster {name} ativo - verificar se necessário',
                service='EMR Analysis',
                priority=Priority.HIGH
            ))
        
        return recommendations
    
    def _analyze_kinesis(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa streams Kinesis."""
        recommendations = []
        streams_data = resources.get('kinesis_streams', {})
        
        streams = streams_data.get('StreamNames', [])
        metrics['kinesis_streams'] = len(streams)
        
        return recommendations
    
    def _analyze_glue(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa jobs Glue."""
        recommendations = []
        
        jobs_data = resources.get('glue_jobs', {})
        metrics['glue_jobs'] = len(jobs_data.get('JobNames', []))
        
        crawlers_data = resources.get('glue_crawlers', {})
        metrics['glue_crawlers'] = len(crawlers_data.get('CrawlerNames', []))
        
        return recommendations
    
    def _analyze_redshift(
        self, 
        resources: Dict[str, Any], 
        metrics: Dict[str, int]
    ) -> List[Recommendation]:
        """Analisa clusters Redshift."""
        recommendations = []
        clusters_data = resources.get('redshift_clusters', {})
        
        clusters = clusters_data.get('Clusters', [])
        metrics['redshift_clusters'] = len(clusters)
        
        for cluster in clusters:
            cluster_id = cluster.get('ClusterIdentifier', '')
            node_type = cluster.get('NodeType', '')
            
            recommendations.append(self._create_recommendation(
                rec_type='REDSHIFT_RUNNING',
                resource_id=cluster_id,
                description=f'Redshift cluster {cluster_id} ({node_type}) ativo - revisar uso',
                service='Redshift Analysis',
                priority=Priority.MEDIUM
            ))
            
            if 'ds2' in node_type or 'dc1' in node_type:
                recommendations.append(self._create_recommendation(
                    rec_type='REDSHIFT_OLD_GENERATION',
                    resource_id=cluster_id,
                    description=f'Redshift {cluster_id} usa tipo antigo ({node_type}) - migrar para RA3',
                    service='Redshift Optimization',
                    priority=Priority.MEDIUM,
                    savings=100.0
                ))
        
        return recommendations
    
    def _get_services_list(self) -> List[str]:
        """Retorna serviços analisados."""
        return ['EMR', 'Kinesis', 'Glue', 'Redshift']
