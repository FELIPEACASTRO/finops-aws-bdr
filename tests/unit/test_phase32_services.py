"""
Testes Unitários - FASE 3.2: Networking Advanced Services

Cobertura de testes para:
- GlobalAcceleratorService: Aceleradores, listeners, endpoint groups
- DirectConnectService: Conexões, VIFs, Gateways, LAGs
- TransitGatewayService: TGWs, attachments, route tables, peerings
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from src.finops_aws.services.globalaccelerator_service import (
    GlobalAcceleratorService,
    GlobalAccelerator,
    AcceleratorListener,
    EndpointGroup
)
from src.finops_aws.services.directconnect_service import (
    DirectConnectService,
    DirectConnectConnection,
    VirtualInterface,
    DirectConnectGateway,
    LinkAggregationGroup
)
from src.finops_aws.services.transitgateway_service import (
    TransitGatewayService,
    TransitGateway,
    TransitGatewayAttachment,
    TransitGatewayRouteTable,
    TransitGatewayPeeringAttachment
)
from src.finops_aws.core.factories import ServiceFactory


class TestGlobalAcceleratorDataclass:
    """Testes para dataclass GlobalAccelerator."""
    
    def test_accelerator_basic(self):
        """Testa criação básica de GlobalAccelerator."""
        acc = GlobalAccelerator(accelerator_arn="arn:aws:globalaccelerator::123:accelerator/abc")
        assert acc.is_enabled is True
        assert acc.is_deployed is True
    
    def test_accelerator_disabled(self):
        """Testa acelerador desabilitado."""
        acc = GlobalAccelerator(accelerator_arn="arn", enabled=False)
        assert acc.is_enabled is False
    
    def test_accelerator_in_progress(self):
        """Testa acelerador em progresso."""
        acc = GlobalAccelerator(accelerator_arn="arn", status="IN_PROGRESS")
        assert acc.is_in_progress is True
        assert acc.is_deployed is False
    
    def test_accelerator_dual_stack(self):
        """Testa suporte IPv6."""
        acc = GlobalAccelerator(accelerator_arn="arn", ip_address_type="DUAL_STACK")
        assert acc.supports_ipv6 is True
    
    def test_accelerator_static_ips(self):
        """Testa contagem de IPs estáticos."""
        acc = GlobalAccelerator(
            accelerator_arn="arn",
            ip_sets=[{"IpAddresses": ["1.2.3.4", "5.6.7.8"]}]
        )
        assert acc.static_ip_count == 2
    
    def test_accelerator_cost(self):
        """Testa custo estimado."""
        acc = GlobalAccelerator(accelerator_arn="arn", enabled=True)
        assert acc.estimated_monthly_cost > 0
    
    def test_accelerator_to_dict(self):
        """Testa conversão para dicionário."""
        acc = GlobalAccelerator(accelerator_arn="arn", name="test")
        data = acc.to_dict()
        assert "is_enabled" in data
        assert "estimated_monthly_cost" in data


class TestAcceleratorListenerDataclass:
    """Testes para dataclass AcceleratorListener."""
    
    def test_listener_basic(self):
        """Testa criação básica de AcceleratorListener."""
        listener = AcceleratorListener(listener_arn="arn")
        assert listener.is_tcp is True
    
    def test_listener_udp(self):
        """Testa listener UDP."""
        listener = AcceleratorListener(listener_arn="arn", protocol="UDP")
        assert listener.is_udp is True
        assert listener.is_tcp is False
    
    def test_listener_client_affinity(self):
        """Testa client affinity."""
        listener = AcceleratorListener(listener_arn="arn", client_affinity="SOURCE_IP")
        assert listener.has_client_affinity is True
    
    def test_listener_port_count(self):
        """Testa contagem de portas."""
        listener = AcceleratorListener(
            listener_arn="arn",
            port_ranges=[{"FromPort": 80, "ToPort": 80}, {"FromPort": 443, "ToPort": 443}]
        )
        assert listener.port_count == 2
    
    def test_listener_to_dict(self):
        """Testa conversão para dicionário."""
        listener = AcceleratorListener(listener_arn="arn")
        data = listener.to_dict()
        assert "is_tcp" in data
        assert "port_count" in data


class TestEndpointGroupDataclass:
    """Testes para dataclass EndpointGroup."""
    
    def test_endpoint_group_basic(self):
        """Testa criação básica de EndpointGroup."""
        eg = EndpointGroup(endpoint_group_arn="arn", endpoint_group_region="us-east-1")
        assert eg.is_fully_utilized is True
    
    def test_endpoint_group_disabled(self):
        """Testa endpoint group desabilitado."""
        eg = EndpointGroup(endpoint_group_arn="arn", traffic_dial_percentage=0.0)
        assert eg.is_disabled is True
    
    def test_endpoint_group_endpoints(self):
        """Testa contagem de endpoints."""
        eg = EndpointGroup(
            endpoint_group_arn="arn",
            endpoint_descriptions=[
                {"EndpointId": "i-123", "HealthState": "HEALTHY"},
                {"EndpointId": "i-456", "HealthState": "UNHEALTHY"}
            ]
        )
        assert eg.endpoint_count == 2
        assert eg.healthy_endpoints == 1
    
    def test_endpoint_group_to_dict(self):
        """Testa conversão para dicionário."""
        eg = EndpointGroup(endpoint_group_arn="arn")
        data = eg.to_dict()
        assert "is_fully_utilized" in data
        assert "endpoint_count" in data


class TestGlobalAcceleratorService:
    """Testes para GlobalAcceleratorService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        ga_client = Mock()
        factory.get_client.return_value = ga_client
        return factory
    
    def test_ga_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = GlobalAcceleratorService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_ga_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.list_accelerators.return_value = {
            'Accelerators': []
        }
        service = GlobalAcceleratorService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_ga_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Accelerators': []}]
        client.get_paginator.return_value = paginator
        
        service = GlobalAcceleratorService(mock_client_factory)
        resources = service.get_resources()
        assert "accelerators" in resources
        assert "listeners" in resources
        assert "summary" in resources
    
    def test_ga_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Accelerators': []}]
        client.get_paginator.return_value = paginator
        
        service = GlobalAcceleratorService(mock_client_factory)
        metrics = service.get_metrics()
        assert "accelerators_count" in metrics
        assert "estimated_monthly_cost" in metrics
    
    def test_ga_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'Accelerators': []}]
        client.get_paginator.return_value = paginator
        
        service = GlobalAcceleratorService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestDirectConnectConnectionDataclass:
    """Testes para dataclass DirectConnectConnection."""
    
    def test_connection_basic(self):
        """Testa criação básica de DirectConnectConnection."""
        conn = DirectConnectConnection(connection_id="dxcon-123")
        assert conn.is_available is True
    
    def test_connection_down(self):
        """Testa conexão down."""
        conn = DirectConnectConnection(connection_id="dxcon-123", connection_state="down")
        assert conn.is_down is True
        assert conn.is_available is False
    
    def test_connection_pending(self):
        """Testa conexão pending."""
        conn = DirectConnectConnection(connection_id="dxcon-123", connection_state="pending")
        assert conn.is_pending is True
    
    def test_connection_bandwidth(self):
        """Testa conversão de bandwidth."""
        conn_1g = DirectConnectConnection(connection_id="test", bandwidth="1Gbps")
        conn_10g = DirectConnectConnection(connection_id="test", bandwidth="10Gbps")
        conn_500m = DirectConnectConnection(connection_id="test", bandwidth="500Mbps")
        
        assert conn_1g.bandwidth_gbps == 1.0
        assert conn_10g.bandwidth_gbps == 10.0
        assert conn_500m.bandwidth_gbps == 0.5
    
    def test_connection_lag_member(self):
        """Testa membro de LAG."""
        conn = DirectConnectConnection(connection_id="test", lag_id="dxlag-123")
        assert conn.is_lag_member is True
    
    def test_connection_features(self):
        """Testa features."""
        conn = DirectConnectConnection(
            connection_id="test",
            jumbo_frame_capable=True,
            mac_sec_capable=True,
            port_encryption_status="enabled"
        )
        assert conn.supports_jumbo_frames is True
        assert conn.supports_macsec is True
        assert conn.has_encryption is True
    
    def test_connection_cost(self):
        """Testa custo estimado."""
        conn = DirectConnectConnection(connection_id="test", bandwidth="1Gbps")
        assert conn.estimated_monthly_cost > 0
    
    def test_connection_to_dict(self):
        """Testa conversão para dicionário."""
        conn = DirectConnectConnection(connection_id="test")
        data = conn.to_dict()
        assert "is_available" in data
        assert "bandwidth_gbps" in data


class TestVirtualInterfaceDataclass:
    """Testes para dataclass VirtualInterface."""
    
    def test_vif_basic(self):
        """Testa criação básica de VirtualInterface."""
        vif = VirtualInterface(virtual_interface_id="dxvif-123")
        assert vif.is_available is True
        assert vif.is_private is True
    
    def test_vif_types(self):
        """Testa diferentes tipos de VIF."""
        private = VirtualInterface(virtual_interface_id="test", virtual_interface_type="private")
        public = VirtualInterface(virtual_interface_id="test", virtual_interface_type="public")
        transit = VirtualInterface(virtual_interface_id="test", virtual_interface_type="transit")
        
        assert private.is_private is True
        assert public.is_public is True
        assert transit.is_transit is True
    
    def test_vif_ipv6(self):
        """Testa suporte IPv6."""
        vif = VirtualInterface(virtual_interface_id="test", address_family="ipv6")
        assert vif.supports_ipv6 is True
    
    def test_vif_jumbo_mtu(self):
        """Testa jumbo MTU."""
        vif = VirtualInterface(virtual_interface_id="test", mtu=9001)
        assert vif.uses_jumbo_mtu is True
    
    def test_vif_dcgw(self):
        """Testa conexão com DC Gateway."""
        vif = VirtualInterface(
            virtual_interface_id="test",
            direct_connect_gateway_id="dcgw-123"
        )
        assert vif.has_dcgw is True
    
    def test_vif_bgp_peers(self):
        """Testa contagem de BGP peers."""
        vif = VirtualInterface(
            virtual_interface_id="test",
            bgp_peers=[{"bgpPeerId": "1"}, {"bgpPeerId": "2"}]
        )
        assert vif.bgp_peers_count == 2
    
    def test_vif_to_dict(self):
        """Testa conversão para dicionário."""
        vif = VirtualInterface(virtual_interface_id="test")
        data = vif.to_dict()
        assert "is_private" in data
        assert "uses_jumbo_mtu" in data


class TestDirectConnectGatewayDataclass:
    """Testes para dataclass DirectConnectGateway."""
    
    def test_dcgw_basic(self):
        """Testa criação básica de DirectConnectGateway."""
        gw = DirectConnectGateway(direct_connect_gateway_id="dcgw-123")
        assert gw.is_available is True
    
    def test_dcgw_pending(self):
        """Testa gateway pending."""
        gw = DirectConnectGateway(
            direct_connect_gateway_id="test",
            direct_connect_gateway_state="pending"
        )
        assert gw.is_pending is True
    
    def test_dcgw_deleting(self):
        """Testa gateway being deleted."""
        gw = DirectConnectGateway(
            direct_connect_gateway_id="test",
            direct_connect_gateway_state="deleting"
        )
        assert gw.is_deleting is True
    
    def test_dcgw_error(self):
        """Testa gateway com erro."""
        gw = DirectConnectGateway(
            direct_connect_gateway_id="test",
            state_change_error="Some error"
        )
        assert gw.has_error is True
    
    def test_dcgw_to_dict(self):
        """Testa conversão para dicionário."""
        gw = DirectConnectGateway(direct_connect_gateway_id="test")
        data = gw.to_dict()
        assert "is_available" in data
        assert "has_error" in data


class TestLinkAggregationGroupDataclass:
    """Testes para dataclass LinkAggregationGroup."""
    
    def test_lag_basic(self):
        """Testa criação básica de LinkAggregationGroup."""
        lag = LinkAggregationGroup(lag_id="dxlag-123")
        assert lag.is_available is True
    
    def test_lag_down(self):
        """Testa LAG down."""
        lag = LinkAggregationGroup(lag_id="test", lag_state="down")
        assert lag.is_down is True
    
    def test_lag_minimum_links(self):
        """Testa verificação de mínimo de links."""
        lag_ok = LinkAggregationGroup(
            lag_id="test",
            minimum_links=2,
            number_of_connections=3
        )
        lag_fail = LinkAggregationGroup(
            lag_id="test",
            minimum_links=2,
            number_of_connections=1
        )
        assert lag_ok.meets_minimum_links is True
        assert lag_fail.meets_minimum_links is False
    
    def test_lag_bandwidth(self):
        """Testa cálculo de bandwidth."""
        lag = LinkAggregationGroup(
            lag_id="test",
            connections_bandwidth="1Gbps",
            number_of_connections=4
        )
        assert lag.bandwidth_gbps == 4.0
    
    def test_lag_cost(self):
        """Testa custo estimado."""
        lag = LinkAggregationGroup(
            lag_id="test",
            connections_bandwidth="1Gbps",
            number_of_connections=2
        )
        assert lag.estimated_monthly_cost > 0
    
    def test_lag_to_dict(self):
        """Testa conversão para dicionário."""
        lag = LinkAggregationGroup(lag_id="test")
        data = lag.to_dict()
        assert "is_available" in data
        assert "bandwidth_gbps" in data


class TestDirectConnectService:
    """Testes para DirectConnectService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        dx_client = Mock()
        factory.get_client.return_value = dx_client
        return factory
    
    def test_dx_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = DirectConnectService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_dx_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.describe_connections.return_value = {
            'connections': []
        }
        service = DirectConnectService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_dx_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        client.describe_connections.return_value = {'connections': []}
        client.describe_virtual_interfaces.return_value = {'virtualInterfaces': []}
        client.describe_direct_connect_gateways.return_value = {'directConnectGateways': []}
        client.describe_lags.return_value = {'lags': []}
        
        service = DirectConnectService(mock_client_factory)
        resources = service.get_resources()
        assert "connections" in resources
        assert "virtual_interfaces" in resources
        assert "direct_connect_gateways" in resources
        assert "lags" in resources
        assert "summary" in resources
    
    def test_dx_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        client.describe_connections.return_value = {'connections': []}
        client.describe_virtual_interfaces.return_value = {'virtualInterfaces': []}
        client.describe_direct_connect_gateways.return_value = {'directConnectGateways': []}
        client.describe_lags.return_value = {'lags': []}
        
        service = DirectConnectService(mock_client_factory)
        metrics = service.get_metrics()
        assert "connections_count" in metrics
        assert "vif_types" in metrics
    
    def test_dx_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        client.describe_connections.return_value = {'connections': []}
        client.describe_virtual_interfaces.return_value = {'virtualInterfaces': []}
        client.describe_direct_connect_gateways.return_value = {'directConnectGateways': []}
        client.describe_lags.return_value = {'lags': []}
        
        service = DirectConnectService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestTransitGatewayDataclass:
    """Testes para dataclass TransitGateway."""
    
    def test_tgw_basic(self):
        """Testa criação básica de TransitGateway."""
        tgw = TransitGateway(transit_gateway_id="tgw-123")
        assert tgw.is_available is True
    
    def test_tgw_pending(self):
        """Testa TGW pending."""
        tgw = TransitGateway(transit_gateway_id="test", state="pending")
        assert tgw.is_pending is True
    
    def test_tgw_deleting(self):
        """Testa TGW being deleted."""
        tgw = TransitGateway(transit_gateway_id="test", state="deleting")
        assert tgw.is_deleting is True
    
    def test_tgw_options(self):
        """Testa opções do TGW."""
        tgw = TransitGateway(
            transit_gateway_id="test",
            options={
                "AmazonSideAsn": 64512,
                "AutoAcceptSharedAttachments": "enable",
                "DnsSupport": "enable",
                "VpnEcmpSupport": "enable",
                "MulticastSupport": "enable"
            }
        )
        assert tgw.amazon_side_asn == 64512
        assert tgw.auto_accept_shared_attachments is True
        assert tgw.dns_support is True
        assert tgw.vpn_ecmp_support is True
        assert tgw.multicast_support is True
    
    def test_tgw_cost(self):
        """Testa custo estimado."""
        tgw = TransitGateway(transit_gateway_id="test")
        assert tgw.estimated_hourly_cost == 0.05
        assert tgw.estimated_monthly_cost == 0.05 * 24 * 30
    
    def test_tgw_to_dict(self):
        """Testa conversão para dicionário."""
        tgw = TransitGateway(transit_gateway_id="test")
        data = tgw.to_dict()
        assert "is_available" in data
        assert "estimated_monthly_cost" in data


class TestTransitGatewayAttachmentDataclass:
    """Testes para dataclass TransitGatewayAttachment."""
    
    def test_attachment_basic(self):
        """Testa criação básica de TransitGatewayAttachment."""
        att = TransitGatewayAttachment(transit_gateway_attachment_id="tgw-attach-123")
        assert att.is_available is True
    
    def test_attachment_pending(self):
        """Testa attachment pending."""
        att = TransitGatewayAttachment(
            transit_gateway_attachment_id="test",
            state="pendingAcceptance"
        )
        assert att.is_pending is True
    
    def test_attachment_types(self):
        """Testa diferentes tipos de attachment."""
        vpc = TransitGatewayAttachment(
            transit_gateway_attachment_id="test",
            resource_type="vpc"
        )
        vpn = TransitGatewayAttachment(
            transit_gateway_attachment_id="test",
            resource_type="vpn"
        )
        dx = TransitGatewayAttachment(
            transit_gateway_attachment_id="test",
            resource_type="direct-connect-gateway"
        )
        peering = TransitGatewayAttachment(
            transit_gateway_attachment_id="test",
            resource_type="peering"
        )
        connect = TransitGatewayAttachment(
            transit_gateway_attachment_id="test",
            resource_type="connect"
        )
        
        assert vpc.is_vpc is True
        assert vpn.is_vpn is True
        assert dx.is_direct_connect is True
        assert peering.is_peering is True
        assert connect.is_tgw_connect is True
    
    def test_attachment_association(self):
        """Testa associação."""
        att = TransitGatewayAttachment(
            transit_gateway_attachment_id="test",
            association={"TransitGatewayRouteTableId": "tgw-rtb-123"}
        )
        assert att.has_association is True
        assert att.route_table_id == "tgw-rtb-123"
    
    def test_attachment_cost(self):
        """Testa custo estimado."""
        att = TransitGatewayAttachment(transit_gateway_attachment_id="test")
        assert att.estimated_hourly_cost == 0.05
    
    def test_attachment_to_dict(self):
        """Testa conversão para dicionário."""
        att = TransitGatewayAttachment(transit_gateway_attachment_id="test")
        data = att.to_dict()
        assert "is_vpc" in data
        assert "estimated_monthly_cost" in data


class TestTransitGatewayRouteTableDataclass:
    """Testes para dataclass TransitGatewayRouteTable."""
    
    def test_route_table_basic(self):
        """Testa criação básica de TransitGatewayRouteTable."""
        rt = TransitGatewayRouteTable(transit_gateway_route_table_id="tgw-rtb-123")
        assert rt.is_available is True
    
    def test_route_table_defaults(self):
        """Testa route table default."""
        rt = TransitGatewayRouteTable(
            transit_gateway_route_table_id="test",
            default_association_route_table=True,
            default_propagation_route_table=True
        )
        assert rt.is_default_association is True
        assert rt.is_default_propagation is True
    
    def test_route_table_to_dict(self):
        """Testa conversão para dicionário."""
        rt = TransitGatewayRouteTable(transit_gateway_route_table_id="test")
        data = rt.to_dict()
        assert "is_available" in data
        assert "is_default_association" in data


class TestTransitGatewayPeeringAttachmentDataclass:
    """Testes para dataclass TransitGatewayPeeringAttachment."""
    
    def test_peering_basic(self):
        """Testa criação básica de TransitGatewayPeeringAttachment."""
        peer = TransitGatewayPeeringAttachment(transit_gateway_attachment_id="tgw-attach-123")
        assert peer.is_available is True
    
    def test_peering_pending(self):
        """Testa peering pending."""
        peer = TransitGatewayPeeringAttachment(
            transit_gateway_attachment_id="test",
            state="pendingAcceptance"
        )
        assert peer.is_pending_acceptance is True
    
    def test_peering_cross_region(self):
        """Testa peering cross-region."""
        peer = TransitGatewayPeeringAttachment(
            transit_gateway_attachment_id="test",
            requester_tgw_info={"TransitGatewayId": "tgw-1", "Region": "us-east-1"},
            accepter_tgw_info={"TransitGatewayId": "tgw-2", "Region": "eu-west-1"}
        )
        assert peer.is_cross_region is True
    
    def test_peering_same_region(self):
        """Testa peering same region."""
        peer = TransitGatewayPeeringAttachment(
            transit_gateway_attachment_id="test",
            requester_tgw_info={"TransitGatewayId": "tgw-1", "Region": "us-east-1"},
            accepter_tgw_info={"TransitGatewayId": "tgw-2", "Region": "us-east-1"}
        )
        assert peer.is_cross_region is False
    
    def test_peering_to_dict(self):
        """Testa conversão para dicionário."""
        peer = TransitGatewayPeeringAttachment(transit_gateway_attachment_id="test")
        data = peer.to_dict()
        assert "is_available" in data
        assert "is_cross_region" in data


class TestTransitGatewayService:
    """Testes para TransitGatewayService."""
    
    @pytest.fixture
    def mock_client_factory(self):
        """Cria mock do client factory."""
        factory = Mock()
        ec2_client = Mock()
        factory.get_client.return_value = ec2_client
        return factory
    
    def test_tgw_service_init(self, mock_client_factory):
        """Testa inicialização do serviço."""
        service = TransitGatewayService(mock_client_factory)
        assert service._client_factory == mock_client_factory
    
    def test_tgw_service_health_check_healthy(self, mock_client_factory):
        """Testa health check saudável."""
        mock_client_factory.get_client.return_value.describe_transit_gateways.return_value = {
            'TransitGateways': []
        }
        service = TransitGatewayService(mock_client_factory)
        result = service.health_check()
        assert result["status"] == "healthy"
    
    def test_tgw_service_get_resources(self, mock_client_factory):
        """Testa get_resources."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'TransitGateways': []}]
        client.get_paginator.return_value = paginator
        
        service = TransitGatewayService(mock_client_factory)
        resources = service.get_resources()
        assert "transit_gateways" in resources
        assert "attachments" in resources
        assert "route_tables" in resources
        assert "summary" in resources
    
    def test_tgw_service_get_metrics(self, mock_client_factory):
        """Testa get_metrics."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'TransitGateways': []}]
        client.get_paginator.return_value = paginator
        
        service = TransitGatewayService(mock_client_factory)
        metrics = service.get_metrics()
        assert "transit_gateways_count" in metrics
        assert "attachment_types" in metrics
    
    def test_tgw_service_get_recommendations(self, mock_client_factory):
        """Testa get_recommendations."""
        client = mock_client_factory.get_client.return_value
        paginator = Mock()
        paginator.paginate.return_value = [{'TransitGateways': []}]
        client.get_paginator.return_value = paginator
        
        service = TransitGatewayService(mock_client_factory)
        recommendations = service.get_recommendations()
        assert isinstance(recommendations, list)


class TestServiceFactoryIntegration:
    """Testes de integração com ServiceFactory."""
    
    def test_service_factory_get_globalaccelerator_service(self):
        """Testa obtenção do GlobalAcceleratorService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_ga = Mock()
        factory.register_mock('globalaccelerator', mock_ga)
        
        service = factory.get_globalaccelerator_service()
        assert service == mock_ga
    
    def test_service_factory_get_directconnect_service(self):
        """Testa obtenção do DirectConnectService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_dx = Mock()
        factory.register_mock('directconnect', mock_dx)
        
        service = factory.get_directconnect_service()
        assert service == mock_dx
    
    def test_service_factory_get_transitgateway_service(self):
        """Testa obtenção do TransitGatewayService via factory."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        mock_tgw = Mock()
        factory.register_mock('transitgateway', mock_tgw)
        
        service = factory.get_transitgateway_service()
        assert service == mock_tgw
    
    def test_service_factory_get_all_services_includes_networking(self):
        """Testa que get_all_services inclui serviços Networking Advanced."""
        ServiceFactory.reset_instance()
        factory = ServiceFactory()
        
        factory.register_mock('globalaccelerator', Mock())
        factory.register_mock('directconnect', Mock())
        factory.register_mock('transitgateway', Mock())
        factory.register_mock('cost', Mock())
        factory.register_mock('metrics', Mock())
        factory.register_mock('optimizer', Mock())
        
        all_services = factory.get_all_services()
        assert 'globalaccelerator' in all_services
        assert 'directconnect' in all_services
        assert 'transitgateway' in all_services
