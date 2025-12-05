"""
Kinesis FinOps Service - Análise de Custos de Streaming

FASE 2 - Prioridade 2: Analytics
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de Data Streams, Firehose, Analytics
- Análise de shards e throughput
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class KinesisDataStream:
    """Representa um Kinesis Data Stream"""
    stream_name: str
    stream_arn: str
    stream_status: str
    stream_mode: str  # ON_DEMAND, PROVISIONED
    retention_period_hours: int
    shard_count: int = 0
    open_shard_count: int = 0
    consumer_count: int = 0
    encryption_type: str = "NONE"
    key_id: Optional[str] = None
    stream_creation_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'stream_name': self.stream_name,
            'stream_arn': self.stream_arn,
            'stream_status': self.stream_status,
            'stream_mode': self.stream_mode,
            'retention_period_hours': self.retention_period_hours,
            'shard_count': self.shard_count,
            'open_shard_count': self.open_shard_count,
            'consumer_count': self.consumer_count,
            'encryption_type': self.encryption_type,
            'stream_creation_timestamp': self.stream_creation_timestamp.isoformat() if self.stream_creation_timestamp else None
        }


@dataclass
class KinesisFirehoseStream:
    """Representa um Kinesis Firehose Delivery Stream"""
    delivery_stream_name: str
    delivery_stream_arn: str
    delivery_stream_status: str
    delivery_stream_type: str
    source: str
    destination_type: str  # S3, Redshift, Elasticsearch, Splunk, HTTP
    create_timestamp: Optional[datetime] = None
    last_update_timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'delivery_stream_name': self.delivery_stream_name,
            'delivery_stream_arn': self.delivery_stream_arn,
            'delivery_stream_status': self.delivery_stream_status,
            'delivery_stream_type': self.delivery_stream_type,
            'source': self.source,
            'destination_type': self.destination_type,
            'create_timestamp': self.create_timestamp.isoformat() if self.create_timestamp else None
        }


class KinesisService(BaseAWSService):
    """
    Serviço FinOps para análise de custos Kinesis
    
    Analisa Data Streams, Firehose e fornece
    recomendações de otimização de custos.
    """
    
    def __init__(
        self,
        kinesis_client=None,
        firehose_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._kinesis_client = kinesis_client
        self._firehose_client = firehose_client
    
    @property
    def kinesis_client(self):
        if self._kinesis_client is None:
            import boto3
            self._kinesis_client = boto3.client('kinesis')
        return self._kinesis_client
    
    @property
    def firehose_client(self):
        if self._firehose_client is None:
            import boto3
            self._firehose_client = boto3.client('firehose')
        return self._firehose_client
    
    def get_service_name(self) -> str:
        return "Amazon Kinesis"
    
    def health_check(self) -> bool:
        try:
            self.kinesis_client.list_streams(Limit=1)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    
    def get_data_streams(self) -> List[KinesisDataStream]:
        """Lista todos os Kinesis Data Streams"""
        streams = []
        
        paginator = self.kinesis_client.get_paginator('list_streams')
        
        for page in paginator.paginate():
            for stream_name in page.get('StreamNames', []):
                try:
                    detail = self.kinesis_client.describe_stream_summary(StreamName=stream_name)
                    summary = detail['StreamDescriptionSummary']
                    
                    stream = KinesisDataStream(
                        stream_name=stream_name,
                        stream_arn=summary['StreamARN'],
                        stream_status=summary['StreamStatus'],
                        stream_mode=summary.get('StreamModeDetails', {}).get('StreamMode', 'PROVISIONED'),
                        retention_period_hours=summary['RetentionPeriodHours'],
                        shard_count=summary.get('OpenShardCount', 0),
                        open_shard_count=summary.get('OpenShardCount', 0),
                        consumer_count=summary.get('ConsumerCount', 0),
                        encryption_type=summary.get('EncryptionType', 'NONE'),
                        key_id=summary.get('KeyId'),
                        stream_creation_timestamp=summary.get('StreamCreationTimestamp')
                    )
                    streams.append(stream)
                except Exception as e:  # noqa: E722
                    pass
        
        return streams
    
    
    def get_firehose_streams(self) -> List[KinesisFirehoseStream]:
        """Lista todos os Firehose Delivery Streams"""
        streams = []
        
        paginator = self.firehose_client.get_paginator('list_delivery_streams')
        
        for page in paginator.paginate():
            for stream_name in page.get('DeliveryStreamNames', []):
                try:
                    detail = self.firehose_client.describe_delivery_stream(DeliveryStreamName=stream_name)
                    desc = detail['DeliveryStreamDescription']
                    
                    destinations = desc.get('Destinations', [])
                    dest_type = 'Unknown'
                    if destinations:
                        dest = destinations[0]
                        if 'S3DestinationDescription' in dest:
                            dest_type = 'S3'
                        elif 'RedshiftDestinationDescription' in dest:
                            dest_type = 'Redshift'
                        elif 'ElasticsearchDestinationDescription' in dest:
                            dest_type = 'Elasticsearch'
                        elif 'SplunkDestinationDescription' in dest:
                            dest_type = 'Splunk'
                        elif 'HttpEndpointDestinationDescription' in dest:
                            dest_type = 'HTTP'
                    
                    source = 'DirectPut'
                    if desc.get('Source', {}).get('KinesisStreamSourceDescription'):
                        source = 'KinesisStream'
                    
                    stream = KinesisFirehoseStream(
                        delivery_stream_name=stream_name,
                        delivery_stream_arn=desc['DeliveryStreamARN'],
                        delivery_stream_status=desc['DeliveryStreamStatus'],
                        delivery_stream_type=desc['DeliveryStreamType'],
                        source=source,
                        destination_type=dest_type,
                        create_timestamp=desc.get('CreateTimestamp'),
                        last_update_timestamp=desc.get('LastUpdateTimestamp')
                    )
                    streams.append(stream)
                except Exception as e:  # noqa: E722
                    pass
        
        return streams
    
    
    def get_stream_metrics(self, stream_name: str, days: int = 7) -> Dict[str, Any]:
        """Obtém métricas de um Data Stream"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        metrics = {}
        
        incoming_records = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Kinesis',
            MetricName='IncomingRecords',
            Dimensions=[{'Name': 'StreamName', 'Value': stream_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if incoming_records.get('Datapoints'):
            metrics['incoming_records'] = int(sum(d['Sum'] for d in incoming_records['Datapoints']))
        
        incoming_bytes = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Kinesis',
            MetricName='IncomingBytes',
            Dimensions=[{'Name': 'StreamName', 'Value': stream_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if incoming_bytes.get('Datapoints'):
            metrics['incoming_bytes_gb'] = round(
                sum(d['Sum'] for d in incoming_bytes['Datapoints']) / (1024**3), 2
            )
        
        write_throttled = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/Kinesis',
            MetricName='WriteProvisionedThroughputExceeded',
            Dimensions=[{'Name': 'StreamName', 'Value': stream_name}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if write_throttled.get('Datapoints'):
            metrics['write_throttled'] = int(sum(d['Sum'] for d in write_throttled['Datapoints']))
        
        return metrics
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        for stream in self.get_data_streams():
            res = stream.to_dict()
            res['resource_type'] = 'data_stream'
            resources.append(res)
        
        for stream in self.get_firehose_streams():
            res = stream.to_dict()
            res['resource_type'] = 'firehose'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de Kinesis"""
        data_streams = self.get_data_streams()
        firehose_streams = self.get_firehose_streams()
        
        total_shards = sum(s.open_shard_count for s in data_streams)
        on_demand = len([s for s in data_streams if s.stream_mode == 'ON_DEMAND'])
        provisioned = len([s for s in data_streams if s.stream_mode == 'PROVISIONED'])
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(data_streams) + len(firehose_streams),
            metrics={
                'data_streams': len(data_streams),
                'firehose_streams': len(firehose_streams),
                'total_shards': total_shards,
                'on_demand_streams': on_demand,
                'provisioned_streams': provisioned,
                'streams_with_consumers': len([s for s in data_streams if s.consumer_count > 0])
            },
            period_days=7,
            collected_at=datetime.now(timezone.utc)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para Kinesis"""
        recommendations = []
        data_streams = self.get_data_streams()
        firehose_streams = self.get_firehose_streams()
        
        for stream in data_streams:
            if stream.encryption_type == 'NONE':
                recommendations.append(ServiceRecommendation(
                    resource_id=stream.stream_name,
                    resource_type='Kinesis Data Stream',
                    recommendation_type='SECURITY',
                    title='Stream sem criptografia',
                    description=f'Stream {stream.stream_name} não tem criptografia habilitada. '
                               f'Habilite criptografia SSE para conformidade.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    action='Habilitar Server-Side Encryption'
                ))
            
            if stream.stream_mode == 'PROVISIONED':
                try:
                    metrics = self.get_stream_metrics(stream.stream_name, days=7)
                    
                    if metrics.get('incoming_records', 0) == 0:
                        shard_cost = stream.open_shard_count * 0.015 * 24 * 30
                        recommendations.append(ServiceRecommendation(
                            resource_id=stream.stream_name,
                            resource_type='Kinesis Data Stream',
                            recommendation_type='UNUSED_RESOURCE',
                            title='Stream sem dados nos últimos 7 dias',
                            description=f'Stream {stream.stream_name} com {stream.open_shard_count} shards '
                                       f'não recebeu dados. Custo estimado: ${shard_cost:.2f}/mês.',
                            estimated_savings=shard_cost,
                            priority='HIGH',
                            action='Remover stream não utilizado'
                        ))
                    
                    if stream.open_shard_count > 2 and metrics.get('write_throttled', 0) == 0:
                        incoming_gb = metrics.get('incoming_bytes_gb', 0)
                        daily_gb = incoming_gb / 7 if incoming_gb else 0
                        
                        if daily_gb < stream.open_shard_count:
                            recommendations.append(ServiceRecommendation(
                                resource_id=stream.stream_name,
                                resource_type='Kinesis Data Stream',
                                recommendation_type='OVERSIZED',
                                title=f'Stream potencialmente superdimensionado',
                                description=f'Stream {stream.stream_name} tem {stream.open_shard_count} shards '
                                           f'mas processa apenas {daily_gb:.2f} GB/dia. Considere On-Demand.',
                                estimated_savings=stream.open_shard_count * 5,
                                priority='MEDIUM',
                                action='Migrar para On-Demand ou reduzir shards'
                            ))
                    
                except Exception as e:  # noqa: E722
                    pass
            
            if stream.retention_period_hours > 24:
                extra_hours = stream.retention_period_hours - 24
                extra_cost = (extra_hours / 24) * 0.02 * stream.open_shard_count * 30
                recommendations.append(ServiceRecommendation(
                    resource_id=stream.stream_name,
                    resource_type='Kinesis Data Stream',
                    recommendation_type='EXTENDED_RETENTION',
                    title=f'Retenção estendida: {stream.retention_period_hours}h',
                    description=f'Stream {stream.stream_name} tem retenção de {stream.retention_period_hours}h. '
                               f'Retenção além de 24h tem custo adicional (~${extra_cost:.2f}/mês).',
                    estimated_savings=extra_cost if stream.retention_period_hours > 168 else 0,
                    priority='LOW',
                    action='Avaliar necessidade de retenção estendida'
                ))
        
        for stream in firehose_streams:
            if stream.delivery_stream_status != 'ACTIVE':
                recommendations.append(ServiceRecommendation(
                    resource_id=stream.delivery_stream_name,
                    resource_type='Kinesis Firehose',
                    recommendation_type='UNHEALTHY',
                    title=f'Firehose em estado {stream.delivery_stream_status}',
                    description=f'Firehose {stream.delivery_stream_name} não está ativo. '
                               f'Investigue problemas de configuração.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    action='Investigar estado do delivery stream'
                ))
        
        return recommendations
