"""
SNS/SQS FinOps Service - Análise de Custos de Messaging

FASE 2 - Prioridade 2: Application Integration
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de Topics SNS e Queues SQS
- Análise de mensagens e custos
- Recomendações de otimização
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class SNSTopic:
    """Representa um SNS Topic"""
    topic_arn: str
    topic_name: str
    display_name: str = ""
    subscription_count: int = 0
    subscriptions_confirmed: int = 0
    subscriptions_pending: int = 0
    policy: Optional[str] = None
    delivery_policy: Optional[str] = None
    kms_master_key_id: Optional[str] = None
    fifo_topic: bool = False
    content_based_deduplication: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'topic_arn': self.topic_arn,
            'topic_name': self.topic_name,
            'subscription_count': self.subscription_count,
            'fifo_topic': self.fifo_topic,
            'encrypted': self.kms_master_key_id is not None
        }


@dataclass
class SQSQueue:
    """Representa uma SQS Queue"""
    queue_url: str
    queue_name: str
    queue_arn: str
    approximate_number_of_messages: int = 0
    approximate_number_of_messages_not_visible: int = 0
    approximate_number_of_messages_delayed: int = 0
    visibility_timeout: int = 30
    message_retention_period: int = 345600
    delay_seconds: int = 0
    receive_message_wait_time_seconds: int = 0
    fifo_queue: bool = False
    content_based_deduplication: bool = False
    kms_master_key_id: Optional[str] = None
    dead_letter_target_arn: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'queue_url': self.queue_url,
            'queue_name': self.queue_name,
            'approximate_messages': self.approximate_number_of_messages,
            'visibility_timeout': self.visibility_timeout,
            'message_retention_days': self.message_retention_period // 86400,
            'fifo_queue': self.fifo_queue,
            'encrypted': self.kms_master_key_id is not None,
            'has_dlq': self.dead_letter_target_arn is not None
        }


class SNSSQSService(BaseAWSService):
    """
    Serviço FinOps para análise de custos SNS e SQS
    """
    
    def __init__(
        self,
        sns_client=None,
        sqs_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._sns_client = sns_client
        self._sqs_client = sqs_client
    
    @property
    def sns_client(self):
        if self._sns_client is None:
            import boto3
            self._sns_client = boto3.client('sns')
        return self._sns_client
    
    @property
    def sqs_client(self):
        if self._sqs_client is None:
            import boto3
            self._sqs_client = boto3.client('sqs')
        return self._sqs_client
    
    def get_service_name(self) -> str:
        return "Amazon SNS/SQS"
    
    def health_check(self) -> bool:
        try:
            self.sns_client.list_topics()
            return True
        except Exception as e:  # noqa: E722
            return False
    
    
    def get_sns_topics(self) -> List[SNSTopic]:
        """Lista SNS Topics"""
        topics = []
        
        paginator = self.sns_client.get_paginator('list_topics')
        
        for page in paginator.paginate():
            for topic in page.get('Topics', []):
                topic_arn = topic['TopicArn']
                topic_name = topic_arn.split(':')[-1]
                
                try:
                    attrs = self.sns_client.get_topic_attributes(TopicArn=topic_arn)
                    attributes = attrs.get('Attributes', {})
                    
                    sns_topic = SNSTopic(
                        topic_arn=topic_arn,
                        topic_name=topic_name,
                        display_name=attributes.get('DisplayName', ''),
                        subscription_count=int(attributes.get('SubscriptionsConfirmed', 0)) + 
                                          int(attributes.get('SubscriptionsPending', 0)),
                        subscriptions_confirmed=int(attributes.get('SubscriptionsConfirmed', 0)),
                        subscriptions_pending=int(attributes.get('SubscriptionsPending', 0)),
                        kms_master_key_id=attributes.get('KmsMasterKeyId'),
                        fifo_topic=attributes.get('FifoTopic', 'false') == 'true',
                        content_based_deduplication=attributes.get('ContentBasedDeduplication', 'false') == 'true'
                    )
                    topics.append(sns_topic)
                except Exception as e:  # noqa: E722
                    pass
        
        return topics
    
    
    def get_sqs_queues(self) -> List[SQSQueue]:
        """Lista SQS Queues"""
        queues = []
        
        response = self.sqs_client.list_queues()
        
        for queue_url in response.get('QueueUrls', []):
            try:
                attrs = self.sqs_client.get_queue_attributes(
                    QueueUrl=queue_url,
                    AttributeNames=['All']
                )
                attributes = attrs.get('Attributes', {})
                
                queue_name = queue_url.split('/')[-1]
                
                redrive_policy = attributes.get('RedrivePolicy', '{}')
                dlq_arn = None
                if redrive_policy and redrive_policy != '{}':
                    import json
                    try:
                        dlq_arn = json.loads(redrive_policy).get('deadLetterTargetArn')
                    except Exception as e:  # noqa: E722
                        pass
                
                sqs_queue = SQSQueue(
                    queue_url=queue_url,
                    queue_name=queue_name,
                    queue_arn=attributes.get('QueueArn', ''),
                    approximate_number_of_messages=int(attributes.get('ApproximateNumberOfMessages', 0)),
                    approximate_number_of_messages_not_visible=int(attributes.get('ApproximateNumberOfMessagesNotVisible', 0)),
                    approximate_number_of_messages_delayed=int(attributes.get('ApproximateNumberOfMessagesDelayed', 0)),
                    visibility_timeout=int(attributes.get('VisibilityTimeout', 30)),
                    message_retention_period=int(attributes.get('MessageRetentionPeriod', 345600)),
                    delay_seconds=int(attributes.get('DelaySeconds', 0)),
                    receive_message_wait_time_seconds=int(attributes.get('ReceiveMessageWaitTimeSeconds', 0)),
                    fifo_queue=attributes.get('FifoQueue', 'false') == 'true',
                    content_based_deduplication=attributes.get('ContentBasedDeduplication', 'false') == 'true',
                    kms_master_key_id=attributes.get('KmsMasterKeyId'),
                    dead_letter_target_arn=dlq_arn
                )
                queues.append(sqs_queue)
            except Exception as e:  # noqa: E722
                pass
        
        return queues
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        for topic in self.get_sns_topics():
            res = topic.to_dict()
            res['resource_type'] = 'sns_topic'
            resources.append(res)
        
        for queue in self.get_sqs_queues():
            res = queue.to_dict()
            res['resource_type'] = 'sqs_queue'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de SNS/SQS"""
        topics = self.get_sns_topics()
        queues = self.get_sqs_queues()
        
        total_subscriptions = sum(t.subscription_count for t in topics)
        total_messages = sum(q.approximate_number_of_messages for q in queues)
        fifo_queues = len([q for q in queues if q.fifo_queue])
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(topics) + len(queues),
            metrics={
                'sns_topics': len(topics),
                'total_subscriptions': total_subscriptions,
                'sqs_queues': len(queues),
                'fifo_queues': fifo_queues,
                'standard_queues': len(queues) - fifo_queues,
                'total_messages_in_queues': total_messages,
                'queues_with_dlq': len([q for q in queues if q.dead_letter_target_arn])
            },
            period_days=7,
            collected_at=datetime.now(timezone.utc)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para SNS/SQS"""
        recommendations = []
        topics = self.get_sns_topics()
        queues = self.get_sqs_queues()
        
        for topic in topics:
            if topic.subscription_count == 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=topic.topic_name,
                    resource_type='SNS Topic',
                    recommendation_type='NO_SUBSCRIBERS',
                    title='Topic sem subscribers',
                    description=f'Topic {topic.topic_name} não tem nenhum subscriber. '
                               f'Considere remover se não for mais necessário.',
                    estimated_savings=0.0,
                    priority='LOW',
                    action='Remover topic não utilizado'
                ))
        
        for queue in queues:
            if not queue.fifo_queue and queue.receive_message_wait_time_seconds == 0:
                recommendations.append(ServiceRecommendation(
                    resource_id=queue.queue_name,
                    resource_type='SQS Queue',
                    recommendation_type='SHORT_POLLING',
                    title='Queue usando short polling',
                    description=f'Queue {queue.queue_name} usa short polling. '
                               f'Long polling (WaitTimeSeconds > 0) reduz custos de requests vazios.',
                    estimated_savings=5.0,
                    priority='MEDIUM',
                    action='Configurar long polling'
                ))
            
            if not queue.dead_letter_target_arn and not queue.queue_name.endswith('-dlq'):
                recommendations.append(ServiceRecommendation(
                    resource_id=queue.queue_name,
                    resource_type='SQS Queue',
                    recommendation_type='NO_DLQ',
                    title='Queue sem Dead Letter Queue',
                    description=f'Queue {queue.queue_name} não tem DLQ configurada. '
                               f'Configure para capturar mensagens que falham.',
                    estimated_savings=0.0,
                    priority='MEDIUM',
                    action='Configurar Dead Letter Queue'
                ))
            
            if queue.approximate_number_of_messages > 10000:
                recommendations.append(ServiceRecommendation(
                    resource_id=queue.queue_name,
                    resource_type='SQS Queue',
                    recommendation_type='MESSAGE_BACKLOG',
                    title=f'Backlog alto: {queue.approximate_number_of_messages} mensagens',
                    description=f'Queue {queue.queue_name} tem {queue.approximate_number_of_messages} mensagens. '
                               f'Verifique se consumers estão funcionando corretamente.',
                    estimated_savings=0.0,
                    priority='HIGH',
                    action='Investigar processamento de mensagens'
                ))
        
        return recommendations
