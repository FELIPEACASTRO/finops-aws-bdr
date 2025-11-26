"""
RDS Service - Exemplo de expansão para todos os serviços AWS
Coleta custos, uso, métricas e recomendações do Amazon RDS
"""
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from ..utils.logger import setup_logger, log_api_call
from ..utils.aws_helpers import handle_aws_error, get_aws_region

logger = setup_logger(__name__)


@dataclass
class RDSInstance:
    """Representa uma instância RDS"""
    db_instance_identifier: str
    db_instance_class: str
    engine: str
    engine_version: str
    db_instance_status: str
    availability_zone: str
    multi_az: bool
    storage_type: str
    allocated_storage: int
    storage_encrypted: bool
    backup_retention_period: int
    monthly_cost: float = 0.0
    cpu_utilization: float = 0.0
    database_connections: int = 0
    read_latency: float = 0.0
    write_latency: float = 0.0


class RDSService:
    """
    Serviço para análise completa do Amazon RDS
    Coleta custos, métricas de uso e recomendações de otimização
    
    Suporta injeção de dependências para Clean Architecture.
    
    Uso com Factory (recomendado):
        factory = ServiceFactory()
        rds_service = factory.get_rds_service()
        
    Uso direto (legado):
        rds_service = RDSService()
    """
    
    def __init__(
        self,
        rds_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        """
        Inicializa o RDSService
        
        Args:
            rds_client: Cliente RDS injetado (opcional)
            cloudwatch_client: Cliente CloudWatch injetado (opcional)
            cost_client: Cliente Cost Explorer injetado (opcional)
        """
        self.rds_client = rds_client or boto3.client('rds')
        self.cloudwatch_client = cloudwatch_client or boto3.client('cloudwatch')
        self.cost_client = cost_client or boto3.client('ce')
        self.region = get_aws_region()
    
    def get_service_name(self) -> str:
        """Retorna nome do serviço"""
        return "RDSService"
    
    def health_check(self) -> bool:
        """Verifica se serviço está operacional"""
        try:
            self.rds_client.describe_db_instances(MaxRecords=5)
            return True
        except Exception:
            return False
    
    def get_rds_instances(self) -> List[RDSInstance]:
        """
        Obtém lista de todas as instâncias RDS
        """
        try:
            response = self.rds_client.describe_db_instances()
            instances = []
            
            for db_instance in response['DBInstances']:
                instance = RDSInstance(
                    db_instance_identifier=db_instance['DBInstanceIdentifier'],
                    db_instance_class=db_instance['DBInstanceClass'],
                    engine=db_instance['Engine'],
                    engine_version=db_instance['EngineVersion'],
                    db_instance_status=db_instance['DBInstanceStatus'],
                    availability_zone=db_instance['AvailabilityZone'],
                    multi_az=db_instance['MultiAZ'],
                    storage_type=db_instance.get('StorageType', 'gp2'),
                    allocated_storage=db_instance['AllocatedStorage'],
                    storage_encrypted=db_instance.get('StorageEncrypted', False),
                    backup_retention_period=db_instance.get('BackupRetentionPeriod', 0)
                )
                instances.append(instance)
            
            logger.info(f"Found {len(instances)} RDS instances")
            return instances
            
        except Exception as e:
            handle_aws_error(e, "get_rds_instances")
            return []
    
    def get_rds_costs(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Obtém custos detalhados do RDS
        """
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            # Custo total do RDS
            response = self.cost_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': ['Amazon Relational Database Service']
                    }
                }
            )
            
            costs = {
                'total_cost': 0.0,
                'cost_by_engine': {},
                'cost_by_instance_type': {},
                'cost_by_usage_type': {},
                'daily_costs': [],
                'trends': 'STABLE'
            }
            
            for result in response['ResultsByTime']:
                daily_cost = 0.0
                date = result['TimePeriod']['Start']
                
                for group in result['Groups']:
                    service = group['Keys'][0]
                    usage_type = group['Keys'][1]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if service == 'Amazon Relational Database Service':
                        daily_cost += cost
                        costs['total_cost'] += cost
                        
                        # Categorizar por tipo de uso
                        if usage_type not in costs['cost_by_usage_type']:
                            costs['cost_by_usage_type'][usage_type] = 0.0
                        costs['cost_by_usage_type'][usage_type] += cost
                
                costs['daily_costs'].append({
                    'date': date,
                    'cost': daily_cost
                })
            
            # Calcular tendência
            if len(costs['daily_costs']) >= 7:
                recent_avg = sum(d['cost'] for d in costs['daily_costs'][-7:]) / 7
                older_avg = sum(d['cost'] for d in costs['daily_costs'][:7]) / 7
                
                if recent_avg > older_avg * 1.1:
                    costs['trends'] = 'INCREASING'
                elif recent_avg < older_avg * 0.9:
                    costs['trends'] = 'DECREASING'
            
            logger.info(f"RDS total cost for {period_days} days: ${costs['total_cost']:.2f}")
            return costs
            
        except Exception as e:
            handle_aws_error(e, "get_rds_costs")
            return {}
    
    def get_rds_metrics(self, instance_id: str, period_days: int = 7) -> Dict[str, Any]:
        """
        Obtém métricas detalhadas de uma instância RDS
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=period_days)
            
            metrics_to_collect = [
                'CPUUtilization',
                'DatabaseConnections',
                'ReadLatency',
                'WriteLatency',
                'ReadIOPS',
                'WriteIOPS',
                'NetworkReceiveThroughput',
                'NetworkTransmitThroughput',
                'FreeStorageSpace',
                'FreeableMemory'
            ]
            
            metrics_data = {}
            
            for metric_name in metrics_to_collect:
                try:
                    response = self.cloudwatch_client.get_metric_statistics(
                        Namespace='AWS/RDS',
                        MetricName=metric_name,
                        Dimensions=[
                            {
                                'Name': 'DBInstanceIdentifier',
                                'Value': instance_id
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=3600,  # 1 hora
                        Statistics=['Average', 'Maximum']
                    )
                    
                    if response['Datapoints']:
                        datapoints = sorted(response['Datapoints'], key=lambda x: x['Timestamp'])
                        metrics_data[metric_name] = {
                            'average': sum(dp['Average'] for dp in datapoints) / len(datapoints),
                            'maximum': max(dp['Maximum'] for dp in datapoints),
                            'latest': datapoints[-1]['Average'] if datapoints else 0,
                            'datapoints': len(datapoints)
                        }
                    else:
                        metrics_data[metric_name] = {
                            'average': 0,
                            'maximum': 0,
                            'latest': 0,
                            'datapoints': 0
                        }
                        
                except Exception as metric_error:
                    logger.warning(f"Failed to get metric {metric_name} for {instance_id}: {metric_error}")
                    metrics_data[metric_name] = {'average': 0, 'maximum': 0, 'latest': 0, 'datapoints': 0}
            
            return metrics_data
            
        except Exception as e:
            handle_aws_error(e, f"get_rds_metrics for {instance_id}")
            return {}
    
    def get_rds_recommendations(self, instances: List[RDSInstance]) -> List[Dict[str, Any]]:
        """
        Gera recomendações de otimização para instâncias RDS
        """
        recommendations = []
        
        for instance in instances:
            # Obter métricas para análise
            metrics = self.get_rds_metrics(instance.db_instance_identifier)
            
            if not metrics:
                continue
            
            cpu_avg = metrics.get('CPUUtilization', {}).get('average', 0)
            connections_avg = metrics.get('DatabaseConnections', {}).get('average', 0)
            read_latency = metrics.get('ReadLatency', {}).get('average', 0)
            write_latency = metrics.get('WriteLatency', {}).get('average', 0)
            
            # Recomendação de rightsizing
            if cpu_avg < 20:
                recommendations.append({
                    'resource_id': instance.db_instance_identifier,
                    'resource_type': 'RDS',
                    'finding': 'OVER_PROVISIONED',
                    'current_configuration': instance.db_instance_class,
                    'recommended_action': 'Downgrade instance type',
                    'estimated_monthly_savings': instance.monthly_cost * 0.3,
                    'reason': f'Low CPU utilization: {cpu_avg:.1f}%',
                    'priority': 'HIGH'
                })
            elif cpu_avg > 80:
                recommendations.append({
                    'resource_id': instance.db_instance_identifier,
                    'resource_type': 'RDS',
                    'finding': 'UNDER_PROVISIONED',
                    'current_configuration': instance.db_instance_class,
                    'recommended_action': 'Upgrade instance type',
                    'estimated_monthly_cost': instance.monthly_cost * 0.5,
                    'reason': f'High CPU utilization: {cpu_avg:.1f}%',
                    'priority': 'HIGH'
                })
            
            # Recomendação de Multi-AZ
            if not instance.multi_az and instance.db_instance_status == 'available':
                recommendations.append({
                    'resource_id': instance.db_instance_identifier,
                    'resource_type': 'RDS',
                    'finding': 'AVAILABILITY_IMPROVEMENT',
                    'current_configuration': 'Single-AZ',
                    'recommended_action': 'Enable Multi-AZ',
                    'estimated_monthly_cost': instance.monthly_cost * 1.0,
                    'reason': 'Improve availability and durability',
                    'priority': 'MEDIUM'
                })
            
            # Recomendação de backup
            if instance.backup_retention_period < 7:
                recommendations.append({
                    'resource_id': instance.db_instance_identifier,
                    'resource_type': 'RDS',
                    'finding': 'BACKUP_IMPROVEMENT',
                    'current_configuration': f'{instance.backup_retention_period} days retention',
                    'recommended_action': 'Increase backup retention to 7+ days',
                    'estimated_monthly_cost': instance.monthly_cost * 0.1,
                    'reason': 'Improve data protection',
                    'priority': 'MEDIUM'
                })
            
            # Recomendação de encryption
            if not instance.storage_encrypted:
                recommendations.append({
                    'resource_id': instance.db_instance_identifier,
                    'resource_type': 'RDS',
                    'finding': 'SECURITY_IMPROVEMENT',
                    'current_configuration': 'Unencrypted storage',
                    'recommended_action': 'Enable storage encryption',
                    'estimated_monthly_cost': 0,
                    'reason': 'Improve data security',
                    'priority': 'HIGH'
                })
        
        logger.info(f"Generated {len(recommendations)} RDS recommendations")
        return recommendations
    
    def get_all_rds_data(self) -> Dict[str, Any]:
        """
        Coleta todos os dados do RDS: custos, uso e recomendações
        """
        logger.info("Starting comprehensive RDS analysis")
        
        # Obter instâncias
        instances = self.get_rds_instances()
        
        # Obter custos
        costs = self.get_rds_costs()
        
        # Obter métricas para cada instância
        instances_with_metrics = []
        for instance in instances:
            metrics = self.get_rds_metrics(instance.db_instance_identifier)
            
            # Adicionar métricas à instância
            if metrics:
                instance.cpu_utilization = metrics.get('CPUUtilization', {}).get('average', 0)
                instance.database_connections = int(metrics.get('DatabaseConnections', {}).get('average', 0))
                instance.read_latency = metrics.get('ReadLatency', {}).get('average', 0)
                instance.write_latency = metrics.get('WriteLatency', {}).get('average', 0)
            
            instances_with_metrics.append(instance)
        
        # Gerar recomendações
        recommendations = self.get_rds_recommendations(instances_with_metrics)
        
        # Calcular economia total
        total_savings = sum(rec.get('estimated_monthly_savings', 0) for rec in recommendations)
        
        result = {
            'service': 'Amazon RDS',
            'summary': {
                'total_instances': len(instances),
                'running_instances': len([i for i in instances if i.db_instance_status == 'available']),
                'total_monthly_cost': costs.get('total_cost', 0),
                'potential_monthly_savings': total_savings,
                'recommendations_count': len(recommendations)
            },
            'costs': costs,
            'instances': [
                {
                    'db_instance_identifier': i.db_instance_identifier,
                    'db_instance_class': i.db_instance_class,
                    'engine': i.engine,
                    'status': i.db_instance_status,
                    'multi_az': i.multi_az,
                    'cpu_utilization': i.cpu_utilization,
                    'database_connections': i.database_connections,
                    'read_latency': i.read_latency,
                    'write_latency': i.write_latency
                }
                for i in instances_with_metrics
            ],
            'recommendations': recommendations,
            'finops_insights': {
                'cost_trend': costs.get('trends', 'STABLE'),
                'optimization_opportunities': len([r for r in recommendations if r['finding'] == 'OVER_PROVISIONED']),
                'security_improvements': len([r for r in recommendations if r['finding'] == 'SECURITY_IMPROVEMENT']),
                'availability_improvements': len([r for r in recommendations if r['finding'] == 'AVAILABILITY_IMPROVEMENT'])
            }
        }
        
        logger.info("RDS analysis completed successfully")
        return result


# Exemplo de uso
if __name__ == "__main__":
    rds_service = RDSService()
    rds_data = rds_service.get_all_rds_data()
    print(f"RDS Analysis: {rds_data['summary']}")