"""
AWS Transit Gateway Service para FinOps.

Análise de custos e otimização de Transit Gateways.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class TransitGateway:
    """Transit Gateway AWS."""
    transit_gateway_id: str
    transit_gateway_arn: str = ""
    state: str = "available"
    owner_id: str = ""
    description: str = ""
    creation_time: Optional[datetime] = None
    options: Dict[str, Any] = field(default_factory=dict)
    tags: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.state == "available"

    @property
    def is_pending(self) -> bool:
        """Verifica se está pending."""
        return self.state == "pending"

    @property
    def is_deleting(self) -> bool:
        """Verifica se está sendo deletado."""
        return self.state == "deleting"

    @property
    def amazon_side_asn(self) -> int:
        """ASN do lado Amazon."""
        return self.options.get('AmazonSideAsn', 0)

    @property
    def auto_accept_shared_attachments(self) -> bool:
        """Verifica se aceita attachments automaticamente."""
        return self.options.get('AutoAcceptSharedAttachments', 'disable') == 'enable'

    @property
    def default_route_table_association(self) -> bool:
        """Verifica se usa route table padrão."""
        return self.options.get('DefaultRouteTableAssociation', 'enable') == 'enable'

    @property
    def dns_support(self) -> bool:
        """Verifica se tem suporte DNS."""
        return self.options.get('DnsSupport', 'enable') == 'enable'

    @property
    def vpn_ecmp_support(self) -> bool:
        """Verifica se tem suporte VPN ECMP."""
        return self.options.get('VpnEcmpSupport', 'enable') == 'enable'

    @property
    def multicast_support(self) -> bool:
        """Verifica se tem suporte multicast."""
        return self.options.get('MulticastSupport', 'disable') == 'enable'

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora do Transit Gateway ($0.05/hora)."""
        return 0.05 if self.is_available else 0.0

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado (base)."""
        return self.estimated_hourly_cost * 24 * 30

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "transit_gateway_id": self.transit_gateway_id,
            "transit_gateway_arn": self.transit_gateway_arn,
            "state": self.state,
            "owner_id": self.owner_id,
            "description": self.description,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "is_available": self.is_available,
            "amazon_side_asn": self.amazon_side_asn,
            "auto_accept_shared_attachments": self.auto_accept_shared_attachments,
            "default_route_table_association": self.default_route_table_association,
            "dns_support": self.dns_support,
            "vpn_ecmp_support": self.vpn_ecmp_support,
            "multicast_support": self.multicast_support,
            "estimated_hourly_cost": self.estimated_hourly_cost,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class TransitGatewayAttachment:
    """Attachment do Transit Gateway."""
    transit_gateway_attachment_id: str
    transit_gateway_id: str = ""
    transit_gateway_owner_id: str = ""
    resource_owner_id: str = ""
    resource_type: str = ""
    resource_id: str = ""
    state: str = "available"
    association: Dict[str, Any] = field(default_factory=dict)
    creation_time: Optional[datetime] = None
    tags: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.state == "available"

    @property
    def is_pending(self) -> bool:
        """Verifica se está pending."""
        return self.state in ["pending", "pendingAcceptance", "initiating"]

    @property
    def is_vpc(self) -> bool:
        """Verifica se é attachment VPC."""
        return self.resource_type == "vpc"

    @property
    def is_vpn(self) -> bool:
        """Verifica se é attachment VPN."""
        return self.resource_type == "vpn"

    @property
    def is_direct_connect(self) -> bool:
        """Verifica se é attachment Direct Connect."""
        return self.resource_type == "direct-connect-gateway"

    @property
    def is_peering(self) -> bool:
        """Verifica se é attachment peering."""
        return self.resource_type == "peering"

    @property
    def is_tgw_connect(self) -> bool:
        """Verifica se é attachment Connect."""
        return self.resource_type == "connect"

    @property
    def has_association(self) -> bool:
        """Verifica se tem associação."""
        return bool(self.association)

    @property
    def route_table_id(self) -> Optional[str]:
        """ID da route table associada."""
        return self.association.get('TransitGatewayRouteTableId')

    @property
    def estimated_hourly_cost(self) -> float:
        """Custo por hora do attachment ($0.05/hora)."""
        return 0.05 if self.is_available else 0.0

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado."""
        return self.estimated_hourly_cost * 24 * 30

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "transit_gateway_attachment_id": self.transit_gateway_attachment_id,
            "transit_gateway_id": self.transit_gateway_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "state": self.state,
            "is_available": self.is_available,
            "is_vpc": self.is_vpc,
            "is_vpn": self.is_vpn,
            "is_direct_connect": self.is_direct_connect,
            "is_peering": self.is_peering,
            "has_association": self.has_association,
            "route_table_id": self.route_table_id,
            "estimated_hourly_cost": self.estimated_hourly_cost,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class TransitGatewayRouteTable:
    """Route Table do Transit Gateway."""
    transit_gateway_route_table_id: str
    transit_gateway_id: str = ""
    state: str = "available"
    default_association_route_table: bool = False
    default_propagation_route_table: bool = False
    creation_time: Optional[datetime] = None
    tags: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.state == "available"

    @property
    def is_default_association(self) -> bool:
        """Verifica se é default para associação."""
        return self.default_association_route_table

    @property
    def is_default_propagation(self) -> bool:
        """Verifica se é default para propagação."""
        return self.default_propagation_route_table

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "transit_gateway_route_table_id": self.transit_gateway_route_table_id,
            "transit_gateway_id": self.transit_gateway_id,
            "state": self.state,
            "default_association_route_table": self.default_association_route_table,
            "default_propagation_route_table": self.default_propagation_route_table,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None,
            "is_available": self.is_available,
            "is_default_association": self.is_default_association,
            "is_default_propagation": self.is_default_propagation
        }


@dataclass
class TransitGatewayPeeringAttachment:
    """Peering Attachment do Transit Gateway."""
    transit_gateway_attachment_id: str
    requester_tgw_info: Dict[str, Any] = field(default_factory=dict)
    accepter_tgw_info: Dict[str, Any] = field(default_factory=dict)
    state: str = "available"
    creation_time: Optional[datetime] = None
    tags: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.state == "available"

    @property
    def is_pending_acceptance(self) -> bool:
        """Verifica se está pendente aceitação."""
        return self.state == "pendingAcceptance"

    @property
    def requester_transit_gateway_id(self) -> str:
        """ID do TGW solicitante."""
        return self.requester_tgw_info.get('TransitGatewayId', '')

    @property
    def accepter_transit_gateway_id(self) -> str:
        """ID do TGW aceitante."""
        return self.accepter_tgw_info.get('TransitGatewayId', '')

    @property
    def is_cross_region(self) -> bool:
        """Verifica se é cross-region."""
        req_region = self.requester_tgw_info.get('Region', '')
        acc_region = self.accepter_tgw_info.get('Region', '')
        return req_region != acc_region and req_region and acc_region

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "transit_gateway_attachment_id": self.transit_gateway_attachment_id,
            "requester_transit_gateway_id": self.requester_transit_gateway_id,
            "accepter_transit_gateway_id": self.accepter_transit_gateway_id,
            "state": self.state,
            "is_available": self.is_available,
            "is_pending_acceptance": self.is_pending_acceptance,
            "is_cross_region": self.is_cross_region,
            "creation_time": self.creation_time.isoformat() if self.creation_time else None
        }


class TransitGatewayService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Transit Gateway."""

    def __init__(self, client_factory):
        """Inicializa o serviço Transit Gateway."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._ec2_client = None

    @property
    def ec2_client(self):
        """Cliente EC2 com lazy loading."""
        if self._ec2_client is None:
            self._ec2_client = self._client_factory.get_client('ec2')
        return self._ec2_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Transit Gateway."""
        try:
            self.ec2_client.describe_transit_gateways(MaxResults=5)
            return {
                "service": "transitgateway",
                "status": "healthy",
                "message": "Transit Gateway service is accessible"
            }
        except Exception as e:
            return {
                "service": "transitgateway",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_transit_gateways(self) -> List[TransitGateway]:
        """Lista Transit Gateways."""
        tgws = []
        try:
            paginator = self.ec2_client.get_paginator('describe_transit_gateways')
            for page in paginator.paginate():
                for tgw in page.get('TransitGateways', []):
                    tgws.append(TransitGateway(
                        transit_gateway_id=tgw.get('TransitGatewayId', ''),
                        transit_gateway_arn=tgw.get('TransitGatewayArn', ''),
                        state=tgw.get('State', 'available'),
                        owner_id=tgw.get('OwnerId', ''),
                        description=tgw.get('Description', ''),
                        creation_time=tgw.get('CreationTime'),
                        options=tgw.get('Options', {}),
                        tags=tgw.get('Tags', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar Transit Gateways: {e}")
        return tgws

    def get_attachments(self) -> List[TransitGatewayAttachment]:
        """Lista attachments."""
        attachments = []
        try:
            paginator = self.ec2_client.get_paginator('describe_transit_gateway_attachments')
            for page in paginator.paginate():
                for att in page.get('TransitGatewayAttachments', []):
                    attachments.append(TransitGatewayAttachment(
                        transit_gateway_attachment_id=att.get('TransitGatewayAttachmentId', ''),
                        transit_gateway_id=att.get('TransitGatewayId', ''),
                        transit_gateway_owner_id=att.get('TransitGatewayOwnerId', ''),
                        resource_owner_id=att.get('ResourceOwnerId', ''),
                        resource_type=att.get('ResourceType', ''),
                        resource_id=att.get('ResourceId', ''),
                        state=att.get('State', 'available'),
                        association=att.get('Association', {}),
                        creation_time=att.get('CreationTime'),
                        tags=att.get('Tags', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar attachments: {e}")
        return attachments

    def get_route_tables(self) -> List[TransitGatewayRouteTable]:
        """Lista route tables."""
        route_tables = []
        try:
            paginator = self.ec2_client.get_paginator('describe_transit_gateway_route_tables')
            for page in paginator.paginate():
                for rt in page.get('TransitGatewayRouteTables', []):
                    route_tables.append(TransitGatewayRouteTable(
                        transit_gateway_route_table_id=rt.get('TransitGatewayRouteTableId', ''),
                        transit_gateway_id=rt.get('TransitGatewayId', ''),
                        state=rt.get('State', 'available'),
                        default_association_route_table=rt.get('DefaultAssociationRouteTable', False),
                        default_propagation_route_table=rt.get('DefaultPropagationRouteTable', False),
                        creation_time=rt.get('CreationTime'),
                        tags=rt.get('Tags', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar route tables: {e}")
        return route_tables

    def get_peering_attachments(self) -> List[TransitGatewayPeeringAttachment]:
        """Lista peering attachments."""
        peerings = []
        try:
            paginator = self.ec2_client.get_paginator('describe_transit_gateway_peering_attachments')
            for page in paginator.paginate():
                for peer in page.get('TransitGatewayPeeringAttachments', []):
                    peerings.append(TransitGatewayPeeringAttachment(
                        transit_gateway_attachment_id=peer.get('TransitGatewayAttachmentId', ''),
                        requester_tgw_info=peer.get('RequesterTgwInfo', {}),
                        accepter_tgw_info=peer.get('AccepterTgwInfo', {}),
                        state=peer.get('State', 'available'),
                        creation_time=peer.get('CreationTime'),
                        tags=peer.get('Tags', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar peering attachments: {e}")
        return peerings

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Transit Gateway."""
        tgws = self.get_transit_gateways()
        attachments = self.get_attachments()
        route_tables = self.get_route_tables()
        peerings = self.get_peering_attachments()

        tgw_cost = sum(t.estimated_monthly_cost for t in tgws)
        attachment_cost = sum(a.estimated_monthly_cost for a in attachments)

        return {
            "transit_gateways": [t.to_dict() for t in tgws],
            "attachments": [a.to_dict() for a in attachments],
            "route_tables": [r.to_dict() for r in route_tables],
            "peering_attachments": [p.to_dict() for p in peerings],
            "summary": {
                "total_transit_gateways": len(tgws),
                "available_tgws": len([t for t in tgws if t.is_available]),
                "total_attachments": len(attachments),
                "vpc_attachments": len([a for a in attachments if a.is_vpc]),
                "vpn_attachments": len([a for a in attachments if a.is_vpn]),
                "dx_attachments": len([a for a in attachments if a.is_direct_connect]),
                "peering_attachments": len([a for a in attachments if a.is_peering]),
                "total_route_tables": len(route_tables),
                "cross_region_peerings": len([p for p in peerings if p.is_cross_region]),
                "estimated_monthly_cost": tgw_cost + attachment_cost
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Transit Gateway."""
        tgws = self.get_transit_gateways()
        attachments = self.get_attachments()
        route_tables = self.get_route_tables()
        peerings = self.get_peering_attachments()

        return {
            "transit_gateways_count": len(tgws),
            "available_tgws": len([t for t in tgws if t.is_available]),
            "tgws_with_multicast": len([t for t in tgws if t.multicast_support]),
            "tgws_with_dns_support": len([t for t in tgws if t.dns_support]),
            "attachments_count": len(attachments),
            "attachment_types": {
                "vpc": len([a for a in attachments if a.is_vpc]),
                "vpn": len([a for a in attachments if a.is_vpn]),
                "direct_connect": len([a for a in attachments if a.is_direct_connect]),
                "peering": len([a for a in attachments if a.is_peering]),
                "connect": len([a for a in attachments if a.is_tgw_connect])
            },
            "route_tables_count": len(route_tables),
            "peering_attachments_count": len(peerings),
            "cross_region_peerings": len([p for p in peerings if p.is_cross_region]),
            "estimated_monthly_cost": sum(t.estimated_monthly_cost for t in tgws) + sum(a.estimated_monthly_cost for a in attachments)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Transit Gateway."""
        recommendations = []
        tgws = self.get_transit_gateways()
        attachments = self.get_attachments()
        peerings = self.get_peering_attachments()

        # Verificar TGWs sem attachments
        tgw_ids_with_attachments = set(a.transit_gateway_id for a in attachments)
        tgws_without_attachments = [t for t in tgws if t.transit_gateway_id not in tgw_ids_with_attachments and t.is_available]
        
        if tgws_without_attachments:
            recommendations.append({
                "resource_type": "TransitGateway",
                "resource_id": "multiple",
                "recommendation": "Remover Transit Gateways sem attachments",
                "description": f"{len(tgws_without_attachments)} Transit Gateway(s) sem attachments. "
                               "Considerar remover se não for mais necessário.",
                "estimated_savings": sum(t.estimated_monthly_cost for t in tgws_without_attachments),
                "priority": "medium"
            })

        # Verificar attachments pendentes
        pending_attachments = [a for a in attachments if a.is_pending]
        if pending_attachments:
            recommendations.append({
                "resource_type": "TransitGatewayAttachment",
                "resource_id": "multiple",
                "recommendation": "Verificar attachments pendentes",
                "description": f"{len(pending_attachments)} attachment(s) em estado pending. "
                               "Verificar e resolver problemas de conectividade.",
                "priority": "medium"
            })

        # Verificar peerings pendentes
        pending_peerings = [p for p in peerings if p.is_pending_acceptance]
        if pending_peerings:
            recommendations.append({
                "resource_type": "TransitGatewayPeeringAttachment",
                "resource_id": "multiple",
                "recommendation": "Aceitar peerings pendentes",
                "description": f"{len(pending_peerings)} peering(s) aguardando aceitação. "
                               "Aceitar ou rejeitar conforme necessário.",
                "priority": "high"
            })

        # Verificar TGWs sem DNS support
        no_dns = [t for t in tgws if t.is_available and not t.dns_support]
        if no_dns:
            recommendations.append({
                "resource_type": "TransitGateway",
                "resource_id": "multiple",
                "recommendation": "Habilitar DNS support",
                "description": f"{len(no_dns)} Transit Gateway(s) sem suporte DNS. "
                               "Habilitar para resolução de DNS cross-VPC.",
                "priority": "low"
            })

        return recommendations
