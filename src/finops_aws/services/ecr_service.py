"""
AWS ECR Service para FinOps.

Análise de custos e otimização de registros de containers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .base_service import BaseAWSService
from ..utils.logger import setup_logger


@dataclass
class ECRRepository:
    """Repositório ECR."""
    repository_name: str
    repository_arn: str = ""
    registry_id: str = ""
    repository_uri: str = ""
    created_at: Optional[datetime] = None
    image_tag_mutability: str = "MUTABLE"
    image_scanning_configuration: Dict[str, Any] = field(default_factory=dict)
    encryption_configuration: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_immutable(self) -> bool:
        """Verifica se tags são imutáveis."""
        return self.image_tag_mutability == "IMMUTABLE"

    @property
    def has_scan_on_push(self) -> bool:
        """Verifica se tem scan on push."""
        return self.image_scanning_configuration.get('scanOnPush', False)

    @property
    def has_encryption(self) -> bool:
        """Verifica se tem criptografia customizada."""
        return self.encryption_configuration.get('encryptionType', 'AES256') == 'KMS'

    @property
    def kms_key(self) -> Optional[str]:
        """KMS key usada."""
        return self.encryption_configuration.get('kmsKey')

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "repository_name": self.repository_name,
            "repository_arn": self.repository_arn,
            "repository_uri": self.repository_uri,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "image_tag_mutability": self.image_tag_mutability,
            "is_immutable": self.is_immutable,
            "has_scan_on_push": self.has_scan_on_push,
            "has_encryption": self.has_encryption
        }


@dataclass
class ECRImage:
    """Imagem ECR."""
    repository_name: str
    image_digest: str = ""
    image_tags: List[str] = field(default_factory=list)
    image_size_in_bytes: int = 0
    image_pushed_at: Optional[datetime] = None
    image_scan_status: Dict[str, Any] = field(default_factory=dict)
    image_scan_findings_summary: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_tagged(self) -> bool:
        """Verifica se tem tags."""
        return len(self.image_tags) > 0

    @property
    def is_untagged(self) -> bool:
        """Verifica se não tem tags."""
        return len(self.image_tags) == 0

    @property
    def size_mb(self) -> float:
        """Tamanho em MB."""
        return self.image_size_in_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Tamanho em GB."""
        return self.image_size_in_bytes / (1024 ** 3)

    @property
    def estimated_monthly_cost(self) -> float:
        """Custo mensal estimado ($0.10/GB/mês)."""
        return self.size_gb * 0.10

    @property
    def has_vulnerabilities(self) -> bool:
        """Verifica se tem vulnerabilidades."""
        findings = self.image_scan_findings_summary.get('findingSeverityCounts', {})
        return sum(findings.values()) > 0 if findings else False

    @property
    def critical_vulnerabilities(self) -> int:
        """Número de vulnerabilidades críticas."""
        return self.image_scan_findings_summary.get('findingSeverityCounts', {}).get('CRITICAL', 0)

    @property
    def high_vulnerabilities(self) -> int:
        """Número de vulnerabilidades altas."""
        return self.image_scan_findings_summary.get('findingSeverityCounts', {}).get('HIGH', 0)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "repository_name": self.repository_name,
            "image_digest": self.image_digest[:20] + "..." if len(self.image_digest) > 20 else self.image_digest,
            "image_tags": self.image_tags,
            "image_size_mb": self.size_mb,
            "image_pushed_at": self.image_pushed_at.isoformat() if self.image_pushed_at else None,
            "is_tagged": self.is_tagged,
            "has_vulnerabilities": self.has_vulnerabilities,
            "critical_vulnerabilities": self.critical_vulnerabilities,
            "estimated_monthly_cost": self.estimated_monthly_cost
        }


@dataclass
class ECRLifecyclePolicy:
    """Política de lifecycle ECR."""
    repository_name: str
    lifecycle_policy_text: str = ""
    registry_id: str = ""
    last_evaluated_at: Optional[datetime] = None

    @property
    def has_policy(self) -> bool:
        """Verifica se tem política."""
        return bool(self.lifecycle_policy_text)

    @property
    def rules_count(self) -> int:
        """Número de regras (estimativa)."""
        if not self.lifecycle_policy_text:
            return 0
        return self.lifecycle_policy_text.count('"rulePriority"')

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "repository_name": self.repository_name,
            "has_policy": self.has_policy,
            "rules_count": self.rules_count,
            "last_evaluated_at": self.last_evaluated_at.isoformat() if self.last_evaluated_at else None
        }


class ECRService(BaseAWSService):
    """Serviço para análise de custos e otimização do AWS ECR."""

    def __init__(self, client_factory):
        """Inicializa o serviço ECR."""
        super().__init__()
        self._client_factory = client_factory
        self.logger = setup_logger(__name__)
        self._ecr_client = None

    @property
    def ecr_client(self):
        """Cliente ECR com lazy loading."""
        if self._ecr_client is None:
            self._ecr_client = self._client_factory.get_client('ecr')
        return self._ecr_client

    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço ECR."""
        try:
            self.ecr_client.describe_repositories(maxResults=1)
            return {
                "service": "ecr",
                "status": "healthy",
                "message": "ECR service is accessible"
            }
        except Exception as e:
            return {
                "service": "ecr",
                "status": "unhealthy",
                "message": str(e)
            }

    def get_repositories(self) -> List[ECRRepository]:
        """Lista repositórios ECR."""
        repositories = []
        try:
            paginator = self.ecr_client.get_paginator('describe_repositories')
            for page in paginator.paginate():
                for repo in page.get('repositories', []):
                    repositories.append(ECRRepository(
                        repository_name=repo.get('repositoryName', ''),
                        repository_arn=repo.get('repositoryArn', ''),
                        registry_id=repo.get('registryId', ''),
                        repository_uri=repo.get('repositoryUri', ''),
                        created_at=repo.get('createdAt'),
                        image_tag_mutability=repo.get('imageTagMutability', 'MUTABLE'),
                        image_scanning_configuration=repo.get('imageScanningConfiguration', {}),
                        encryption_configuration=repo.get('encryptionConfiguration', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar repositórios: {e}")
        return repositories

    def get_images(self, repository_name: str) -> List[ECRImage]:
        """Lista imagens de um repositório."""
        images = []
        try:
            paginator = self.ecr_client.get_paginator('describe_images')
            for page in paginator.paginate(repositoryName=repository_name):
                for img in page.get('imageDetails', []):
                    images.append(ECRImage(
                        repository_name=repository_name,
                        image_digest=img.get('imageDigest', ''),
                        image_tags=img.get('imageTags', []),
                        image_size_in_bytes=img.get('imageSizeInBytes', 0),
                        image_pushed_at=img.get('imagePushedAt'),
                        image_scan_status=img.get('imageScanStatus', {}),
                        image_scan_findings_summary=img.get('imageScanFindingsSummary', {})
                    ))
        except Exception as e:
            self.logger.error(f"Erro ao listar imagens: {e}")
        return images

    def get_resources(self) -> Dict[str, Any]:
        """Obtém todos os recursos ECR."""
        repositories = self.get_repositories()
        all_images = []
        total_size_bytes = 0
        
        for repo in repositories[:10]:
            images = self.get_images(repo.repository_name)
            all_images.extend(images)
            total_size_bytes += sum(img.image_size_in_bytes for img in images)

        total_size_gb = total_size_bytes / (1024 ** 3)

        return {
            "repositories": [r.to_dict() for r in repositories],
            "images_sample": [i.to_dict() for i in all_images[:50]],
            "summary": {
                "total_repositories": len(repositories),
                "immutable_repositories": len([r for r in repositories if r.is_immutable]),
                "scan_on_push_enabled": len([r for r in repositories if r.has_scan_on_push]),
                "kms_encrypted": len([r for r in repositories if r.has_encryption]),
                "total_images": len(all_images),
                "untagged_images": len([i for i in all_images if i.is_untagged]),
                "total_size_gb": total_size_gb,
                "estimated_monthly_cost": total_size_gb * 0.10
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Obtém métricas de uso do ECR."""
        repositories = self.get_repositories()
        all_images = []
        total_size_bytes = 0
        
        for repo in repositories[:10]:
            images = self.get_images(repo.repository_name)
            all_images.extend(images)
            total_size_bytes += sum(img.image_size_in_bytes for img in images)

        return {
            "repositories_count": len(repositories),
            "immutable_repositories": len([r for r in repositories if r.is_immutable]),
            "mutable_repositories": len([r for r in repositories if not r.is_immutable]),
            "scan_on_push_enabled": len([r for r in repositories if r.has_scan_on_push]),
            "images_count": len(all_images),
            "tagged_images": len([i for i in all_images if i.is_tagged]),
            "untagged_images": len([i for i in all_images if i.is_untagged]),
            "images_with_vulnerabilities": len([i for i in all_images if i.has_vulnerabilities]),
            "total_storage_gb": total_size_bytes / (1024 ** 3),
            "estimated_monthly_cost": (total_size_bytes / (1024 ** 3)) * 0.10
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Gera recomendações de otimização para ECR."""
        recommendations = []
        repositories = self.get_repositories()
        all_images = []
        
        for repo in repositories[:10]:
            images = self.get_images(repo.repository_name)
            all_images.extend(images)

        # Verificar repositórios sem scan on push
        no_scan = [r for r in repositories if not r.has_scan_on_push]
        if no_scan:
            recommendations.append({
                "resource_type": "ECRRepository",
                "resource_id": "multiple",
                "recommendation": "Habilitar scan on push",
                "description": f"{len(no_scan)} repositório(s) sem scan automático. "
                               "Habilitar para detectar vulnerabilidades.",
                "priority": "medium"
            })

        # Verificar imagens não taggeadas
        untagged = [i for i in all_images if i.is_untagged]
        if untagged:
            total_untagged_size = sum(i.size_gb for i in untagged)
            recommendations.append({
                "resource_type": "ECRImage",
                "resource_id": "multiple",
                "recommendation": "Remover imagens não taggeadas",
                "description": f"{len(untagged)} imagem(ns) sem tags ocupando {total_untagged_size:.2f} GB. "
                               "Configurar lifecycle policy para limpeza automática.",
                "estimated_savings": total_untagged_size * 0.10,
                "priority": "high"
            })

        # Verificar vulnerabilidades críticas
        critical_vulns = [i for i in all_images if i.critical_vulnerabilities > 0]
        if critical_vulns:
            recommendations.append({
                "resource_type": "ECRImage",
                "resource_id": "multiple",
                "recommendation": "Corrigir vulnerabilidades críticas",
                "description": f"{len(critical_vulns)} imagem(ns) com vulnerabilidades CRÍTICAS. "
                               "Atualizar base images e dependências.",
                "priority": "high"
            })

        return recommendations
