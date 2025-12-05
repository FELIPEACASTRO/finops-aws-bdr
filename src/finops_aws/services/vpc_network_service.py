"""
VPC Network FinOps Service - Análise de Custos de Networking

FASE 2 - Prioridade 1: Networking (custos de transferência e NAT)
Autor: FinOps AWS Team
Data: Novembro 2025

Funcionalidades:
- Listagem de VPCs, NAT Gateways, VPN, Transit Gateway
- Análise de custos de transferência
- Recomendações de otimização de rede
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from .base_service import BaseAWSService, ServiceCost, ServiceMetrics, ServiceRecommendation



@dataclass
class VPC:
    """Representa uma VPC"""
    vpc_id: str
    cidr_block: str
    state: str
    is_default: bool
    instance_tenancy: str = "default"
    dhcp_options_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vpc_id': self.vpc_id,
            'cidr_block': self.cidr_block,
            'state': self.state,
            'is_default': self.is_default,
            'instance_tenancy': self.instance_tenancy,
            'name': self.tags.get('Name', '')
        }


@dataclass
class NATGateway:
    """Representa um NAT Gateway"""
    nat_gateway_id: str
    vpc_id: str
    subnet_id: str
    state: str
    connectivity_type: str  # public, private
    public_ip: Optional[str] = None
    private_ip: Optional[str] = None
    create_time: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nat_gateway_id': self.nat_gateway_id,
            'vpc_id': self.vpc_id,
            'subnet_id': self.subnet_id,
            'state': self.state,
            'connectivity_type': self.connectivity_type,
            'public_ip': self.public_ip,
            'name': self.tags.get('Name', ''),
            'create_time': self.create_time.isoformat() if self.create_time else None
        }


@dataclass
class TransitGateway:
    """Representa um Transit Gateway"""
    transit_gateway_id: str
    state: str
    owner_id: str
    description: str = ""
    amazon_side_asn: int = 0
    auto_accept_shared_attachments: str = "disable"
    default_route_table_association: str = "enable"
    default_route_table_propagation: str = "enable"
    vpn_ecmp_support: str = "enable"
    dns_support: str = "enable"
    multicast_support: str = "disable"
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'transit_gateway_id': self.transit_gateway_id,
            'state': self.state,
            'description': self.description,
            'auto_accept_shared_attachments': self.auto_accept_shared_attachments,
            'multicast_support': self.multicast_support,
            'name': self.tags.get('Name', '')
        }


@dataclass
class VPNConnection:
    """Representa uma conexão VPN"""
    vpn_connection_id: str
    state: str
    type: str
    vpn_gateway_id: Optional[str] = None
    transit_gateway_id: Optional[str] = None
    customer_gateway_id: Optional[str] = None
    category: str = "VPN"
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'vpn_connection_id': self.vpn_connection_id,
            'state': self.state,
            'type': self.type,
            'vpn_gateway_id': self.vpn_gateway_id,
            'transit_gateway_id': self.transit_gateway_id,
            'name': self.tags.get('Name', '')
        }


@dataclass
class ElasticIP:
    """Representa um Elastic IP"""
    allocation_id: str
    public_ip: str
    domain: str
    instance_id: Optional[str] = None
    association_id: Optional[str] = None
    network_interface_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'allocation_id': self.allocation_id,
            'public_ip': self.public_ip,
            'domain': self.domain,
            'instance_id': self.instance_id,
            'is_associated': self.association_id is not None,
            'name': self.tags.get('Name', '')
        }


class VPCNetworkService(BaseAWSService):
    """
    Serviço FinOps para análise de custos de Networking
    
    Analisa VPCs, NAT Gateways, VPN, Transit Gateway
    e fornece recomendações de otimização de custos.
    """
    
    def __init__(
        self,
        ec2_client=None,
        cloudwatch_client=None,
        cost_client=None
    ):
        super().__init__(cloudwatch_client, cost_client)
        self._ec2_client = ec2_client
    
    @property
    def ec2_client(self):
        if self._ec2_client is None:
            import boto3
            self._ec2_client = boto3.client('ec2')
        return self._ec2_client
    
    def get_service_name(self) -> str:
        return "Amazon VPC"
    
    def health_check(self) -> bool:
        try:
            self.ec2_client.describe_vpcs(MaxResults=5)
            return True
        except Exception as e:  # noqa: E722
            return False
    
    
    def get_vpcs(self) -> List[VPC]:
        """Lista todas as VPCs"""
        vpcs = []
        
        response = self.ec2_client.describe_vpcs()
        
        for vpc in response.get('Vpcs', []):
            tags = {t['Key']: t['Value'] for t in vpc.get('Tags', [])}
            
            v = VPC(
                vpc_id=vpc['VpcId'],
                cidr_block=vpc['CidrBlock'],
                state=vpc['State'],
                is_default=vpc.get('IsDefault', False),
                instance_tenancy=vpc.get('InstanceTenancy', 'default'),
                dhcp_options_id=vpc.get('DhcpOptionsId'),
                tags=tags
            )
            vpcs.append(v)
        
        return vpcs
    
    
    def get_nat_gateways(self) -> List[NATGateway]:
        """Lista todos os NAT Gateways"""
        nat_gateways = []
        
        paginator = self.ec2_client.get_paginator('describe_nat_gateways')
        
        for page in paginator.paginate():
            for nat in page.get('NatGateways', []):
                tags = {t['Key']: t['Value'] for t in nat.get('Tags', [])}
                
                addresses = nat.get('NatGatewayAddresses', [])
                public_ip = addresses[0].get('PublicIp') if addresses else None
                private_ip = addresses[0].get('PrivateIp') if addresses else None
                
                ng = NATGateway(
                    nat_gateway_id=nat['NatGatewayId'],
                    vpc_id=nat['VpcId'],
                    subnet_id=nat['SubnetId'],
                    state=nat['State'],
                    connectivity_type=nat.get('ConnectivityType', 'public'),
                    public_ip=public_ip,
                    private_ip=private_ip,
                    create_time=nat.get('CreateTime'),
                    tags=tags
                )
                nat_gateways.append(ng)
        
        return nat_gateways
    
    
    def get_transit_gateways(self) -> List[TransitGateway]:
        """Lista Transit Gateways"""
        tgws = []
        
        response = self.ec2_client.describe_transit_gateways()
        
        for tgw in response.get('TransitGateways', []):
            tags = {t['Key']: t['Value'] for t in tgw.get('Tags', [])}
            options = tgw.get('Options', {})
            
            t = TransitGateway(
                transit_gateway_id=tgw['TransitGatewayId'],
                state=tgw['State'],
                owner_id=tgw['OwnerId'],
                description=tgw.get('Description', ''),
                amazon_side_asn=options.get('AmazonSideAsn', 0),
                auto_accept_shared_attachments=options.get('AutoAcceptSharedAttachments', 'disable'),
                default_route_table_association=options.get('DefaultRouteTableAssociation', 'enable'),
                default_route_table_propagation=options.get('DefaultRouteTablePropagation', 'enable'),
                vpn_ecmp_support=options.get('VpnEcmpSupport', 'enable'),
                dns_support=options.get('DnsSupport', 'enable'),
                multicast_support=options.get('MulticastSupport', 'disable'),
                tags=tags
            )
            tgws.append(t)
        
        return tgws
    
    
    def get_vpn_connections(self) -> List[VPNConnection]:
        """Lista conexões VPN"""
        vpns = []
        
        response = self.ec2_client.describe_vpn_connections()
        
        for vpn in response.get('VpnConnections', []):
            tags = {t['Key']: t['Value'] for t in vpn.get('Tags', [])}
            
            v = VPNConnection(
                vpn_connection_id=vpn['VpnConnectionId'],
                state=vpn['State'],
                type=vpn['Type'],
                vpn_gateway_id=vpn.get('VpnGatewayId'),
                transit_gateway_id=vpn.get('TransitGatewayId'),
                customer_gateway_id=vpn.get('CustomerGatewayId'),
                category=vpn.get('Category', 'VPN'),
                tags=tags
            )
            vpns.append(v)
        
        return vpns
    
    
    def get_elastic_ips(self) -> List[ElasticIP]:
        """Lista Elastic IPs"""
        eips = []
        
        response = self.ec2_client.describe_addresses()
        
        for addr in response.get('Addresses', []):
            tags = {t['Key']: t['Value'] for t in addr.get('Tags', [])}
            
            eip = ElasticIP(
                allocation_id=addr.get('AllocationId', ''),
                public_ip=addr['PublicIp'],
                domain=addr['Domain'],
                instance_id=addr.get('InstanceId'),
                association_id=addr.get('AssociationId'),
                network_interface_id=addr.get('NetworkInterfaceId'),
                tags=tags
            )
            eips.append(eip)
        
        return eips
    
    
    def get_nat_gateway_metrics(self, nat_id: str, days: int = 7) -> Dict[str, Any]:
        """Obtém métricas de um NAT Gateway"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)
        
        metrics = {}
        
        bytes_out = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/NATGateway',
            MetricName='BytesOutToDestination',
            Dimensions=[{'Name': 'NatGatewayId', 'Value': nat_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if bytes_out.get('Datapoints'):
            metrics['bytes_out_gb'] = round(
                sum(d['Sum'] for d in bytes_out['Datapoints']) / (1024**3), 2
            )
        
        bytes_in = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/NATGateway',
            MetricName='BytesInFromDestination',
            Dimensions=[{'Name': 'NatGatewayId', 'Value': nat_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if bytes_in.get('Datapoints'):
            metrics['bytes_in_gb'] = round(
                sum(d['Sum'] for d in bytes_in['Datapoints']) / (1024**3), 2
            )
        
        packets = self.cloudwatch_client.get_metric_statistics(
            Namespace='AWS/NATGateway',
            MetricName='PacketsOutToDestination',
            Dimensions=[{'Name': 'NatGatewayId', 'Value': nat_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=['Sum']
        )
        if packets.get('Datapoints'):
            metrics['packets_out'] = int(sum(d['Sum'] for d in packets['Datapoints']))
        
        return metrics
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Implementação da interface BaseAWSService"""
        resources = []
        
        for vpc in self.get_vpcs():
            res = vpc.to_dict()
            res['resource_type'] = 'vpc'
            resources.append(res)
        
        for nat in self.get_nat_gateways():
            res = nat.to_dict()
            res['resource_type'] = 'nat_gateway'
            resources.append(res)
        
        for tgw in self.get_transit_gateways():
            res = tgw.to_dict()
            res['resource_type'] = 'transit_gateway'
            resources.append(res)
        
        for vpn in self.get_vpn_connections():
            res = vpn.to_dict()
            res['resource_type'] = 'vpn_connection'
            resources.append(res)
        
        for eip in self.get_elastic_ips():
            res = eip.to_dict()
            res['resource_type'] = 'elastic_ip'
            resources.append(res)
        
        return resources
    
    def get_metrics(self) -> ServiceMetrics:
        """Obtém métricas agregadas de VPC/Network"""
        vpcs = self.get_vpcs()
        nat_gateways = self.get_nat_gateways()
        transit_gateways = self.get_transit_gateways()
        vpn_connections = self.get_vpn_connections()
        elastic_ips = self.get_elastic_ips()
        
        unassociated_eips = len([e for e in elastic_ips if e.association_id is None])
        active_nats = len([n for n in nat_gateways if n.state == 'available'])
        
        return ServiceMetrics(
            service_name=self.get_service_name(),
            resource_count=len(vpcs) + len(nat_gateways) + len(transit_gateways) + len(vpn_connections) + len(elastic_ips),
            metrics={
                'vpcs': len(vpcs),
                'nat_gateways': len(nat_gateways),
                'active_nat_gateways': active_nats,
                'transit_gateways': len(transit_gateways),
                'vpn_connections': len(vpn_connections),
                'elastic_ips': len(elastic_ips),
                'unassociated_elastic_ips': unassociated_eips
            },
            period_days=7,
            collected_at=datetime.now(timezone.utc)
        )
    
    def get_recommendations(self) -> List[ServiceRecommendation]:
        """Gera recomendações de otimização para VPC/Network"""
        recommendations = []
        nat_gateways = self.get_nat_gateways()
        elastic_ips = self.get_elastic_ips()
        vpn_connections = self.get_vpn_connections()
        
        for eip in elastic_ips:
            if eip.association_id is None:
                recommendations.append(ServiceRecommendation(
                    resource_id=eip.allocation_id,
                    resource_type='Elastic IP',
                    recommendation_type='UNUSED_RESOURCE',
                    title='Elastic IP não associado',
                    description=f'Elastic IP {eip.public_ip} não está associado a nenhum recurso. '
                               f'EIPs não associados custam $0.005/hora (~$3.60/mês).',
                    estimated_savings=3.60,
                    priority='HIGH',
                    action='Associar ou liberar Elastic IP'
                ))
        
        for nat in nat_gateways:
            if nat.state != 'available':
                continue
            
            try:
                metrics = self.get_nat_gateway_metrics(nat.nat_gateway_id, days=30)
                
                total_traffic = metrics.get('bytes_out_gb', 0) + metrics.get('bytes_in_gb', 0)
                
                if total_traffic == 0:
                    recommendations.append(ServiceRecommendation(
                        resource_id=nat.nat_gateway_id,
                        resource_type='NAT Gateway',
                        recommendation_type='UNUSED_RESOURCE',
                        title='NAT Gateway sem tráfego',
                        description=f'NAT Gateway {nat.nat_gateway_id} não teve tráfego nos últimos 30 dias. '
                                   f'NAT Gateways custam ~$32/mês + taxas de processamento.',
                        estimated_savings=32.0,
                        priority='HIGH',
                        action='Remover NAT Gateway não utilizado'
                    ))
                elif total_traffic < 1:
                    recommendations.append(ServiceRecommendation(
                        resource_id=nat.nat_gateway_id,
                        resource_type='NAT Gateway',
                        recommendation_type='LOW_UTILIZATION',
                        title='NAT Gateway com baixa utilização',
                        description=f'NAT Gateway {nat.nat_gateway_id} processou apenas {total_traffic:.2f} GB. '
                                   f'Para tráfego baixo, considere NAT Instance.',
                        estimated_savings=20.0,
                        priority='MEDIUM',
                        action='Avaliar NAT Instance para baixo tráfego'
                    ))
                
                if metrics.get('bytes_out_gb', 0) > 100:
                    data_cost = metrics['bytes_out_gb'] * 0.045
                    recommendations.append(ServiceRecommendation(
                        resource_id=nat.nat_gateway_id,
                        resource_type='NAT Gateway',
                        recommendation_type='HIGH_DATA_TRANSFER',
                        title=f'Alto custo de transferência via NAT ({metrics["bytes_out_gb"]:.0f} GB)',
                        description=f'NAT Gateway {nat.nat_gateway_id} processou {metrics["bytes_out_gb"]:.0f} GB. '
                                   f'Custo estimado de dados: ${data_cost:.2f}. Considere VPC Endpoints.',
                        estimated_savings=data_cost * 0.5,
                        priority='HIGH',
                        action='Implementar VPC Endpoints para S3/DynamoDB'
                    ))
                
            except Exception as e:  # noqa: E722
                pass
        
        for vpn in vpn_connections:
            if vpn.state == 'deleted':
                continue
            
            if vpn.state != 'available':
                recommendations.append(ServiceRecommendation(
                    resource_id=vpn.vpn_connection_id,
                    resource_type='VPN Connection',
                    recommendation_type='UNHEALTHY_RESOURCE',
                    title=f'VPN em estado anormal: {vpn.state}',
                    description=f'VPN Connection {vpn.vpn_connection_id} está em estado {vpn.state}. '
                               f'VPNs custam $0.05/hora (~$36/mês) mesmo sem tráfego.',
                    estimated_savings=36.0,
                    priority='HIGH',
                    action='Investigar ou remover VPN'
                ))
        
        return recommendations
