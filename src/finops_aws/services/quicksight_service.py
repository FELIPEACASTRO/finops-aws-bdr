"""
AWS QuickSight Service para FinOps.

Análise de custos e otimização de dashboards e análises de BI.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class QuickSightDashboard:
    """Dashboard do QuickSight."""
    dashboard_id: str
    name: str = ""
    arn: str = ""
    version_number: int = 1
    created_time: Optional[datetime] = None
    last_updated_time: Optional[datetime] = None
    last_published_time: Optional[datetime] = None
    published_version_number: int = 0

    @property
    def is_published(self) -> bool:
        """Verifica se está publicado."""
        return self.published_version_number > 0

    @property
    def has_multiple_versions(self) -> bool:
        """Verifica se tem múltiplas versões."""
        return self.version_number > 1

    @property
    def age_days(self) -> int:
        """Idade do dashboard em dias."""
        if self.created_time:
            return (datetime.now(self.created_time.tzinfo) - self.created_time).days
        return 0

    @property
    def days_since_update(self) -> int:
        """Dias desde última atualização."""
        if self.last_updated_time:
            return (datetime.now(self.last_updated_time.tzinfo) - self.last_updated_time).days
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "dashboard_id": self.dashboard_id,
            "name": self.name,
            "arn": self.arn,
            "version_number": self.version_number,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "last_updated_time": self.last_updated_time.isoformat() if self.last_updated_time else None,
            "last_published_time": self.last_published_time.isoformat() if self.last_published_time else None,
            "published_version_number": self.published_version_number,
            "is_published": self.is_published,
            "has_multiple_versions": self.has_multiple_versions,
            "age_days": self.age_days,
            "days_since_update": self.days_since_update
        }


@dataclass
class QuickSightDataSet:
    """Dataset do QuickSight."""
    data_set_id: str
    name: str = ""
    arn: str = ""
    created_time: Optional[datetime] = None
    last_updated_time: Optional[datetime] = None
    import_mode: str = "SPICE"
    consumed_spice_capacity_in_bytes: int = 0
    row_level_permission_data_set: Optional[Dict[str, Any]] = None
    column_level_permission_rules_applied: bool = False

    @property
    def is_spice(self) -> bool:
        """Verifica se usa SPICE."""
        return self.import_mode == "SPICE"

    @property
    def is_direct_query(self) -> bool:
        """Verifica se é direct query."""
        return self.import_mode == "DIRECT_QUERY"

    @property
    def spice_capacity_gb(self) -> float:
        """Capacidade SPICE em GB."""
        return self.consumed_spice_capacity_in_bytes / (1024 ** 3)

    @property
    def has_row_level_security(self) -> bool:
        """Verifica se tem RLS."""
        return self.row_level_permission_data_set is not None

    @property
    def has_column_level_security(self) -> bool:
        """Verifica se tem CLS."""
        return self.column_level_permission_rules_applied

    @property
    def estimated_spice_cost_monthly(self) -> float:
        """Custo mensal estimado de SPICE ($0.38/GB)."""
        if self.is_spice:
            return self.spice_capacity_gb * 0.38
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "data_set_id": self.data_set_id,
            "name": self.name,
            "arn": self.arn,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "last_updated_time": self.last_updated_time.isoformat() if self.last_updated_time else None,
            "import_mode": self.import_mode,
            "consumed_spice_capacity_in_bytes": self.consumed_spice_capacity_in_bytes,
            "spice_capacity_gb": self.spice_capacity_gb,
            "is_spice": self.is_spice,
            "is_direct_query": self.is_direct_query,
            "has_row_level_security": self.has_row_level_security,
            "has_column_level_security": self.has_column_level_security,
            "estimated_spice_cost_monthly": self.estimated_spice_cost_monthly
        }


@dataclass
class QuickSightAnalysis:
    """Análise do QuickSight."""
    analysis_id: str
    name: str = ""
    arn: str = ""
    status: str = "CREATION_SUCCESSFUL"
    created_time: Optional[datetime] = None
    last_updated_time: Optional[datetime] = None
    theme_arn: Optional[str] = None
    data_set_arns: List[str] = field(default_factory=list)

    @property
    def is_successful(self) -> bool:
        """Verifica se criação foi bem sucedida."""
        return self.status == "CREATION_SUCCESSFUL"

    @property
    def is_failed(self) -> bool:
        """Verifica se criação falhou."""
        return self.status == "CREATION_FAILED"

    @property
    def has_theme(self) -> bool:
        """Verifica se tem tema customizado."""
        return self.theme_arn is not None

    @property
    def data_sets_count(self) -> int:
        """Número de datasets."""
        return len(self.data_set_arns)

    @property
    def age_days(self) -> int:
        """Idade da análise em dias."""
        if self.created_time:
            return (datetime.now(self.created_time.tzinfo) - self.created_time).days
        return 0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "analysis_id": self.analysis_id,
            "name": self.name,
            "arn": self.arn,
            "status": self.status,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "last_updated_time": self.last_updated_time.isoformat() if self.last_updated_time else None,
            "theme_arn": self.theme_arn,
            "data_sets_count": self.data_sets_count,
            "is_successful": self.is_successful,
            "is_failed": self.is_failed,
            "has_theme": self.has_theme,
            "age_days": self.age_days
        }


@dataclass
class QuickSightUser:
    """Usuário do QuickSight."""
    user_name: str
    email: str = ""
    role: str = "READER"
    identity_type: str = "QUICKSIGHT"
    active: bool = True
    principal_id: str = ""
    arn: str = ""

    @property
    def is_admin(self) -> bool:
        """Verifica se é admin."""
        return self.role == "ADMIN"

    @property
    def is_author(self) -> bool:
        """Verifica se é author."""
        return self.role == "AUTHOR"

    @property
    def is_reader(self) -> bool:
        """Verifica se é reader."""
        return self.role == "READER"

    @property
    def is_iam_user(self) -> bool:
        """Verifica se é usuário IAM."""
        return self.identity_type == "IAM"

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado por tipo de usuário."""
        if self.is_admin or self.is_author:
            return 24.0  # $24/mês para authors
        elif self.is_reader:
            return 0.30  # $0.30 por sessão (estimativa média)
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "user_name": self.user_name,
            "email": self.email,
            "role": self.role,
            "identity_type": self.identity_type,
            "active": self.active,
            "is_admin": self.is_admin,
            "is_author": self.is_author,
            "is_reader": self.is_reader,
            "is_iam_user": self.is_iam_user,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


class QuickSightService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS QuickSight."""

    def __init__(self, client_factory):
        """Inicializa o serviço QuickSight."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._quicksight_client = None
        self._account_id = None

    @property
    def quicksight_client(self):
        """Cliente QuickSight com lazy loading."""
        if self._quicksight_client is None:
            self._quicksight_client = self._client_factory.get_client('quicksight')
        return self._quicksight_client

    def _get_account_id(self) -> str:
        """Obtém o ID da conta AWS."""
        if self._account_id is None:
            try:
                sts = self._client_factory.get_client('sts')
                self._account_id = sts.get_caller_identity()['Account']
            except Exception:
                self._account_id = "000000000000"
        return self._account_id

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço QuickSight."""
        try:
            account_id = self._get_account_id()
            self.quicksight_client.list_dashboards(AwsAccountId=account_id, MaxResults=1)
            return {
                "service": "quicksight",
                "status": "healthy",
                "message": "QuickSight service is accessible"
            }
        except Exception as e:
            return {
                "service": "quicksight",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_dashboards(self) -> List[QuickSightDashboard]:
        """Lista dashboards."""
        dashboards = []
        try:
            account_id = self._get_account_id()
            paginator = self.quicksight_client.get_paginator('list_dashboards')
            for page in paginator.paginate(AwsAccountId=account_id):
                for dash in page.get('DashboardSummaryList', []):
                    dashboards.append(QuickSightDashboard(
                        dashboard_id=dash.get('DashboardId', ''),
                        name=dash.get('Name', ''),
                        arn=dash.get('Arn', ''),
                        created_time=dash.get('CreatedTime'),
                        last_updated_time=dash.get('LastUpdatedTime'),
                        last_published_time=dash.get('LastPublishedTime'),
                        published_version_number=dash.get('PublishedVersionNumber', 0)
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar dashboards: {e}")
        return dashboards

    def get_data_sets(self) -> List[QuickSightDataSet]:
        """Lista datasets."""
        datasets = []
        try:
            account_id = self._get_account_id()
            paginator = self.quicksight_client.get_paginator('list_data_sets')
            for page in paginator.paginate(AwsAccountId=account_id):
                for ds in page.get('DataSetSummaries', []):
                    datasets.append(QuickSightDataSet(
                        data_set_id=ds.get('DataSetId', ''),
                        name=ds.get('Name', ''),
                        arn=ds.get('Arn', ''),
                        created_time=ds.get('CreatedTime'),
                        last_updated_time=ds.get('LastUpdatedTime'),
                        import_mode=ds.get('ImportMode', 'SPICE'),
                        consumed_spice_capacity_in_bytes=ds.get('ConsumedSpiceCapacityInBytes', 0),
                        row_level_permission_data_set=ds.get('RowLevelPermissionDataSet'),
                        column_level_permission_rules_applied=ds.get('ColumnLevelPermissionRulesApplied', False)
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar datasets: {e}")
        return datasets

    def get_analyses(self) -> List[QuickSightAnalysis]:
        """Lista análises."""
        analyses = []
        try:
            account_id = self._get_account_id()
            paginator = self.quicksight_client.get_paginator('list_analyses')
            for page in paginator.paginate(AwsAccountId=account_id):
                for analysis in page.get('AnalysisSummaryList', []):
                    analyses.append(QuickSightAnalysis(
                        analysis_id=analysis.get('AnalysisId', ''),
                        name=analysis.get('Name', ''),
                        arn=analysis.get('Arn', ''),
                        status=analysis.get('Status', 'CREATION_SUCCESSFUL'),
                        created_time=analysis.get('CreatedTime'),
                        last_updated_time=analysis.get('LastUpdatedTime')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar análises: {e}")
        return analyses

    def get_users(self) -> List[QuickSightUser]:
        """Lista usuários."""
        users = []
        try:
            account_id = self._get_account_id()
            paginator = self.quicksight_client.get_paginator('list_users')
            for page in paginator.paginate(AwsAccountId=account_id, Namespace='default'):
                for user in page.get('UserList', []):
                    users.append(QuickSightUser(
                        user_name=user.get('UserName', ''),
                        email=user.get('Email', ''),
                        role=user.get('Role', 'READER'),
                        identity_type=user.get('IdentityType', 'QUICKSIGHT'),
                        active=user.get('Active', True),
                        principal_id=user.get('PrincipalId', ''),
                        arn=user.get('Arn', '')
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar usuários: {e}")
        return users

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos QuickSight."""
        dashboards = self.get_dashboards()
        datasets = self.get_data_sets()
        analyses = self.get_analyses()
        users = self.get_users()

        total_spice_gb = sum(ds.spice_capacity_gb for ds in datasets)

        return {
            "dashboards": [d.to_dict() for d in dashboards],
            "data_sets": [ds.to_dict() for ds in datasets],
            "analyses": [a.to_dict() for a in analyses],
            "users": [u.to_dict() for u in users],
            "summary": {
                "total_dashboards": len(dashboards),
                "published_dashboards": len([d for d in dashboards if d.is_published]),
                "total_datasets": len(datasets),
                "spice_datasets": len([ds for ds in datasets if ds.is_spice]),
                "total_spice_capacity_gb": total_spice_gb,
                "total_analyses": len(analyses),
                "successful_analyses": len([a for a in analyses if a.is_successful]),
                "total_users": len(users),
                "authors": len([u for u in users if u.is_author or u.is_admin]),
                "readers": len([u for u in users if u.is_reader])
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do QuickSight."""
        dashboards = self.get_dashboards()
        datasets = self.get_data_sets()
        analyses = self.get_analyses()
        users = self.get_users()

        total_spice_cost = sum(ds.estimated_spice_cost_monthly for ds in datasets)
        total_user_cost = sum(u.estimated_monthly_cost for u in users)

        return {
            "dashboards_count": len(dashboards),
            "published_dashboards": len([d for d in dashboards if d.is_published]),
            "datasets_count": len(datasets),
            "spice_datasets": len([ds for ds in datasets if ds.is_spice]),
            "direct_query_datasets": len([ds for ds in datasets if ds.is_direct_query]),
            "total_spice_capacity_gb": sum(ds.spice_capacity_gb for ds in datasets),
            "estimated_spice_cost_monthly": total_spice_cost,
            "analyses_count": len(analyses),
            "users_count": len(users),
            "authors_count": len([u for u in users if u.is_author or u.is_admin]),
            "readers_count": len([u for u in users if u.is_reader]),
            "estimated_user_cost_monthly": total_user_cost,
            "total_estimated_monthly_cost": total_spice_cost + total_user_cost
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para QuickSight."""
        recommendations = []
        dashboards = self.get_dashboards()
        datasets = self.get_data_sets()
        users = self.get_users()

        # Verificar dashboards não publicados antigos
        for dash in dashboards:
            if not dash.is_published and dash.age_days > 30:
                recommendations.append({
                    "resource_type": "QuickSightDashboard",
                    "resource_id": dash.name,
                    "recommendation": "Publicar ou remover dashboard antigo",
                    "description": f"Dashboard '{dash.name}' tem {dash.age_days} dias e não está publicado. "
                                   "Considerar publicar ou remover.",
                    "priority": "low"
                })

        # Verificar datasets SPICE grandes
        for ds in datasets:
            if ds.is_spice and ds.spice_capacity_gb > 10:
                recommendations.append({
                    "resource_type": "QuickSightDataSet",
                    "resource_id": ds.name,
                    "recommendation": "Otimizar dataset SPICE grande",
                    "description": f"Dataset '{ds.name}' usa {ds.spice_capacity_gb:.2f} GB de SPICE. "
                                   f"Custo mensal estimado: ${ds.estimated_spice_cost_monthly:.2f}. "
                                   "Considerar filtrar dados ou usar Direct Query.",
                    "estimated_savings": ds.estimated_spice_cost_monthly * 0.5,
                    "priority": "high"
                })

        # Verificar datasets sem segurança
        for ds in datasets:
            if not ds.has_row_level_security and not ds.has_column_level_security:
                recommendations.append({
                    "resource_type": "QuickSightDataSet",
                    "resource_id": ds.name,
                    "recommendation": "Considerar segurança em nível de linha/coluna",
                    "description": f"Dataset '{ds.name}' não tem RLS ou CLS. "
                                   "Considerar implementar para controle de acesso granular.",
                    "priority": "medium"
                })

        # Verificar usuários inativos
        inactive_users = [u for u in users if not u.active]
        if inactive_users:
            recommendations.append({
                "resource_type": "QuickSightUser",
                "resource_id": "multiple",
                "recommendation": "Remover usuários inativos",
                "description": f"{len(inactive_users)} usuário(s) inativos encontrados. "
                               "Considerar remover para reduzir custos de licenciamento.",
                "priority": "medium"
            })

        return recommendations
