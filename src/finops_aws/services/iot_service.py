"""
AWS IoT Core Service para FinOps.

Análise de custos e otimização de recursos IoT Core.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class IoTThing:
    """Thing IoT."""
    thing_name: str
    thing_arn: str = ""
    thing_id: str = ""
    thing_type_name: str = ""
    version: int = 1
    attributes: Dict[str, str] = field(default_factory=dict)
    billing_group_name: str = ""

    @property
    def has_type(self) -> bool:
        """Verifica se tem tipo."""
        return bool(self.thing_type_name)

    @property
    def has_attributes(self) -> bool:
        """Verifica se tem atributos."""
        return len(self.attributes) > 0

    @property
    def attributes_count(self) -> int:
        """Número de atributos."""
        return len(self.attributes)

    @property
    def has_billing_group(self) -> bool:
        """Verifica se está em billing group."""
        return bool(self.billing_group_name)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "thing_name": self.thing_name,
            "thing_arn": self.thing_arn,
            "thing_type_name": self.thing_type_name,
            "version": self.version,
            "has_type": self.has_type,
            "has_attributes": self.has_attributes,
            "attributes_count": self.attributes_count,
            "has_billing_group": self.has_billing_group
        }


@dataclass
class IoTThingType:
    """Thing Type IoT."""
    thing_type_name: str
    thing_type_arn: str = ""
    thing_type_id: str = ""
    description: str = ""
    searchable_attributes: List[str] = field(default_factory=list)
    creation_date: Optional[datetime] = None
    deprecated: bool = False
    deprecation_date: Optional[datetime] = None

    @property
    def is_deprecated(self) -> bool:
        """Verifica se está deprecated."""
        return self.deprecated

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return not self.deprecated

    @property
    def searchable_attributes_count(self) -> int:
        """Número de atributos pesquisáveis."""
        return len(self.searchable_attributes)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "thing_type_name": self.thing_type_name,
            "thing_type_arn": self.thing_type_arn,
            "description": self.description,
            "is_deprecated": self.is_deprecated,
            "is_active": self.is_active,
            "searchable_attributes_count": self.searchable_attributes_count,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None
        }


@dataclass
class IoTPolicy:
    """Policy IoT."""
    policy_name: str
    policy_arn: str = ""
    policy_document: str = ""
    default_version_id: str = "1"
    creation_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None
    generation_id: str = ""

    @property
    def has_document(self) -> bool:
        """Verifica se tem documento."""
        return bool(self.policy_document)

    @property
    def version(self) -> int:
        """Versão como inteiro."""
        try:
            return int(self.default_version_id)
        except (ValueError, TypeError):
            return 1

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "policy_name": self.policy_name,
            "policy_arn": self.policy_arn,
            "default_version_id": self.default_version_id,
            "has_document": self.has_document,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None
        }


@dataclass
class IoTCertificate:
    """Certificado IoT."""
    certificate_id: str
    certificate_arn: str = ""
    status: str = "ACTIVE"
    creation_date: Optional[datetime] = None
    certificate_mode: str = "DEFAULT"
    customer_version: int = 1

    @property
    def is_active(self) -> bool:
        """Verifica se está ativo."""
        return self.status == "ACTIVE"

    @property
    def is_inactive(self) -> bool:
        """Verifica se está inativo."""
        return self.status == "INACTIVE"

    @property
    def is_revoked(self) -> bool:
        """Verifica se foi revogado."""
        return self.status == "REVOKED"

    @property
    def is_pending_transfer(self) -> bool:
        """Verifica se está em transferência."""
        return self.status == "PENDING_TRANSFER"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "certificate_id": self.certificate_id[:20] + "..." if len(self.certificate_id) > 20 else self.certificate_id,
            "certificate_arn": self.certificate_arn,
            "status": self.status,
            "is_active": self.is_active,
            "is_inactive": self.is_inactive,
            "is_revoked": self.is_revoked,
            "creation_date": self.creation_date.isoformat() if self.creation_date else None
        }


class IoTCoreService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS IoT Core."""

    def __init__(self, client_factory):
        """Inicializa o serviço IoT Core."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._iot_client = None

    @property
    def iot_client(self):
        """Cliente IoT com lazy loading."""
        if self._iot_client is None:
            self._iot_client = self._client_factory.get_client('iot')
        return self._iot_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço IoT Core."""
        try:
            self.iot_client.list_things(maxResults=1)
            return {
                "service": "iot",
                "status": "healthy",
                "message": "IoT Core service is accessible"
            }
        except Exception as e:
            return {
                "service": "iot",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_things(self) -> List[IoTThing]:
        """Lista things IoT."""
        things = []
        try:
            paginator = self.iot_client.get_paginator('list_things')
            for page in paginator.paginate():
                for thing in page.get('things', []):
                    things.append(IoTThing(
                        thing_name=thing.get('thingName', ''),
                        thing_arn=thing.get('thingArn', ''),
                        thing_type_name=thing.get('thingTypeName', ''),
                        version=thing.get('version', 1),
                        attributes=thing.get('attributes', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar things: {e}")
        return things

    def get_thing_types(self) -> List[IoTThingType]:
        """Lista thing types."""
        types = []
        try:
            paginator = self.iot_client.get_paginator('list_thing_types')
            for page in paginator.paginate():
                for tt in page.get('thingTypes', []):
                    metadata = tt.get('thingTypeMetadata', {})
                    props = tt.get('thingTypeProperties', {})
                    types.append(IoTThingType(
                        thing_type_name=tt.get('thingTypeName', ''),
                        thing_type_arn=tt.get('thingTypeArn', ''),
                        description=props.get('thingTypeDescription', ''),
                        searchable_attributes=props.get('searchableAttributes', []),
                        creation_date=metadata.get('creationDate'),
                        deprecated=metadata.get('deprecated', False),
                        deprecation_date=metadata.get('deprecationDate')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar thing types: {e}")
        return types

    def get_policies(self) -> List[IoTPolicy]:
        """Lista policies IoT."""
        policies = []
        try:
            paginator = self.iot_client.get_paginator('list_policies')
            for page in paginator.paginate():
                for policy in page.get('policies', []):
                    policies.append(IoTPolicy(
                        policy_name=policy.get('policyName', ''),
                        policy_arn=policy.get('policyArn', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar policies: {e}")
        return policies

    def get_certificates(self) -> List[IoTCertificate]:
        """Lista certificados IoT."""
        certificates = []
        try:
            paginator = self.iot_client.get_paginator('list_certificates')
            for page in paginator.paginate():
                for cert in page.get('certificates', []):
                    certificates.append(IoTCertificate(
                        certificate_id=cert.get('certificateId', ''),
                        certificate_arn=cert.get('certificateArn', ''),
                        status=cert.get('status', 'ACTIVE'),
                        creation_date=cert.get('creationDate'),
                        certificate_mode=cert.get('certificateMode', 'DEFAULT')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar certificados: {e}")
        return certificates

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos IoT Core."""
        things = self.get_things()
        thing_types = self.get_thing_types()
        policies = self.get_policies()
        certificates = self.get_certificates()

        return {
            "things": [t.to_dict() for t in things[:100]],
            "thing_types": [t.to_dict() for t in thing_types],
            "policies": [p.to_dict() for p in policies],
            "certificates": [c.to_dict() for c in certificates[:50]],
            "summary": {
                "total_things": len(things),
                "things_with_type": len([t for t in things if t.has_type]),
                "things_with_attributes": len([t for t in things if t.has_attributes]),
                "total_thing_types": len(thing_types),
                "active_thing_types": len([t for t in thing_types if t.is_active]),
                "deprecated_thing_types": len([t for t in thing_types if t.is_deprecated]),
                "total_policies": len(policies),
                "total_certificates": len(certificates),
                "active_certificates": len([c for c in certificates if c.is_active]),
                "inactive_certificates": len([c for c in certificates if c.is_inactive])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do IoT Core."""
        things = self.get_things()
        thing_types = self.get_thing_types()
        policies = self.get_policies()
        certificates = self.get_certificates()

        return {
            "things_count": len(things),
            "things_with_type": len([t for t in things if t.has_type]),
            "things_with_attributes": len([t for t in things if t.has_attributes]),
            "thing_types_count": len(thing_types),
            "active_thing_types": len([t for t in thing_types if t.is_active]),
            "deprecated_thing_types": len([t for t in thing_types if t.is_deprecated]),
            "policies_count": len(policies),
            "certificates_count": len(certificates),
            "active_certificates": len([c for c in certificates if c.is_active]),
            "inactive_certificates": len([c for c in certificates if c.is_inactive]),
            "revoked_certificates": len([c for c in certificates if c.is_revoked])
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para IoT Core."""
        recommendations = []
        things = self.get_things()
        thing_types = self.get_thing_types()
        certificates = self.get_certificates()

        no_type = [t for t in things if not t.has_type]
        if len(no_type) > 10:
            recommendations.append({
                "resource_type": "IoTThing",
                "resource_id": "multiple",
                "recommendation": "Organizar things com tipos",
                "description": f"{len(no_type)} thing(s) sem tipo. "
                               "Usar thing types para melhor organização.",
                "priority": "low"
            })

        deprecated_types = [t for t in thing_types if t.is_deprecated]
        if deprecated_types:
            recommendations.append({
                "resource_type": "IoTThingType",
                "resource_id": "multiple",
                "recommendation": "Remover thing types deprecated",
                "description": f"{len(deprecated_types)} thing type(s) deprecated. "
                               "Considerar remover após migrar things.",
                "priority": "low"
            })

        inactive_certs = [c for c in certificates if c.is_inactive]
        if inactive_certs:
            recommendations.append({
                "resource_type": "IoTCertificate",
                "resource_id": "multiple",
                "recommendation": "Remover certificados inativos",
                "description": f"{len(inactive_certs)} certificado(s) inativo(s). "
                               "Considerar remover se não forem mais necessários.",
                "priority": "medium"
            })

        return recommendations
