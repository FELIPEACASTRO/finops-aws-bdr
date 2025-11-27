"""
AWS IoT Events Service para FinOps.

Análise de custos e otimização de recursos IoT Events.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class IoTEventsDetectorModel:
    """Detector Model IoT Events."""
    detector_model_name: str
    detector_model_arn: str = ""
    detector_model_description: str = ""
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    status: str = "ACTIVE"
    evaluation_method: str = "BATCH"
    key: str = ""
    role_arn: str = ""

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_activating(self) -> bool:
        """Verifica se está ativando."""
        return self.status == "ACTIVATING"

    @property
    def is_inactive(self) -> bool:
        """Verifica se está inativo."""
        return self.status == "INACTIVE"

    @property
    def uses_batch_evaluation(self) -> bool:
        """Verifica se usa avaliação batch."""
        return self.evaluation_method == "BATCH"

    @property
    def uses_serial_evaluation(self) -> bool:
        """Verifica se usa avaliação serial."""
        return self.evaluation_method == "SERIAL"

    @property
    def has_key(self) -> bool:
        """Verifica se tem key para particionamento."""
        return bool(self.key)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "detector_model_name": self.detector_model_name,
            "detector_model_arn": self.detector_model_arn,
            "detector_model_description": self.detector_model_description,
            "status": self.status,
            "is_active": self.is_active,
            "evaluation_method": self.evaluation_method,
            "uses_batch_evaluation": self.uses_batch_evaluation,
            "has_key": self.has_key,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class IoTEventsInput:
    """Input IoT Events."""
    input_name: str
    input_arn: str = ""
    input_description: str = ""
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    status: str = "ACTIVE"
    input_definition: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def attributes_count(self) -> int:
        """Número de atributos."""
        return len(self.input_definition.get('attributes', []))

    @property
    def has_definition(self) -> bool:
        """Verifica se tem definição."""
        return bool(self.input_definition)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "input_name": self.input_name,
            "input_arn": self.input_arn,
            "input_description": self.input_description,
            "status": self.status,
            "is_active": self.is_active,
            "attributes_count": self.attributes_count,
            "has_definition": self.has_definition,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


@dataclass
class IoTEventsAlarmModel:
    """Alarm Model IoT Events."""
    alarm_model_name: str
    alarm_model_arn: str = ""
    alarm_model_description: str = ""
    creation_time: Optional[datetime] = None
    last_update_time: Optional[datetime] = None
    status: str = "ACTIVE"
    severity: int = 1
    role_arn: str = ""
    alarm_model_version: str = "1"

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_activating(self) -> bool:
        """Verifica se está ativando."""
        return self.status == "ACTIVATING"

    @property
    def is_inactive(self) -> bool:
        """Verifica se está inativo."""
        return self.status == "INACTIVE"

    @property
    def is_critical(self) -> bool:
        """Verifica se é crítico (severidade >= 8)."""
        return self.severity >= 8

    @property
    def is_high(self) -> bool:
        """Verifica se é alta severidade (5-7)."""
        return 5 <= self.severity < 8

    @property
    def is_medium(self) -> bool:
        """Verifica se é média severidade (3-4)."""
        return 3 <= self.severity < 5

    @property
    def is_low(self) -> bool:
        """Verifica se é baixa severidade (1-2)."""
        return self.severity < 3

    @property
    def version_number(self) -> int:
        """Número da versão."""
        try:
            return int(self.alarm_model_version)
        except (ValueError, TypeError):
            return 1

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "alarm_model_name": self.alarm_model_name,
            "alarm_model_arn": self.alarm_model_arn,
            "alarm_model_description": self.alarm_model_description,
            "status": self.status,
            "is_active": self.is_active,
            "severity": self.severity,
            "is_critical": self.is_critical,
            "is_high": self.is_high,
            "alarm_model_version": self.alarm_model_version,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


class IoTEventsService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS IoT Events."""

    def __init__(self, client_factory):
        """Inicializa o serviço IoT Events."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._iotevents_client = None

    @property
    def iotevents_client(self):
        """Cliente IoT Events com lazy loading."""
        if self._iotevents_client is None:
            self._iotevents_client = self._client_factory.get_client('iotevents')
        return self._iotevents_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço IoT Events."""
        try:
            self.iotevents_client.list_detector_models()
            return {
                "service": "iotevents",
                "status": "healthy",
                "message": "IoT Events service is accessible"
            }
        except Exception as e:
            return {
                "service": "iotevents",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_detector_models(self) -> List[IoTEventsDetectorModel]:
        """Lista detector models."""
        models = []
        try:
            response = self.iotevents_client.list_detector_models()
            for model in response.get('detectorModelSummaries', []):
                models.append(IoTEventsDetectorModel(
                    detector_model_name=model.get('detectorModelName', ''),
                    detector_model_arn=model.get('detectorModelArn', ''),
                    detector_model_description=model.get('detectorModelDescription', ''),
                    creation_time=model.get('creationTime')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar detector models: {e}")
        return models

    def get_inputs(self) -> List[IoTEventsInput]:
        """Lista inputs."""
        inputs = []
        try:
            response = self.iotevents_client.list_inputs()
            for inp in response.get('inputSummaries', []):
                inputs.append(IoTEventsInput(
                    input_name=inp.get('inputName', ''),
                    input_arn=inp.get('inputArn', ''),
                    input_description=inp.get('inputDescription', ''),
                    creation_time=inp.get('creationTime'),
                    last_update_time=inp.get('lastUpdateTime'),
                    status=inp.get('status', 'ACTIVE')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar inputs: {e}")
        return inputs

    def get_alarm_models(self) -> List[IoTEventsAlarmModel]:
        """Lista alarm models."""
        alarms = []
        try:
            response = self.iotevents_client.list_alarm_models()
            for alarm in response.get('alarmModelSummaries', []):
                alarms.append(IoTEventsAlarmModel(
                    alarm_model_name=alarm.get('alarmModelName', ''),
                    alarm_model_arn=alarm.get('alarmModelArn', ''),
                    alarm_model_description=alarm.get('alarmModelDescription', ''),
                    creation_time=alarm.get('creationTime')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar alarm models: {e}")
        return alarms

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos IoT Events."""
        detector_models = self.get_detector_models()
        inputs = self.get_inputs()
        alarm_models = self.get_alarm_models()

        return {
            "detector_models": [d.to_dict() for d in detector_models],
            "inputs": [i.to_dict() for i in inputs],
            "alarm_models": [a.to_dict() for a in alarm_models],
            "summary": {
                "total_detector_models": len(detector_models),
                "active_detector_models": len([d for d in detector_models if d.is_active]),
                "total_inputs": len(inputs),
                "active_inputs": len([i for i in inputs if i.is_active]),
                "total_alarm_models": len(alarm_models),
                "active_alarm_models": len([a for a in alarm_models if a.is_active]),
                "critical_alarms": len([a for a in alarm_models if a.is_critical]),
                "high_severity_alarms": len([a for a in alarm_models if a.is_high])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do IoT Events."""
        detector_models = self.get_detector_models()
        inputs = self.get_inputs()
        alarm_models = self.get_alarm_models()

        return {
            "detector_models_count": len(detector_models),
            "active_detector_models": len([d for d in detector_models if d.is_active]),
            "batch_evaluation_models": len([d for d in detector_models if d.uses_batch_evaluation]),
            "serial_evaluation_models": len([d for d in detector_models if d.uses_serial_evaluation]),
            "inputs_count": len(inputs),
            "active_inputs": len([i for i in inputs if i.is_active]),
            "alarm_models_count": len(alarm_models),
            "active_alarm_models": len([a for a in alarm_models if a.is_active]),
            "alarm_severity": {
                "critical": len([a for a in alarm_models if a.is_critical]),
                "high": len([a for a in alarm_models if a.is_high]),
                "medium": len([a for a in alarm_models if a.is_medium]),
                "low": len([a for a in alarm_models if a.is_low])
            }
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para IoT Events."""
        recommendations = []
        detector_models = self.get_detector_models()
        inputs = self.get_inputs()
        alarm_models = self.get_alarm_models()

        inactive_detectors = [d for d in detector_models if d.is_inactive]
        if inactive_detectors:
            recommendations.append({
                "resource_type": "IoTEventsDetectorModel",
                "resource_id": "multiple",
                "recommendation": "Remover detector models inativos",
                "description": f"{len(inactive_detectors)} detector model(s) inativo(s). "
                               "Considerar remover se não forem mais necessários.",
                "priority": "low"
            })

        inactive_inputs = [i for i in inputs if not i.is_active]
        if inactive_inputs:
            recommendations.append({
                "resource_type": "IoTEventsInput",
                "resource_id": "multiple",
                "recommendation": "Remover inputs inativos",
                "description": f"{len(inactive_inputs)} input(s) inativo(s). "
                               "Considerar remover se não forem mais necessários.",
                "priority": "low"
            })

        inactive_alarms = [a for a in alarm_models if a.is_inactive]
        if inactive_alarms:
            recommendations.append({
                "resource_type": "IoTEventsAlarmModel",
                "resource_id": "multiple",
                "recommendation": "Remover alarm models inativos",
                "description": f"{len(inactive_alarms)} alarm model(s) inativo(s). "
                               "Considerar remover se não forem mais necessários.",
                "priority": "low"
            })

        return recommendations
