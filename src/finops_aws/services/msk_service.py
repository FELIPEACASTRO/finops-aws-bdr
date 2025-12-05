"""
MSK FinOps Service - Análise de Custos do Amazon Managed Streaming for Apache Kafka

FASE 2.4 - Serviços Não-Serverless de Alto Custo
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de clusters MSK
- Análise de brokers e configurações
- Métricas de throughput e utilização
- Recomendações de otimização de custos
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class MSKBrokerNodeInfo:
    """Informações de um nó broker MSK"""
    broker_id: str
    instance_type: str
    availability_zone: str
    client_subnet: str
    endpoints: List[str] = field(default_factory=list)
    attached_eni_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'broker_id': self.broker_id,
            'instance_type': self.instance_type,
            'availability_zone': self.availability_zone,
            'client_subnet': self.client_subnet,
            'endpoints': self.endpoints,
            'attached_eni_id': self.attached_eni_id
        }


@dataclass
class MSKStorageInfo:
    """Informações de armazenamento MSK"""
    ebs_storage_info: Dict[str, Any] = field(default_factory=dict)
    provisioned_throughput: Optional[Dict[str, Any]] = None
    
    @property
    def volume_size_gb(self) -> int:
        return self.ebs_storage_info.get('VolumeSize', 0)
    
    @property
    def provisioned_throughput_enabled(self) -> bool:
        if self.provisioned_throughput:
            return self.provisioned_throughput.get('Enabled', False)
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'volume_size_gb': self.volume_size_gb,
            'provisioned_throughput_enabled': self.provisioned_throughput_enabled,
            'ebs_storage_info': self.ebs_storage_info
        }


@dataclass
class MSKCluster:
    """Representa um cluster MSK"""
    cluster_name: str
    cluster_arn: str
    cluster_state: str
    cluster_type: str
    kafka_version: str
    number_of_broker_nodes: int
    broker_node_group_info: Dict[str, Any] = field(default_factory=dict)
    current_broker_software_info: Dict[str, Any] = field(default_factory=dict)
    encryption_info: Dict[str, Any] = field(default_factory=dict)
    enhanced_monitoring: str = "DEFAULT"
    open_monitoring: Dict[str, Any] = field(default_factory=dict)
    logging_info: Dict[str, Any] = field(default_factory=dict)
    creation_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    zookeeper_connect_string: Optional[str] = None
    bootstrap_brokers: Optional[str] = None
    bootstrap_brokers_tls: Optional[str] = None
    storage_mode: str = "LOCAL"
    
    @property
    def instance_type(self) -> str:
        return self.broker_node_group_info.get('InstanceType', 'unknown')
    
    @property
    def storage_info(self) -> MSKStorageInfo:
        storage = self.broker_node_group_info.get('StorageInfo', {})
        return MSKStorageInfo(
            ebs_storage_info=storage.get('EbsStorageInfo', {}),
            provisioned_throughput=storage.get('EbsStorageInfo', {}).get('ProvisionedThroughput')
        )
    
    @property
    def is_provisioned(self) -> bool:
        return self.cluster_type == "PROVISIONED"
    
    @property
    def is_serverless(self) -> bool:
        return self.cluster_type == "SERVERLESS"
    
    @property
    def has_encryption_at_rest(self) -> bool:
        return bool(self.encryption_info.get('EncryptionAtRest'))
    
    @property
    def has_encryption_in_transit(self) -> bool:
        transit = self.encryption_info.get('EncryptionInTransit', {})
        return transit.get('ClientBroker', 'TLS') in ['TLS', 'TLS_PLAINTEXT']
    
    @property
    def has_open_monitoring(self) -> bool:
        prometheus = self.open_monitoring.get('Prometheus', {})
        return prometheus.get('JmxExporter', {}).get('EnabledInBroker', False) or \
               prometheus.get('NodeExporter', {}).get('EnabledInBroker', False)
    
    @property
    def has_cloudwatch_logs(self) -> bool:
        broker_logs = self.logging_info.get('BrokerLogs', {})
        return bool(broker_logs.get('CloudWatchLogs', {}).get('Enabled'))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cluster_name': self.cluster_name,
            'cluster_arn': self.cluster_arn,
            'cluster_state': self.cluster_state,
            'cluster_type': self.cluster_type,
            'kafka_version': self.kafka_version,
            'number_of_broker_nodes': self.number_of_broker_nodes,
            'instance_type': self.instance_type,
            'storage_info': self.storage_info.to_dict(),
            'enhanced_monitoring': self.enhanced_monitoring,
            'has_encryption_at_rest': self.has_encryption_at_rest,
            'has_encryption_in_transit': self.has_encryption_in_transit,
            'has_open_monitoring': self.has_open_monitoring,
            'has_cloudwatch_logs': self.has_cloudwatch_logs,
            'storage_mode': self.storage_mode,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None,
            'tags': self.tags
        }


@dataclass
class MSKConfiguration:
    """Representa uma configuração MSK"""
    arn: str
    name: str
    description: str
    kafka_versions: List[str] = field(default_factory=list)
    creation_time: Optional[datetime] = None
    state: str = "ACTIVE"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'arn': self.arn,
            'name': self.name,
            'description': self.description,
            'kafka_versions': self.kafka_versions,
            'state': self.state,
            'creation_time': self.creation_time.isoformat() if self.creation_time else None
        }


class MSKService(BaseAWSService):
    """
    Serviço FinOps para análise de custos do Amazon MSK
    
    Analisa clusters MSK provisionados e serverless,
    fornecendo recomendações de otimização de custos.
    
    MSK é um serviço de alto custo devido a:
    - Instâncias EC2 dedicadas para brokers
    - Armazenamento EBS persistente
    - Throughput provisionado
    - Custos de rede entre AZs
    """
    
    SERVICE_NAME = "Amazon MSK"
    SERVICE_FILTER = "Amazon Managed Streaming for Apache Kafka"
    
    def __init__(
        self,
        msk_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cost_client, cloudwatch_client)
        self._msk_client = msk_client
    
    @property
    def msk_client(self):
        if self._msk_client is None:
            import boto3
            self._msk_client = boto3.client('kafka')
        return self._msk_client
    
    def get_service_name(self) -> str:
        return self.SERVICE_NAME
    
    def health_check(self) -> bool:
        try:
            self.msk_client.list_clusters_v2(MaxResults=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    def get_clusters(self) -> List[MSKCluster]:
        """Lista todos os clusters MSK (provisionados e serverless)"""
        clusters = []
        
        try:
            paginator = self.msk_client.get_paginator('list_clusters_v2')
            
            for page in paginator.paginate():
                for cluster_info in page.get('ClusterInfoList', []):
                    cluster = self._parse_cluster_info(cluster_info)
                    if cluster:
                        clusters.append(cluster)
        except Exception as e:
            logger.error(f"Erro ao listar clusters MSK: {e}")
        
        return clusters
    
    def _parse_cluster_info(self, cluster_info: Dict[str, Any]) -> Optional[MSKCluster]:
        """Converte resposta da API em objeto MSKCluster"""
        try:
            cluster_type = cluster_info.get('ClusterType', 'PROVISIONED')
            
            if cluster_type == 'PROVISIONED':
                provisioned = cluster_info.get('Provisioned', {})
                return MSKCluster(
                    cluster_name=cluster_info.get('ClusterName', ''),
                    cluster_arn=cluster_info.get('ClusterArn', ''),
                    cluster_state=cluster_info.get('State', 'UNKNOWN'),
                    cluster_type=cluster_type,
                    kafka_version=provisioned.get('CurrentBrokerSoftwareInfo', {}).get('KafkaVersion', 'unknown'),
                    number_of_broker_nodes=provisioned.get('NumberOfBrokerNodes', 0),
                    broker_node_group_info=provisioned.get('BrokerNodeGroupInfo', {}),
                    current_broker_software_info=provisioned.get('CurrentBrokerSoftwareInfo', {}),
                    encryption_info=provisioned.get('EncryptionInfo', {}),
                    enhanced_monitoring=provisioned.get('EnhancedMonitoring', 'DEFAULT'),
                    open_monitoring=provisioned.get('OpenMonitoring', {}),
                    logging_info=provisioned.get('LoggingInfo', {}),
                    creation_time=cluster_info.get('CreationTime'),
                    tags=cluster_info.get('Tags', {}),
                    zookeeper_connect_string=provisioned.get('ZookeeperConnectString'),
                    storage_mode=provisioned.get('StorageMode', 'LOCAL')
                )
            else:
                return MSKCluster(
                    cluster_name=cluster_info.get('ClusterName', ''),
                    cluster_arn=cluster_info.get('ClusterArn', ''),
                    cluster_state=cluster_info.get('State', 'UNKNOWN'),
                    cluster_type=cluster_type,
                    kafka_version='serverless',
                    number_of_broker_nodes=0,
                    creation_time=cluster_info.get('CreationTime'),
                    tags=cluster_info.get('Tags', {})
                )
        except Exception as e:
            logger.error(f"Erro ao parsear cluster MSK: {e}")
            return None
    
    def get_cluster_details(self, cluster_arn: str) -> Optional[MSKCluster]:
        """Obtém detalhes completos de um cluster específico"""
        try:
            response = self.msk_client.describe_cluster_v2(ClusterArn=cluster_arn)
            cluster_info = response.get('ClusterInfo', {})
            return self._parse_cluster_info(cluster_info)
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do cluster {cluster_arn}: {e}")
            return None
    
    def get_configurations(self) -> List[MSKConfiguration]:
        """Lista todas as configurações MSK"""
        configurations = []
        
        try:
            paginator = self.msk_client.get_paginator('list_configurations')
            
            for page in paginator.paginate():
                for config in page.get('Configurations', []):
                    configurations.append(MSKConfiguration(
                        arn=config.get('Arn', ''),
                        name=config.get('Name', ''),
                        description=config.get('Description', ''),
                        kafka_versions=config.get('KafkaVersions', []),
                        creation_time=config.get('CreationTime'),
                        state=config.get('State', 'ACTIVE')
                    ))
        except Exception as e:
            logger.error(f"Erro ao listar configurações MSK: {e}")
        
        return configurations
    
    def get_cluster_bootstrap_brokers(self, cluster_arn: str) -> Dict[str, str]:
        """Obtém os endpoints dos brokers"""
        try:
            response = self.msk_client.get_bootstrap_brokers(ClusterArn=cluster_arn)
            return {
                'bootstrap_brokers': response.get('BootstrapBrokerString', ''),
                'bootstrap_brokers_tls': response.get('BootstrapBrokerStringTls', ''),
                'bootstrap_brokers_sasl_scram': response.get('BootstrapBrokerStringSaslScram', ''),
                'bootstrap_brokers_sasl_iam': response.get('BootstrapBrokerStringSaslIam', '')
            }
        except Exception as e:
            logger.error(f"Erro ao obter bootstrap brokers: {e}")
            return {}
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Obtém todos os recursos MSK"""
        clusters = self.get_clusters()
        return [c.to_dict() for c in clusters]
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas do MSK"""
        clusters = self.get_clusters()
        provisioned = [c for c in clusters if c.is_provisioned]
        
        total_brokers = sum(c.number_of_broker_nodes for c in provisioned)
        total_storage = sum(c.storage_info.volume_size_gb * c.number_of_broker_nodes for c in provisioned)
        
        return ServiceMetrics(
            service_name=self.SERVICE_NAME,
            resource_count=len(clusters),
            metrics={
                'provisioned_clusters': len(provisioned),
                'serverless_clusters': len(clusters) - len(provisioned),
                'total_broker_nodes': total_brokers,
                'total_storage_gb': total_storage,
                'clusters_active': len([c for c in clusters if c.cluster_state == 'ACTIVE']),
                'clusters_creating': len([c for c in clusters if c.cluster_state == 'CREATING']),
                'clusters_deleting': len([c for c in clusters if c.cluster_state == 'DELETING'])
            }
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para MSK"""
        recommendations = []
        clusters = self.get_clusters()
        
        for cluster in clusters:
            if not cluster.is_provisioned:
                continue
            
            if self._is_oversized_instance(cluster.instance_type):
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_arn,
                    resource_type="MSK::Cluster",
                    recommendation_type="RIGHT_SIZING",
                    title="Cluster MSK com instâncias superdimensionadas",
                    description=f"Cluster '{cluster.cluster_name}' usa instâncias {cluster.instance_type}. "
                               f"Considere usar instâncias menores se o throughput for baixo.",
                    action="Avaliar métricas de throughput e considerar migração para instâncias menores",
                    estimated_savings=self._estimate_instance_savings(cluster),
                    implementation_effort="MEDIUM",
                    priority="MEDIUM"
                ))
            
            if cluster.enhanced_monitoring == "DEFAULT":
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_arn,
                    resource_type="MSK::Cluster",
                    recommendation_type="OPTIMIZATION",
                    title="Monitoramento avançado não habilitado",
                    description=f"Cluster '{cluster.cluster_name}' não tem monitoramento avançado. "
                               f"Isso pode dificultar a identificação de oportunidades de otimização.",
                    action="Habilitar PER_BROKER ou PER_TOPIC_PER_BROKER monitoring",
                    estimated_savings=0,
                    implementation_effort="LOW",
                    priority="LOW"
                ))
            
            if not cluster.has_encryption_at_rest:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_arn,
                    resource_type="MSK::Cluster",
                    recommendation_type="SECURITY",
                    title="Encriptação em repouso não habilitada",
                    description=f"Cluster '{cluster.cluster_name}' não tem encriptação em repouso.",
                    action="Habilitar encriptação em repouso para conformidade",
                    estimated_savings=0,
                    implementation_effort="MEDIUM",
                    priority="HIGH"
                ))
            
            if cluster.number_of_broker_nodes > 6:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_arn,
                    resource_type="MSK::Cluster",
                    recommendation_type="RIGHT_SIZING",
                    title="Cluster com muitos brokers",
                    description=f"Cluster '{cluster.cluster_name}' tem {cluster.number_of_broker_nodes} brokers. "
                               f"Verifique se todos são necessários para o workload atual.",
                    action="Analisar utilização e considerar reduzir número de brokers",
                    estimated_savings=self._estimate_broker_savings(cluster),
                    implementation_effort="HIGH",
                    priority="MEDIUM"
                ))
            
            storage_gb = cluster.storage_info.volume_size_gb
            if storage_gb > 1000:
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_arn,
                    resource_type="MSK::Cluster",
                    recommendation_type="COST_OPTIMIZATION",
                    title="Alto volume de armazenamento",
                    description=f"Cluster '{cluster.cluster_name}' tem {storage_gb}GB por broker. "
                               f"Verifique se a retenção de dados está otimizada.",
                    action="Revisar políticas de retenção de tópicos Kafka",
                    estimated_savings=self._estimate_storage_savings(cluster, storage_gb),
                    implementation_effort="LOW",
                    priority="LOW"
                ))
            
            if cluster.number_of_broker_nodes <= 3 and cluster.instance_type.startswith('kafka.t3'):
                recommendations.append(ServiceRecommendation(
                    resource_id=cluster.cluster_arn,
                    resource_type="MSK::Cluster",
                    recommendation_type="MODERNIZATION",
                    title="Candidato a MSK Serverless",
                    description=f"Cluster '{cluster.cluster_name}' é pequeno e usa instâncias t3. "
                               f"MSK Serverless pode ser mais econômico para workloads variáveis.",
                    action="Avaliar migração para MSK Serverless",
                    estimated_savings=self._estimate_serverless_savings(cluster),
                    implementation_effort="HIGH",
                    priority="LOW"
                ))
        
        return recommendations
    
    def _is_oversized_instance(self, instance_type: str) -> bool:
        """Verifica se a instância é potencialmente superdimensionada"""
        large_instances = [
            'kafka.m5.12xlarge', 'kafka.m5.16xlarge', 'kafka.m5.24xlarge',
            'kafka.m5.4xlarge', 'kafka.m5.8xlarge',
            'kafka.m7g.12xlarge', 'kafka.m7g.16xlarge'
        ]
        return instance_type in large_instances
    
    def _estimate_instance_savings(self, cluster: MSKCluster) -> float:
        """Estima economia ao reduzir tipo de instância"""
        instance_costs = {
            'kafka.m5.24xlarge': 4.608,
            'kafka.m5.16xlarge': 3.072,
            'kafka.m5.12xlarge': 2.304,
            'kafka.m5.8xlarge': 1.536,
            'kafka.m5.4xlarge': 0.768,
            'kafka.m5.2xlarge': 0.384,
            'kafka.m5.large': 0.096
        }
        
        current_cost = instance_costs.get(cluster.instance_type, 0.5)
        smaller_cost = current_cost * 0.5
        
        hourly_savings = (current_cost - smaller_cost) * cluster.number_of_broker_nodes
        return hourly_savings * 24 * 30
    
    def _estimate_broker_savings(self, cluster: MSKCluster) -> float:
        """Estima economia ao reduzir número de brokers"""
        instance_costs = {
            'kafka.m5.large': 0.096,
            'kafka.m5.xlarge': 0.192,
            'kafka.m5.2xlarge': 0.384,
            'kafka.m5.4xlarge': 0.768,
            'kafka.t3.small': 0.024
        }
        
        hourly_cost = instance_costs.get(cluster.instance_type, 0.2)
        brokers_to_remove = max(1, cluster.number_of_broker_nodes - 3)
        
        return hourly_cost * brokers_to_remove * 24 * 30
    
    def _estimate_storage_savings(self, cluster: MSKCluster, storage_gb: int) -> float:
        """Estima economia ao reduzir armazenamento"""
        storage_cost_per_gb = 0.10
        potential_reduction = storage_gb * 0.3
        return potential_reduction * storage_cost_per_gb * cluster.number_of_broker_nodes
    
    def _estimate_serverless_savings(self, cluster: MSKCluster) -> float:
        """Estima economia ao migrar para serverless"""
        instance_costs = {
            'kafka.t3.small': 0.024,
            'kafka.t3.medium': 0.048,
            'kafka.m5.large': 0.096
        }
        
        current_hourly = instance_costs.get(cluster.instance_type, 0.05) * cluster.number_of_broker_nodes
        return current_hourly * 24 * 30 * 0.4
    
    def get_summary(self) -> Dict[str, Any]:
        """Retorna resumo completo do MSK"""
        resources = self.get_resources()
        costs = self.get_costs()
        recommendations = self.get_recommendations()
        
        return {
            'service': self.get_service_name(),
            'resources': resources,
            'costs': costs.to_dict(),
            'recommendations': [r.to_dict() for r in recommendations],
            'total_potential_savings': sum(r.estimated_savings for r in recommendations)
        }
