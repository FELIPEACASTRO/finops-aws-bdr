"""
Value Object: AWS Service Name
Representa nomes de serviços AWS com validações de domínio
Complexidade: O(1) para todas as operações
"""
from dataclasses import dataclass
from typing import Dict, Set
import re


# Known AWS service patterns - Domain Knowledge (moved outside class)
_AWS_SERVICE_PATTERNS: Set[str] = frozenset({
    "Amazon Elastic Compute Cloud",
    "Amazon Simple Storage Service",
    "Amazon Relational Database Service",
    "AWS Lambda",
    "Amazon CloudWatch",
    "Amazon Virtual Private Cloud",
    "Amazon CloudFront",
    "Amazon Route 53",
    "Amazon Simple Notification Service",
    "Amazon Simple Queue Service",
    "Amazon DynamoDB",
    "Amazon ElastiCache",
    "Amazon Redshift",
    "Amazon Elasticsearch Service",
    "Amazon Kinesis",
    "Amazon API Gateway",
    "AWS Identity and Access Management",
    "AWS CloudFormation",
    "AWS CodePipeline",
    "AWS CodeBuild",
    "AWS CodeDeploy",
    "Amazon Elastic Container Service",
    "Amazon Elastic Kubernetes Service",
    "AWS Fargate"
})

# Service abbreviations mapping (immutable)
_SERVICE_ABBREVIATIONS: Dict[str, str] = {
    "EC2": "Amazon Elastic Compute Cloud",
    "S3": "Amazon Simple Storage Service",
    "RDS": "Amazon Relational Database Service",
    "Lambda": "AWS Lambda",
    "CloudWatch": "Amazon CloudWatch",
    "VPC": "Amazon Virtual Private Cloud",
    "CloudFront": "Amazon CloudFront",
    "Route53": "Amazon Route 53",
    "SNS": "Amazon Simple Notification Service",
    "SQS": "Amazon Simple Queue Service",
    "DynamoDB": "Amazon DynamoDB",
    "ElastiCache": "Amazon ElastiCache",
    "Redshift": "Amazon Redshift",
    "ES": "Amazon Elasticsearch Service",
    "Kinesis": "Amazon Kinesis",
    "API Gateway": "Amazon API Gateway",
    "IAM": "AWS Identity and Access Management",
    "CloudFormation": "AWS CloudFormation",
    "CodePipeline": "AWS CodePipeline",
    "CodeBuild": "AWS CodeBuild",
    "CodeDeploy": "AWS CodeDeploy",
    "ECS": "Amazon Elastic Container Service",
    "EKS": "Amazon Elastic Kubernetes Service",
    "Fargate": "AWS Fargate"
}


@dataclass(frozen=True)  # Immutable Value Object
class ServiceName:
    """
    Value Object para nomes de serviços AWS

    DDD Principles:
    - Imutável
    - Validações de domínio específicas
    - Conhecimento do negócio (AWS services)

    Complexidade: O(1) para todas as operações
    """
    name: str

    def __post_init__(self):
        """
        Validações de domínio
        SOLID: Single Responsibility - apenas validação
        """
        if not self.name or not self.name.strip():
            raise ValueError("Service name cannot be empty")

        # Normalize whitespace
        normalized_name = re.sub(r'\s+', ' ', self.name.strip())
        object.__setattr__(self, 'name', normalized_name)

        # Validate length (AWS service names are typically reasonable length)
        if len(self.name) > 100:
            raise ValueError("Service name too long (max 100 characters)")

    def is_known_aws_service(self) -> bool:
        """
        Verifica se é um serviço AWS conhecido

        Complexidade: O(1) - lookup em set
        Domain Logic: Conhecimento específico do domínio AWS
        """
        # Check exact match
        if self.name in _AWS_SERVICE_PATTERNS:
            return True

        # Check if it starts with known patterns (for services with suffixes)
        for pattern in _AWS_SERVICE_PATTERNS:
            if self.name.startswith(pattern):
                return True

        return False

    def get_abbreviation(self) -> str:
        """
        Retorna abreviação do serviço se conhecida

        Complexidade: O(1)
        Clean Code: Nome descritivo
        """
        # Check if the name itself is an abbreviation
        for abbrev, full_name in _SERVICE_ABBREVIATIONS.items():
            if self.name == full_name:
                return abbrev

        # Check for partial matches
        for abbrev, full_name in _SERVICE_ABBREVIATIONS.items():
            if full_name in self.name:
                return abbrev

        # Return first letters of each word as fallback
        words = self.name.split()
        if len(words) > 1:
            return ''.join(word[0].upper() for word in words if word)

        return self.name[:3].upper()

    def get_service_category(self) -> str:
        """
        Categoriza o serviço AWS

        Complexidade: O(1)
        Domain Logic: Conhecimento de categorias AWS
        """
        compute_services = {
            "Amazon Elastic Compute Cloud", "AWS Lambda", "Amazon Elastic Container Service",
            "Amazon Elastic Kubernetes Service", "AWS Fargate"
        }

        storage_services = {
            "Amazon Simple Storage Service", "Amazon Elastic Block Store"
        }

        database_services = {
            "Amazon Relational Database Service", "Amazon DynamoDB",
            "Amazon ElastiCache", "Amazon Redshift"
        }

        networking_services = {
            "Amazon Virtual Private Cloud", "Amazon CloudFront", "Amazon Route 53",
            "Amazon API Gateway"
        }

        monitoring_services = {
            "Amazon CloudWatch"
        }

        messaging_services = {
            "Amazon Simple Notification Service", "Amazon Simple Queue Service",
            "Amazon Kinesis"
        }

        # Check categories
        for service in compute_services:
            if service in self.name:
                return "Compute"

        for service in storage_services:
            if service in self.name:
                return "Storage"

        for service in database_services:
            if service in self.name:
                return "Database"

        for service in networking_services:
            if service in self.name:
                return "Networking"

        for service in monitoring_services:
            if service in self.name:
                return "Monitoring"

        for service in messaging_services:
            if service in self.name:
                return "Messaging"

        return "Other"

    def __str__(self) -> str:
        """String representation"""
        return self.name

    def __hash__(self) -> int:
        """Hash for use as dictionary key"""
        return hash(self.name)

    def __eq__(self, other) -> bool:
        """Equality based on value"""
        if not isinstance(other, ServiceName):
            return False
        return self.name == other.name

    @classmethod
    def from_abbreviation(cls, abbreviation: str) -> 'ServiceName':
        """
        Factory method para criar a partir de abreviação
        Design Pattern: Factory Method
        Complexidade: O(1)
        """
        full_name = _SERVICE_ABBREVIATIONS.get(abbreviation.upper())
        if full_name:
            return cls(full_name)
        return cls(abbreviation)

    @classmethod
    def ec2(cls) -> 'ServiceName':
        """Factory method para EC2"""
        return cls("Amazon Elastic Compute Cloud - Compute")

    @classmethod
    def s3(cls) -> 'ServiceName':
        """Factory method para S3"""
        return cls("Amazon Simple Storage Service")

    @classmethod
    def lambda_service(cls) -> 'ServiceName':
        """Factory method para Lambda"""
        return cls("AWS Lambda")
