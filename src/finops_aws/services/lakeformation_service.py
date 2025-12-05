"""
AWS Lake Formation Service para FinOps.

Análise de custos e otimização de data lake governance.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class LakeFormationDatabase:
    """Database gerenciado pelo Lake Formation."""
    name: str
    catalog_id: str = ""
    description: str = ""
    location_uri: str = ""
    parameters: Dict[str, str] = field(default_factory=dict)
    create_time: Optional[datetime] = None
    create_table_default_permissions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def has_location(self) -> bool:
        """Verifica se tem localização definida."""
        return bool(self.location_uri)

    @property
    def has_default_permissions(self) -> bool:
        """Verifica se tem permissões padrão."""
        return len(self.create_table_default_permissions) > 0

    @property
    def is_s3_location(self) -> bool:
        """Verifica se localização é S3."""
        return self.location_uri.startswith('s3://')

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "catalog_id": self.catalog_id,
            "description": self.description,
            "location_uri": self.location_uri,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "has_location": self.has_location,
            "has_default_permissions": self.has_default_permissions,
            "is_s3_location": self.is_s3_location
        }


@dataclass
class LakeFormationTable:
    """Tabela gerenciada pelo Lake Formation."""
    name: str
    database_name: str
    catalog_id: str = ""
    table_type: str = "EXTERNAL_TABLE"
    owner: str = ""
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    last_access_time: Optional[datetime] = None
    storage_descriptor: Dict[str, Any] = field(default_factory=dict)
    partition_keys: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, str] = field(default_factory=dict)

    @property
    def is_external(self) -> bool:
        """Verifica se é tabela externa."""
        return self.table_type == "EXTERNAL_TABLE"

    @property
    def is_governed(self) -> bool:
        """Verifica se é tabela governada."""
        return self.table_type == "GOVERNED"

    @property
    def has_partitions(self) -> bool:
        """Verifica se tem partições."""
        return len(self.partition_keys) > 0

    @property
    def partition_count(self) -> int:
        """Número de chaves de partição."""
        return len(self.partition_keys)

    @property
    def columns_count(self) -> int:
        """Número de colunas."""
        return len(self.storage_descriptor.get('Columns', []))

    @property
    def location(self) -> str:
        """Localização dos dados."""
        return self.storage_descriptor.get('Location', '')

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "name": self.name,
            "database_name": self.database_name,
            "catalog_id": self.catalog_id,
            "table_type": self.table_type,
            "owner": self.owner,
            "create_time": self.create_time.isoformat() if self.create_time else None,
            "update_time": self.update_time.isoformat() if self.update_time else None,
            "is_external": self.is_external,
            "is_governed": self.is_governed,
            "has_partitions": self.has_partitions,
            "partition_count": self.partition_count,
            "columns_count": self.columns_count,
            "location": self.location
        }


@dataclass
class LakeFormationPermission:
    """Permissão do Lake Formation."""
    principal: Dict[str, Any] = field(default_factory=dict)
    resource: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    permissions_with_grant_option: List[str] = field(default_factory=list)

    @property
    def principal_type(self) -> str:
        """Tipo do principal."""
        if 'DataLakePrincipalIdentifier' in self.principal:
            identifier = self.principal['DataLakePrincipalIdentifier']
            if identifier.startswith('arn:aws:iam'):
                if ':role/' in identifier:
                    return "IAM_ROLE"
                elif ':user/' in identifier:
                    return "IAM_USER"
            return "OTHER"
        return "UNKNOWN"

    @property
    def resource_type(self) -> str:
        """Tipo do recurso."""
        if 'Database' in self.resource:
            return "DATABASE"
        elif 'Table' in self.resource:
            return "TABLE"
        elif 'DataLocation' in self.resource:
            return "DATA_LOCATION"
        elif 'LFTag' in self.resource:
            return "LF_TAG"
        return "UNKNOWN"

    @property
    def has_grant_option(self) -> bool:
        """Verifica se tem opção de grant."""
        return len(self.permissions_with_grant_option) > 0

    @property
    def is_full_access(self) -> bool:
        """Verifica se tem acesso completo."""
        return "ALL" in self.permissions

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "principal": self.principal,
            "resource": self.resource,
            "permissions": self.permissions,
            "permissions_with_grant_option": self.permissions_with_grant_option,
            "principal_type": self.principal_type,
            "resource_type": self.resource_type,
            "has_grant_option": self.has_grant_option,
            "is_full_access": self.is_full_access
        }


@dataclass
class LFTag:
    """Tag do Lake Formation."""
    tag_key: str
    tag_values: List[str] = field(default_factory=list)
    catalog_id: str = ""

    @property
    def values_count(self) -> int:
        """Número de valores."""
        return len(self.tag_values)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "tag_key": self.tag_key,
            "tag_values": self.tag_values,
            "catalog_id": self.catalog_id,
            "values_count": self.values_count
        }


@dataclass
class DataLakeSettings:
    """Configurações do Data Lake."""
    data_lake_admins: List[Dict[str, Any]] = field(default_factory=list)
    create_database_default_permissions: List[Dict[str, Any]] = field(default_factory=list)
    create_table_default_permissions: List[Dict[str, Any]] = field(default_factory=list)
    trusted_resource_owners: List[str] = field(default_factory=list)
    allow_external_data_filtering: bool = False
    external_data_filtering_allow_list: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def admins_count(self) -> int:
        """Número de administradores."""
        return len(self.data_lake_admins)

    @property
    def has_default_db_permissions(self) -> bool:
        """Verifica se tem permissões padrão para database."""
        return len(self.create_database_default_permissions) > 0

    @property
    def has_default_table_permissions(self) -> bool:
        """Verifica se tem permissões padrão para tabela."""
        return len(self.create_table_default_permissions) > 0

    @property
    def allows_external_filtering(self) -> bool:
        """Verifica se permite filtragem externa."""
        return self.allow_external_data_filtering

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "data_lake_admins": self.data_lake_admins,
            "create_database_default_permissions": self.create_database_default_permissions,
            "create_table_default_permissions": self.create_table_default_permissions,
            "trusted_resource_owners": self.trusted_resource_owners,
            "allow_external_data_filtering": self.allow_external_data_filtering,
            "admins_count": self.admins_count,
            "has_default_db_permissions": self.has_default_db_permissions,
            "has_default_table_permissions": self.has_default_table_permissions,
            "allows_external_filtering": self.allows_external_filtering
        }


class LakeFormationService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS Lake Formation."""

    def __init__(self, client_factory):
        """Inicializa o serviço Lake Formation."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._lakeformation_client = None
        self._glue_client = None

    @property
    def lakeformation_client(self):
        """Cliente Lake Formation com lazy loading."""
        if self._lakeformation_client is None:
            self._lakeformation_client = self._client_factory.get_client('lakeformation')
        return self._lakeformation_client

    @property
    def glue_client(self):
        """Cliente Glue com lazy loading."""
        if self._glue_client is None:
            self._glue_client = self._client_factory.get_client('glue')
        return self._glue_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço Lake Formation."""
        try:
            self.lakeformation_client.get_data_lake_settings()
            return {
                "service": "lakeformation",
                "status": "healthy",
                "message": "Lake Formation service is accessible"
            }
        except Exception as e:
            return {
                "service": "lakeformation",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_data_lake_settings(self) -> Optional[DataLakeSettings]:
        """Obtém configurações do data lake."""
        try:
            response = self.lakeformation_client.get_data_lake_settings()
            settings = response.get('DataLakeSettings', {})
            return DataLakeSettings(
                data_lake_admins=settings.get('DataLakeAdmins', []),
                create_database_default_permissions=settings.get('CreateDatabaseDefaultPermissions', []),
                create_table_default_permissions=settings.get('CreateTableDefaultPermissions', []),
                trusted_resource_owners=settings.get('TrustedResourceOwners', []),
                allow_external_data_filtering=settings.get('AllowExternalDataFiltering', False),
                external_data_filtering_allow_list=settings.get('ExternalDataFilteringAllowList', [])
            )
        except Exception as e:
            self.logger.error(f"Erro ao obter configurações do data lake: {e}")
            return None

    def get_databases(self) -> List[LakeFormationDatabase]:
        """Lista databases do catálogo."""
        databases = []
        try:
            paginator = self.glue_client.get_paginator('get_databases')
            for page in paginator.paginate():
                for db in page.get('DatabaseList', []):
                    databases.append(LakeFormationDatabase(
                        name=db.get('Name', ''),
                        catalog_id=db.get('CatalogId', ''),
                        description=db.get('Description', ''),
                        location_uri=db.get('LocationUri', ''),
                        parameters=db.get('Parameters', {}),
                        create_time=db.get('CreateTime'),
                        create_table_default_permissions=db.get('CreateTableDefaultPermissions', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar databases: {e}")
        return databases

    def get_tables(self, database_name: str = None) -> List[LakeFormationTable]:
        """Lista tabelas do catálogo."""
        tables = []
        try:
            databases = [database_name] if database_name else [db.name for db in self.get_databases()]
            
            for db_name in databases[:10]:  # Limitar para evitar timeout
                try:
                    paginator = self.glue_client.get_paginator('get_tables')
                    for page in paginator.paginate(DatabaseName=db_name):
                        for table in page.get('TableList', []):
                            tables.append(LakeFormationTable(
                                name=table.get('Name', ''),
                                database_name=table.get('DatabaseName', ''),
                                catalog_id=table.get('CatalogId', ''),
                                table_type=table.get('TableType', 'EXTERNAL_TABLE'),
                                owner=table.get('Owner', ''),
                                create_time=table.get('CreateTime'),
                                update_time=table.get('UpdateTime'),
                                last_access_time=table.get('LastAccessTime'),
                                storage_descriptor=table.get('StorageDescriptor', {}),
                                partition_keys=table.get('PartitionKeys', []),
                                parameters=table.get('Parameters', {})
                            ))
                except Exception as e:  # noqa: E722
                    continue
        except Exception as e:
            self.logger.error(f"Erro ao listar tabelas: {e}")
        return tables

    def get_lf_tags(self) -> List[LFTag]:
        """Lista LF-Tags."""
        tags = []
        try:
            paginator = self.lakeformation_client.get_paginator('list_lf_tags')
            for page in paginator.paginate():
                for tag in page.get('LFTags', []):
                    tags.append(LFTag(
                        tag_key=tag.get('TagKey', ''),
                        tag_values=tag.get('TagValues', []),
                        catalog_id=tag.get('CatalogId', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar LF-Tags: {e}")
        return tags

    def get_permissions(self) -> List[LakeFormationPermission]:
        """Lista permissões."""
        permissions = []
        try:
            paginator = self.lakeformation_client.get_paginator('list_permissions')
            for page in paginator.paginate():
                for perm in page.get('PrincipalResourcePermissions', []):
                    permissions.append(LakeFormationPermission(
                        principal=perm.get('Principal', {}),
                        resource=perm.get('Resource', {}),
                        permissions=perm.get('Permissions', []),
                        permissions_with_grant_option=perm.get('PermissionsWithGrantOption', [])
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar permissões: {e}")
        return permissions

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos Lake Formation."""
        settings = self.get_data_lake_settings()
        databases = self.get_databases()
        tables = self.get_tables()
        lf_tags = self.get_lf_tags()
        permissions = self.get_permissions()

        return {
            "data_lake_settings": settings.to_dict() if settings else None,
            "databases": [db.to_dict() for db in databases],
            "tables": [t.to_dict() for t in tables],
            "lf_tags": [tag.to_dict() for tag in lf_tags],
            "permissions_count": len(permissions),
            "summary": {
                "admins_count": settings.admins_count if settings else 0,
                "total_databases": len(databases),
                "total_tables": len(tables),
                "external_tables": len([t for t in tables if t.is_external]),
                "governed_tables": len([t for t in tables if t.is_governed]),
                "tables_with_partitions": len([t for t in tables if t.has_partitions]),
                "total_lf_tags": len(lf_tags),
                "total_permissions": len(permissions),
                "full_access_permissions": len([p for p in permissions if p.is_full_access])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do Lake Formation."""
        settings = self.get_data_lake_settings()
        databases = self.get_databases()
        tables = self.get_tables()
        lf_tags = self.get_lf_tags()
        permissions = self.get_permissions()

        return {
            "admins_count": settings.admins_count if settings else 0,
            "databases_count": len(databases),
            "tables_count": len(tables),
            "external_tables": len([t for t in tables if t.is_external]),
            "governed_tables": len([t for t in tables if t.is_governed]),
            "partitioned_tables": len([t for t in tables if t.has_partitions]),
            "lf_tags_count": len(lf_tags),
            "total_tag_values": sum(tag.values_count for tag in lf_tags),
            "permissions_count": len(permissions),
            "permission_types": {
                "database": len([p for p in permissions if p.resource_type == "DATABASE"]),
                "table": len([p for p in permissions if p.resource_type == "TABLE"]),
                "data_location": len([p for p in permissions if p.resource_type == "DATA_LOCATION"]),
                "lf_tag": len([p for p in permissions if p.resource_type == "LF_TAG"])
            }
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para Lake Formation."""
        recommendations = []
        settings = self.get_data_lake_settings()
        databases = self.get_databases()
        tables = self.get_tables()
        permissions = self.get_permissions()

        # Verificar se há administradores configurados
        if settings and settings.admins_count == 0:
            recommendations.append({
                "resource_type": "DataLakeSettings",
                "resource_id": "settings",
                "recommendation": "Configurar administradores do data lake",
                "description": "Nenhum administrador configurado para o Lake Formation. "
                               "Recomendado configurar para governança adequada.",
                "priority": "high"
            })

        # Verificar databases sem localização
        for db in databases:
            if not db.has_location:
                recommendations.append({
                    "resource_type": "LakeFormationDatabase",
                    "resource_id": db.name,
                    "recommendation": "Definir localização do database",
                    "description": f"Database '{db.name}' não tem localização S3 definida. "
                                   "Definir para melhor organização de dados.",
                    "priority": "low"
                })

        # Verificar tabelas sem partições (para tabelas grandes)
        large_external_tables = [t for t in tables if t.is_external and not t.has_partitions]
        if len(large_external_tables) > 5:
            recommendations.append({
                "resource_type": "LakeFormationTable",
                "resource_id": "multiple",
                "recommendation": "Considerar particionamento de tabelas",
                "description": f"{len(large_external_tables)} tabelas externas sem partições. "
                               "Particionar pode melhorar performance e reduzir custos de query.",
                "priority": "medium"
            })

        # Verificar permissões com grant option
        grant_permissions = [p for p in permissions if p.has_grant_option]
        if len(grant_permissions) > 10:
            recommendations.append({
                "resource_type": "LakeFormationPermission",
                "resource_id": "multiple",
                "recommendation": "Revisar permissões com grant option",
                "description": f"{len(grant_permissions)} permissões com opção de grant. "
                               "Revisar para garantir princípio de menor privilégio.",
                "priority": "medium"
            })

        # Verificar permissões de acesso completo
        full_access = [p for p in permissions if p.is_full_access]
        if len(full_access) > 5:
            recommendations.append({
                "resource_type": "LakeFormationPermission",
                "resource_id": "multiple",
                "recommendation": "Revisar permissões de acesso completo",
                "description": f"{len(full_access)} permissões com acesso ALL. "
                               "Considerar permissões mais granulares para segurança.",
                "priority": "high"
            })

        return recommendations
