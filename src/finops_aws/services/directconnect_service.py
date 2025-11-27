"""
AWS Direct Connect Service para FinOps.

Análise de custos e otimização de conexões dedicadas.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class DirectConnectConnection:
    """Conexão Direct Connect."""
    connection_id: str
    connection_name: str = ""
    connection_state: str = "available"
    region: str = ""
    location: str = ""
    bandwidth: str = "1Gbps"
    vlan: int = 0
    partner_name: str = ""
    loa_issue_time: Optional[datetime] = None
    lag_id: Optional[str] = None
    aws_device: str = ""
    aws_device_v2: str = ""
    has_logical_redundancy: Optional[str] = None
    jumbo_frame_capable: bool = False
    port_encryption_status: str = ""
    encryption_mode: str = ""
    mac_sec_capable: bool = False

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.connection_state == "available"

    @property
    def is_down(self) -> bool:
        """Verifica se está down."""
        return self.connection_state == "down"

    @property
    def is_pending(self) -> bool:
        """Verifica se está pending."""
        return self.connection_state in ["pending", "ordering", "requested"]

    @property
    def bandwidth_gbps(self) -> float:
        """Bandwidth em Gbps."""
        bw = self.bandwidth.lower()
        if "gbps" in bw:
            return float(bw.replace("gbps", ""))
        elif "mbps" in bw:
            return float(bw.replace("mbps", "")) / 1000
        return 0.0

    @property
    def is_lag_member(self) -> bool:
        """Verifica se é membro de LAG."""
        return self.lag_id is not None

    @property
    def supports_jumbo_frames(self) -> bool:
        """Verifica se suporta jumbo frames."""
        return self.jumbo_frame_capable

    @property
    def supports_macsec(self) -> bool:
        """Verifica se suporta MACsec."""
        return self.mac_sec_capable

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia."""
        return self.port_encryption_status == "enabled"

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado (baseado em port hour)."""
        rates = {
            0.05: 0.03,    # 50Mbps
            0.1: 0.03,     # 100Mbps
            0.2: 0.03,     # 200Mbps
            0.3: 0.04,     # 300Mbps
            0.4: 0.05,     # 400Mbps
            0.5: 0.06,     # 500Mbps
            1.0: 0.22,     # 1Gbps
            2.0: 0.22,     # 2Gbps
            5.0: 0.22,     # 5Gbps
            10.0: 1.50,    # 10Gbps
            100.0: 12.00,  # 100Gbps
        }
        rate = rates.get(self.bandwidth_gbps, 0.22)
        return rate * 24 * 30 if self.is_available else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "connection_id": self.connection_id,
            "connection_name": self.connection_name,
            "connection_state": self.connection_state,
            "region": self.region,
            "location": self.location,
            "bandwidth": self.bandwidth,
            "bandwidth_gbps": self.bandwidth_gbps,
            "vlan": self.vlan,
            "partner_name": self.partner_name,
            "is_available": self.is_available,
            "is_down": self.is_down,
            "is_lag_member": self.is_lag_member,
            "supports_jumbo_frames": self.supports_jumbo_frames,
            "supports_macsec": self.supports_macsec,
            "has_encryption": self.has_encryption,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class VirtualInterface:
    """Interface Virtual Direct Connect."""
    virtual_interface_id: str
    virtual_interface_name: str = ""
    virtual_interface_type: str = "private"
    virtual_interface_state: str = "available"
    connection_id: str = ""
    vlan: int = 0
    asn: int = 0
    amazon_side_asn: int = 0
    mtu: int = 1500
    auth_key: str = ""
    amazon_address: str = ""
    customer_address: str = ""
    address_family: str = "ipv4"
    bgp_peers: List[Dict[str, Any]] = field(default_factory=list)
    route_filter_prefixes: List[Dict[str, Any]] = field(default_factory=list)
    direct_connect_gateway_id: Optional[str] = None
    virtual_gateway_id: Optional[str] = None
    region: str = ""
    aws_device_v2: str = ""
    jumbo_frame_capable: bool = False
    tags: List[Dict[str, str]] = field(default_factory=list)

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.virtual_interface_state == "available"

    @property
    def is_private(self) -> bool:
        """Verifica se é private VIF."""
        return self.virtual_interface_type == "private"

    @property
    def is_public(self) -> bool:
        """Verifica se é public VIF."""
        return self.virtual_interface_type == "public"

    @property
    def is_transit(self) -> bool:
        """Verifica se é transit VIF."""
        return self.virtual_interface_type == "transit"

    @property
    def supports_ipv6(self) -> bool:
        """Verifica se suporta IPv6."""
        return self.address_family == "ipv6" or any(
            peer.get('addressFamily') == 'ipv6' for peer in self.bgp_peers
        )

    @property
    def bgp_peers_count(self) -> int:
        """Número de BGP peers."""
        return len(self.bgp_peers)

    @property
    def uses_jumbo_mtu(self) -> bool:
        """Verifica se usa jumbo MTU."""
        return self.mtu > 1500

    @property
    def has_dcgw(self) -> bool:
        """Verifica se está conectado a Direct Connect Gateway."""
        return self.direct_connect_gateway_id is not None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "virtual_interface_id": self.virtual_interface_id,
            "virtual_interface_name": self.virtual_interface_name,
            "virtual_interface_type": self.virtual_interface_type,
            "virtual_interface_state": self.virtual_interface_state,
            "connection_id": self.connection_id,
            "vlan": self.vlan,
            "mtu": self.mtu,
            "address_family": self.address_family,
            "is_available": self.is_available,
            "is_private": self.is_private,
            "is_public": self.is_public,
            "is_transit": self.is_transit,
            "supports_ipv6": self.supports_ipv6,
            "bgp_peers_count": self.bgp_peers_count,
            "uses_jumbo_mtu": self.uses_jumbo_mtu,
            "has_dcgw": self.has_dcgw
        }


@dataclass
class DirectConnectGateway:
    """Gateway Direct Connect."""
    direct_connect_gateway_id: str
    direct_connect_gateway_name: str = ""
    amazon_side_asn: int = 0
    owner_account: str = ""
    direct_connect_gateway_state: str = "available"
    state_change_error: str = ""

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.direct_connect_gateway_state == "available"

    @property
    def is_pending(self) -> bool:
        """Verifica se está pending."""
        return self.direct_connect_gateway_state == "pending"

    @property
    def is_deleting(self) -> bool:
        """Verifica se está sendo deletado."""
        return self.direct_connect_gateway_state == "deleting"

    @property
    def has_error(self) -> bool:
        """Verifica se tem erro."""
        return bool(self.state_change_error)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "direct_connect_gateway_id": self.direct_connect_gateway_id,
            "direct_connect_gateway_name": self.direct_connect_gateway_name,
            "amazon_side_asn": self.amazon_side_asn,
            "owner_account": self.owner_account,
            "direct_connect_gateway_state": self.direct_connect_gateway_state,
            "is_available": self.is_available,
            "is_pending": self.is_pending,
            "has_error": self.has_error
        }


@dataclass
class LinkAggregationGroup:
    """Link Aggregation Group (LAG)."""
    lag_id: str
    lag_name: str = ""
    lag_state: str = "available"
    location: str = ""
    region: str = ""
    minimum_links: int = 0
    number_of_connections: int = 0
    allows_hosted_connections: bool = False
    connections_bandwidth: str = ""
    owner_account: str = ""
    jumbo_frame_capable: bool = False
    encryption_mode: str = ""
    mac_sec_capable: bool = False

    @property
    def is_available(self) -> bool:
        """Verifica se está disponível."""
        return self.lag_state == "available"

    @property
    def is_down(self) -> bool:
        """Verifica se está down."""
        return self.lag_state == "down"

    @property
    def meets_minimum_links(self) -> bool:
        """Verifica se atende mínimo de links."""
        return self.number_of_connections >= self.minimum_links

    @property
    def bandwidth_gbps(self) -> float:
        """Bandwidth total em Gbps."""
        bw = self.connections_bandwidth.lower()
        if "gbps" in bw:
            base = float(bw.replace("gbps", ""))
        elif "mbps" in bw:
            base = float(bw.replace("mbps", "")) / 1000
        else:
            base = 0.0
        return base * self.number_of_connections

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado."""
        bw = self.connections_bandwidth.lower()
        if "gbps" in bw:
            base_bw = float(bw.replace("gbps", ""))
        else:
            base_bw = 1.0
        
        rate = 0.22 if base_bw <= 5 else 1.50
        return rate * 24 * 30 * self.number_of_connections if self.is_available else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "lag_id": self.lag_id,
            "lag_name": self.lag_name,
            "lag_state": self.lag_state,
            "location": self.location,
            "region": self.region,
            "minimum_links": self.minimum_links,
            "number_of_connections": self.number_of_connections,
            "connections_bandwidth": self.connections_bandwidth,
            "bandwidth_gbps": self.bandwidth_gbps,
            "is_available": self.is_available,
            "meets_minimum_links": self.meets_minimum_links,
            "jumbo_frame_capable": self.jumbo_frame_capable,
            "mac_sec_capable": self.mac_sec_capable,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


class DirectConnectService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Direct Connect."""

    def __init__(self, client_factory):
        """Inicializa o serviço Direct Connect."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._dx_client = None

    @property
    def dx_client(self):
        """Cliente Direct Connect com lazy loading."""
        if self._dx_client is None:
            self._dx_client = self._client_factory.get_client('directconnect')
        return self._dx_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Direct Connect."""
        try:
            self.dx_client.describe_connections()
            return {
                "service": "directconnect",
                "status": "healthy",
                "message": "Direct Connect service is accessible"
            }
        except Exception as e:
            return {
                "service": "directconnect",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_connections(self) -> List[DirectConnectConnection]:
        """Lista conexões Direct Connect."""
        connections = []
        try:
            response = self.dx_client.describe_connections()
            for conn in response.get('connections', []):
                connections.append(DirectConnectConnection(
                    connection_id=conn.get('connectionId', ''),
                    connection_name=conn.get('connectionName', ''),
                    connection_state=conn.get('connectionState', 'available'),
                    region=conn.get('region', ''),
                    location=conn.get('location', ''),
                    bandwidth=conn.get('bandwidth', '1Gbps'),
                    vlan=conn.get('vlan', 0),
                    partner_name=conn.get('partnerName', ''),
                    loa_issue_time=conn.get('loaIssueTime'),
                    lag_id=conn.get('lagId'),
                    aws_device=conn.get('awsDevice', ''),
                    aws_device_v2=conn.get('awsDeviceV2', ''),
                    has_logical_redundancy=conn.get('hasLogicalRedundancy'),
                    jumbo_frame_capable=conn.get('jumboFrameCapable', False),
                    port_encryption_status=conn.get('portEncryptionStatus', ''),
                    encryption_mode=conn.get('encryptionMode', ''),
                    mac_sec_capable=conn.get('macSecCapable', False)
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar conexões: {e}")
        return connections

    def get_virtual_interfaces(self) -> List[VirtualInterface]:
        """Lista interfaces virtuais."""
        vifs = []
        try:
            response = self.dx_client.describe_virtual_interfaces()
            for vif in response.get('virtualInterfaces', []):
                vifs.append(VirtualInterface(
                    virtual_interface_id=vif.get('virtualInterfaceId', ''),
                    virtual_interface_name=vif.get('virtualInterfaceName', ''),
                    virtual_interface_type=vif.get('virtualInterfaceType', 'private'),
                    virtual_interface_state=vif.get('virtualInterfaceState', 'available'),
                    connection_id=vif.get('connectionId', ''),
                    vlan=vif.get('vlan', 0),
                    asn=vif.get('asn', 0),
                    amazon_side_asn=vif.get('amazonSideAsn', 0),
                    mtu=vif.get('mtu', 1500),
                    auth_key=vif.get('authKey', ''),
                    amazon_address=vif.get('amazonAddress', ''),
                    customer_address=vif.get('customerAddress', ''),
                    address_family=vif.get('addressFamily', 'ipv4'),
                    bgp_peers=vif.get('bgpPeers', []),
                    route_filter_prefixes=vif.get('routeFilterPrefixes', []),
                    direct_connect_gateway_id=vif.get('directConnectGatewayId'),
                    virtual_gateway_id=vif.get('virtualGatewayId'),
                    region=vif.get('region', ''),
                    aws_device_v2=vif.get('awsDeviceV2', ''),
                    jumbo_frame_capable=vif.get('jumboFrameCapable', False),
                    tags=vif.get('tags', [])
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar VIFs: {e}")
        return vifs

    def get_direct_connect_gateways(self) -> List[DirectConnectGateway]:
        """Lista Direct Connect Gateways."""
        gateways = []
        try:
            response = self.dx_client.describe_direct_connect_gateways()
            for gw in response.get('directConnectGateways', []):
                gateways.append(DirectConnectGateway(
                    direct_connect_gateway_id=gw.get('directConnectGatewayId', ''),
                    direct_connect_gateway_name=gw.get('directConnectGatewayName', ''),
                    amazon_side_asn=gw.get('amazonSideAsn', 0),
                    owner_account=gw.get('ownerAccount', ''),
                    direct_connect_gateway_state=gw.get('directConnectGatewayState', 'available'),
                    state_change_error=gw.get('stateChangeError', '')
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar DC Gateways: {e}")
        return gateways

    def get_lags(self) -> List[LinkAggregationGroup]:
        """Lista LAGs."""
        lags = []
        try:
            response = self.dx_client.describe_lags()
            for lag in response.get('lags', []):
                lags.append(LinkAggregationGroup(
                    lag_id=lag.get('lagId', ''),
                    lag_name=lag.get('lagName', ''),
                    lag_state=lag.get('lagState', 'available'),
                    location=lag.get('location', ''),
                    region=lag.get('region', ''),
                    minimum_links=lag.get('minimumLinks', 0),
                    number_of_connections=lag.get('numberOfConnections', 0),
                    allows_hosted_connections=lag.get('allowsHostedConnections', False),
                    connections_bandwidth=lag.get('connectionsBandwidth', ''),
                    owner_account=lag.get('ownerAccount', ''),
                    jumbo_frame_capable=lag.get('jumboFrameCapable', False),
                    encryption_mode=lag.get('encryptionMode', ''),
                    mac_sec_capable=lag.get('macSecCapable', False)
                ))
        except Exception as e:
            self.logger.error(f"Erro ao listar LAGs: {e}")
        return lags

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Direct Connect."""
        connections = self.get_connections()
        vifs = self.get_virtual_interfaces()
        gateways = self.get_direct_connect_gateways()
        lags = self.get_lags()

        total_cost = sum(c.estimated_monthly_cost for c in connections)
        total_cost += sum(l.estimated_monthly_cost for l in lags)

        return {
            "connections": [c.to_dict() for c in connections],
            "virtual_interfaces": [v.to_dict() for v in vifs],
            "direct_connect_gateways": [g.to_dict() for g in gateways],
            "lags": [l.to_dict() for l in lags],
            "summary": {
                "total_connections": len(connections),
                "available_connections": len([c for c in connections if c.is_available]),
                "down_connections": len([c for c in connections if c.is_down]),
                "total_vifs": len(vifs),
                "private_vifs": len([v for v in vifs if v.is_private]),
                "public_vifs": len([v for v in vifs if v.is_public]),
                "transit_vifs": len([v for v in vifs if v.is_transit]),
                "total_gateways": len(gateways),
                "available_gateways": len([g for g in gateways if g.is_available]),
                "total_lags": len(lags),
                "estimated_monthly_cost": total_cost
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Direct Connect."""
        connections = self.get_connections()
        vifs = self.get_virtual_interfaces()
        gateways = self.get_direct_connect_gateways()
        lags = self.get_lags()

        return {
            "connections_count": len(connections),
            "available_connections": len([c for c in connections if c.is_available]),
            "down_connections": len([c for c in connections if c.is_down]),
            "connections_with_encryption": len([c for c in connections if c.has_encryption]),
            "macsec_capable_connections": len([c for c in connections if c.supports_macsec]),
            "total_bandwidth_gbps": sum(c.bandwidth_gbps for c in connections),
            "vifs_count": len(vifs),
            "vif_types": {
                "private": len([v for v in vifs if v.is_private]),
                "public": len([v for v in vifs if v.is_public]),
                "transit": len([v for v in vifs if v.is_transit])
            },
            "gateways_count": len(gateways),
            "lags_count": len(lags),
            "total_lag_bandwidth_gbps": sum(l.bandwidth_gbps for l in lags),
            "estimated_monthly_cost": sum(c.estimated_monthly_cost for c in connections)
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Direct Connect."""
        recommendations = []
        connections = self.get_connections()
        vifs = self.get_virtual_interfaces()
        lags = self.get_lags()

        # Verificar conexões down
        down_connections = [c for c in connections if c.is_down]
        if down_connections:
            recommendations.append({
                "resource_type": "DirectConnectConnection",
                "resource_id": "multiple",
                "recommendation": "Investigar conexões down",
                "description": f"{len(down_connections)} conexão(ões) Direct Connect está(ão) down. "
                               "Verificar status e resolver problemas de conectividade.",
                "priority": "high"
            })

        # Verificar conexões sem criptografia
        no_encryption = [c for c in connections if c.is_available and c.supports_macsec and not c.has_encryption]
        if no_encryption:
            recommendations.append({
                "resource_type": "DirectConnectConnection",
                "resource_id": "multiple",
                "recommendation": "Habilitar MACsec para criptografia",
                "description": f"{len(no_encryption)} conexão(ões) suporta(m) MACsec mas não tem criptografia habilitada. "
                               "Considerar habilitar para maior segurança.",
                "priority": "medium"
            })

        # Verificar VIFs sem jumbo frames
        no_jumbo = [v for v in vifs if v.is_available and not v.uses_jumbo_mtu]
        if len(no_jumbo) > 5:
            recommendations.append({
                "resource_type": "VirtualInterface",
                "resource_id": "multiple",
                "recommendation": "Considerar jumbo frames",
                "description": f"{len(no_jumbo)} VIFs usando MTU padrão (1500). "
                               "Jumbo frames (MTU 9001) podem melhorar throughput.",
                "priority": "low"
            })

        # Verificar LAGs que não atendem mínimo de links
        failing_lags = [l for l in lags if not l.meets_minimum_links]
        if failing_lags:
            recommendations.append({
                "resource_type": "LinkAggregationGroup",
                "resource_id": "multiple",
                "recommendation": "LAGs abaixo do mínimo de links",
                "description": f"{len(failing_lags)} LAG(s) não atende(m) o mínimo de links configurado. "
                               "Verificar e adicionar conexões conforme necessário.",
                "priority": "high"
            })

        return recommendations
