"""
AWS SQS FinOps Service.

Análise de custos e métricas do Amazon SQS para filas de mensagens.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class SQSQueue:
    """Representa uma fila SQS."""
    
    queue_url: str = ""
    queue_arn: str = ""
    queue_name: str = ""
    created_timestamp: Optional[datetime] = None
    last_modified_timestamp: Optional[datetime] = None
    visibility_timeout: int = 30
    maximum_message_size: int = 262144
    message_retention_period: int = 345600
    delay_seconds: int = 0
    receive_message_wait_time_seconds: int = 0
    approximate_number_of_messages: int = 0
    approximate_number_of_messages_not_visible: int = 0
    approximate_number_of_messages_delayed: int = 0
    policy: str = ""
    redrive_policy: Dict[str, Any] = field(default_factory=dict)
    fifo_queue: bool = False
    content_based_deduplication: bool = False
    kms_master_key_id: str = ""
    kms_data_key_reuse_period_seconds: int = 300
    deduplication_scope: str = ""
    fifo_throughput_limit: str = ""
    sqs_managed_sse_enabled: bool = False
    tags: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_fifo(self) -> bool:
        """Verifica se é fila FIFO."""
        return bool(self.fifo_queue)
    
    @property
    def is_standard(self) -> bool:
        """Verifica se é fila Standard."""
        return not self.fifo_queue
    
    @property
    def has_dlq(self) -> bool:
        """Verifica se tem Dead Letter Queue."""
        return bool(self.redrive_policy.get("deadLetterTargetArn"))
    
    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return bool(self.kms_master_key_id) or self.sqs_managed_sse_enabled
    
    @property
    def uses_kms(self) -> bool:
        """Verifica se usa KMS."""
        return bool(self.kms_master_key_id)
    
    @property
    def uses_sse_sqs(self) -> bool:
        """Verifica se usa SSE-SQS."""
        return bool(self.sqs_managed_sse_enabled)
    
    @property
    def has_long_polling(self) -> bool:
        """Verifica se usa long polling."""
        return self.receive_message_wait_time_seconds > 0
    
    @property
    def has_delay(self) -> bool:
        """Verifica se tem delay."""
        return self.delay_seconds > 0
    
    @property
    def has_policy(self) -> bool:
        """Verifica se tem policy."""
        return bool(self.policy)
    
    @property
    def has_messages(self) -> bool:
        """Verifica se tem mensagens."""
        return self.approximate_number_of_messages > 0
    
    @property
    def has_in_flight_messages(self) -> bool:
        """Verifica se tem mensagens in-flight."""
        return self.approximate_number_of_messages_not_visible > 0
    
    @property
    def total_messages(self) -> int:
        """Retorna total de mensagens."""
        return (
            self.approximate_number_of_messages +
            self.approximate_number_of_messages_not_visible +
            self.approximate_number_of_messages_delayed
        )
    
    @property
    def has_tags(self) -> bool:
        """Verifica se tem tags."""
        return bool(self.tags)
    
    @property
    def max_receives(self) -> int:
        """Retorna máximo de receives antes de ir para DLQ."""
        return self.redrive_policy.get("maxReceiveCount", 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "queue_url": self.queue_url,
            "queue_name": self.queue_name,
            "is_fifo": self.is_fifo,
            "has_dlq": self.has_dlq,
            "has_encryption": self.has_encryption,
            "has_long_polling": self.has_long_polling,
            "approximate_number_of_messages": self.approximate_number_of_messages,
            "total_messages": self.total_messages,
            "visibility_timeout": self.visibility_timeout,
            "message_retention_period": self.message_retention_period
        }


class SQSService(BaseAWSService):
    """Serviço FinOps para Amazon SQS."""

    def __init__(self, client_factory):
        """Inicializa o serviço SQS."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)

    def _get_client(self):
        """Obtém cliente SQS."""
        return self._client_factory.get_client("sqs")

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço."""
        try:
            client = self._get_client()
            client.list_queues()
            return {"status": "healthy", "service": "sqs"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "service": "sqs", "error": str(e)}

    def get_resources(self) -> Dict[str, Any]:
        """Obtém recursos SQS."""
        client = self._get_client()
        
        queues = self._list_queues(client)
        
        fifo_queues = [q for q in queues if q.is_fifo]
        standard_queues = [q for q in queues if q.is_standard]
        queues_with_dlq = [q for q in queues if q.has_dlq]
        encrypted_queues = [q for q in queues if q.has_encryption]
        queues_with_messages = [q for q in queues if q.has_messages]
        
        total_messages = sum(q.total_messages for q in queues)
        
        return {
            "queues": [q.to_dict() for q in queues],
            "summary": {
                "total_queues": len(queues),
                "fifo_queues": len(fifo_queues),
                "standard_queues": len(standard_queues),
                "queues_with_dlq": len(queues_with_dlq),
                "encrypted_queues": len(encrypted_queues),
                "queues_with_messages": len(queues_with_messages),
                "total_messages": total_messages
            }
        }

    def get_costs(self) -> Dict[str, Any]:
        """Obtém custos SQS."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        standard_cost = summary["total_messages"] * 0.0000004
        fifo_cost = summary["total_messages"] * 0.00000035 * (summary["fifo_queues"] / max(summary["total_queues"], 1))
        
        return {
            "estimated_monthly": standard_cost + fifo_cost,
            "cost_factors": {
                "standard_requests": "$0.40 per million",
                "fifo_requests": "$0.35 per million (high throughput mode)",
                "data_transfer": "Standard AWS data transfer rates"
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas SQS."""
        resources = self.get_resources()
        summary = resources["summary"]
        
        return {
            "queues_count": summary["total_queues"],
            "fifo_queues": summary["fifo_queues"],
            "standard_queues": summary["standard_queues"],
            "queues_with_dlq": summary["queues_with_dlq"],
            "encrypted_queues": summary["encrypted_queues"],
            "total_messages": summary["total_messages"]
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Obtém recomendações de otimização."""
        recommendations = []
        resources = self.get_resources()
        
        for queue in resources["queues"]:
            if not queue.get("has_dlq"):
                recommendations.append({
                    "type": "ADD_DLQ",
                    "resource": queue["queue_name"],
                    "description": f"Fila '{queue['queue_name']}' sem Dead Letter Queue",
                    "impact": "high",
                    "action": "Configurar DLQ para tratamento de mensagens com falha"
                })
            
            if not queue.get("has_encryption"):
                recommendations.append({
                    "type": "ENABLE_ENCRYPTION",
                    "resource": queue["queue_name"],
                    "description": f"Fila '{queue['queue_name']}' sem criptografia",
                    "impact": "medium",
                    "action": "Habilitar SSE-SQS ou SSE-KMS"
                })
            
            if not queue.get("has_long_polling"):
                recommendations.append({
                    "type": "ENABLE_LONG_POLLING",
                    "resource": queue["queue_name"],
                    "description": f"Fila '{queue['queue_name']}' sem long polling",
                    "impact": "low",
                    "action": "Configurar ReceiveMessageWaitTimeSeconds > 0 para reduzir custos"
                })
        
        return recommendations

    def _list_queues(self, client) -> List[SQSQueue]:
        """Lista filas SQS."""
        queues = []
        try:
            paginator = client.get_paginator("list_queues")
            for page in paginator.paginate():
                for queue_url in page.get("QueueUrls", []):
                    queue = self._get_queue_details(client, queue_url)
                    if queue:
                        queues.append(queue)
        except Exception as e:
            self.logger.warning(f"Error listing queues: {e}")
        return queues

    def _get_queue_details(self, client, queue_url: str) -> Optional[SQSQueue]:
        """Obtém detalhes de uma fila."""
        try:
            response = client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["All"]
            )
            attrs = response.get("Attributes", {})
            
            queue_name = queue_url.split("/")[-1]
            
            redrive_policy = {}
            if attrs.get("RedrivePolicy"):
                import json
                try:
                    redrive_policy = json.loads(attrs.get("RedrivePolicy", "{}"))
                except Exception as e:  # noqa: E722
                    pass
            
            tags = {}
            try:
                tags_response = client.list_queue_tags(QueueUrl=queue_url)
                tags = tags_response.get("Tags", {})
            except Exception as e:  # noqa: E722
                pass
            
            return SQSQueue(
                queue_url=queue_url,
                queue_arn=attrs.get("QueueArn", ""),
                queue_name=queue_name,
                visibility_timeout=int(attrs.get("VisibilityTimeout", 30)),
                maximum_message_size=int(attrs.get("MaximumMessageSize", 262144)),
                message_retention_period=int(attrs.get("MessageRetentionPeriod", 345600)),
                delay_seconds=int(attrs.get("DelaySeconds", 0)),
                receive_message_wait_time_seconds=int(attrs.get("ReceiveMessageWaitTimeSeconds", 0)),
                approximate_number_of_messages=int(attrs.get("ApproximateNumberOfMessages", 0)),
                approximate_number_of_messages_not_visible=int(attrs.get("ApproximateNumberOfMessagesNotVisible", 0)),
                approximate_number_of_messages_delayed=int(attrs.get("ApproximateNumberOfMessagesDelayed", 0)),
                policy=attrs.get("Policy", ""),
                redrive_policy=redrive_policy,
                fifo_queue=attrs.get("FifoQueue", "false").lower() == "true",
                content_based_deduplication=attrs.get("ContentBasedDeduplication", "false").lower() == "true",
                kms_master_key_id=attrs.get("KmsMasterKeyId", ""),
                kms_data_key_reuse_period_seconds=int(attrs.get("KmsDataKeyReusePeriodSeconds", 300)),
                deduplication_scope=attrs.get("DeduplicationScope", ""),
                fifo_throughput_limit=attrs.get("FifoThroughputLimit", ""),
                sqs_managed_sse_enabled=attrs.get("SqsManagedSseEnabled", "false").lower() == "true",
                tags=tags
            )
        except Exception as e:
            self.logger.warning(f"Error getting queue details for {queue_url}: {e}")
            return None
