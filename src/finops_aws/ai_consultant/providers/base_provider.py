"""
Base AI Provider - Interface Abstrata para Provedores de IA

Define o contrato que todos os provedores de IA devem implementar.
Usa o Strategy Pattern do GoF para permitir troca dinamica de provedores.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class AIProviderType(Enum):
    """Tipos de provedores de IA suportados"""
    AMAZON_Q = "amazon_q"
    OPENAI = "openai"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"


class PersonaType(Enum):
    """Tipos de personas para relatorios FinOps"""
    EXECUTIVE = "executive"
    CTO = "cto"
    DEVOPS = "devops"
    ANALYST = "analyst"


@dataclass
class AIProviderConfig:
    """
    Configuracao generica para provedores de IA
    
    Attributes:
        provider_type: Tipo do provedor (AMAZON_Q, OPENAI, etc)
        api_key: Chave de API (para provedores externos)
        model: Modelo a ser usado
        temperature: Temperatura para geracao (0.0 a 1.0)
        max_tokens: Maximo de tokens na resposta
        region: Regiao (para AWS)
        extra_config: Configuracoes adicionais especificas
    """
    provider_type: AIProviderType
    api_key: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    region: str = "us-east-1"
    extra_config: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, provider_type: AIProviderType) -> 'AIProviderConfig':
        """
        Cria configuracao a partir de variaveis de ambiente
        
        Args:
            provider_type: Tipo do provedor
            
        Returns:
            AIProviderConfig configurado
        """
        import os
        
        config = cls(provider_type=provider_type)
        
        if provider_type == AIProviderType.AMAZON_Q:
            config.extra_config = {
                'application_id': os.environ.get('Q_BUSINESS_APPLICATION_ID'),
                'index_id': os.environ.get('Q_BUSINESS_INDEX_ID'),
            }
            config.region = os.environ.get('AWS_REGION', 'us-east-1')
            
        elif provider_type == AIProviderType.OPENAI:
            config.api_key = os.environ.get('OPENAI_API_KEY')
            config.model = os.environ.get('OPENAI_MODEL', 'gpt-4o')
            
        elif provider_type == AIProviderType.GEMINI:
            config.api_key = os.environ.get('GEMINI_API_KEY')
            config.model = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
            
        elif provider_type == AIProviderType.PERPLEXITY:
            config.api_key = os.environ.get('PERPLEXITY_API_KEY')
            config.model = os.environ.get('PERPLEXITY_MODEL', 'llama-3.1-sonar-large-128k-online')
            
        return config


@dataclass
class AIResponse:
    """
    Resposta padronizada de qualquer provedor de IA
    
    Attributes:
        content: Conteudo da resposta (texto)
        provider: Tipo do provedor que gerou a resposta
        model: Modelo usado
        tokens_used: Tokens consumidos (input + output)
        latency_ms: Latencia da requisicao em millisegundos
        metadata: Metadados adicionais da resposta
        sources: Fontes citadas (se disponivel)
        timestamp: Momento da resposta
    """
    content: str
    provider: AIProviderType
    model: str
    tokens_used: int = 0
    latency_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario"""
        return {
            "content": self.content,
            "provider": self.provider.value,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
            "sources": self.sources,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAIProvider(ABC):
    """
    Interface Abstrata para Provedores de IA (Strategy Pattern)
    
    Todos os provedores de IA devem implementar esta interface,
    garantindo consistencia e permitindo troca transparente.
    
    Example:
        ```python
        # Usando qualquer provedor
        provider = AIProviderFactory.create("openai")
        response = provider.generate_report(costs, resources, "executive")
        print(response.content)
        ```
    """
    
    def __init__(self, config: AIProviderConfig):
        """
        Inicializa o provedor
        
        Args:
            config: Configuracao do provedor
        """
        self.config = config
        self._client = None
    
    @property
    @abstractmethod
    def provider_type(self) -> AIProviderType:
        """Retorna o tipo do provedor"""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """Retorna lista de modelos disponiveis"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saude da conexao com o provedor
        
        Returns:
            Dict com status de saude
        """
        pass
    
    @abstractmethod
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Envia mensagem para o provedor de IA
        
        Args:
            message: Mensagem do usuario
            system_prompt: Prompt de sistema (opcional)
            context: Contexto adicional (opcional)
            
        Returns:
            AIResponse com a resposta
        """
        pass
    
    @abstractmethod
    def generate_report(
        self,
        costs: Dict[str, Any],
        resources: Dict[str, Any],
        persona: PersonaType = PersonaType.EXECUTIVE
    ) -> AIResponse:
        """
        Gera relatorio FinOps usando IA
        
        Args:
            costs: Dados de custo AWS
            resources: Dados de recursos AWS
            persona: Tipo de persona para o relatorio
            
        Returns:
            AIResponse com o relatorio gerado
        """
        pass
    
    def _build_finops_prompt(
        self,
        costs: Dict[str, Any],
        resources: Dict[str, Any],
        persona: PersonaType
    ) -> str:
        """
        Constroi prompt padrao FinOps
        
        Args:
            costs: Dados de custo
            resources: Dados de recursos
            persona: Tipo de persona
            
        Returns:
            Prompt formatado
        """
        import json
        
        persona_instructions = self._get_persona_instructions(persona)
        
        return f"""## Contexto do Sistema

Voce e um consultor senior de FinOps especializado em AWS, com mais de 15 anos 
de experiencia em otimizacao de custos cloud. Voce trabalha para uma empresa 
de consultoria de excelencia.

Seu conhecimento inclui:
- Todos os 246 servicos AWS e seus modelos de precificacao
- AWS Well-Architected Framework (Cost Optimization Pillar)
- FinOps Framework e melhores praticas
- Estrategias de Reserved Instances, Savings Plans e Spot
- Rightsizing, automacao e governanca de custos

## Dados de Custo AWS

{json.dumps(costs, indent=2, default=str)}

## Recursos AWS Ativos

{json.dumps(resources, indent=2, default=str)}

## Instrucoes

{persona_instructions}

## Formato de Saida

- Use Markdown com headers hierarquicos
- Valores monetarios em USD
- Priorize por impacto financeiro
- Idioma: Portugues do Brasil
"""

    def _get_persona_instructions(self, persona: PersonaType) -> str:
        """
        Retorna instrucoes especificas da persona
        
        Args:
            persona: Tipo de persona
            
        Returns:
            Instrucoes formatadas
        """
        instructions = {
            PersonaType.EXECUTIVE: """
Produza um relatorio executivo de custos AWS com:

### 1. RESUMO EXECUTIVO (2 paragrafos)
- Gasto total do periodo em USD
- Top 3 servicos que mais impactam o custo

### 2. TOP 3 OPORTUNIDADES DE ECONOMIA
| Oportunidade | Economia/Mes | Prazo |
|--------------|--------------|-------|

### 3. PROXIMOS PASSOS (3 acoes prioritarias)

**Tom**: Executivo, foco em ROI e impacto no negocio.
**Limite**: Maximo 2 paginas.
""",
            PersonaType.CTO: """
Produza um relatorio tecnico-estrategico de custos AWS com:

### 1. VISAO GERAL TECNICA
- Total de recursos por categoria
- Cobertura de Reserved Instances e Savings Plans

### 2. ANALISE POR CAMADA ARQUITETURAL
Para cada camada (Compute, Storage, Database, Network):
- Custo total e % do gasto
- Alternativas arquiteturais

### 3. ROADMAP DE MODERNIZACAO
**Fase 1**: 0-30 dias
**Fase 2**: 30-90 dias
**Fase 3**: 90-180 dias

**Tom**: Tecnico-estrategico, foco em arquitetura.
""",
            PersonaType.DEVOPS: """
Produza um relatorio operacional de custos AWS com:

### 1. RESUMO OPERACIONAL
- Total de recursos ativos
- Recursos com alertas de custo

### 2. ACOES IMEDIATAS
Para cada recurso que precisa de acao:
- ID do recurso
- Comando AWS CLI para resolver

### 3. SCRIPTS DE AUTOMACAO
Forneca scripts Bash/Python para:
- Identificar recursos subutilizados
- Aplicar tags em lote

### 4. CHECKLIST DE IMPLEMENTACAO
- [ ] Lista de acoes ordenadas

**Tom**: Pratico e tecnico, foco em implementacao.
""",
            PersonaType.ANALYST: """
Produza um relatorio analitico de custos AWS com:

### 1. DASHBOARD DE METRICAS
| KPI | Valor | Meta | Status |
|-----|-------|------|--------|

### 2. ANALISE POR SERVICO
| Servico | Custo | % Total | Tendencia |
|---------|-------|---------|-----------|

### 3. COBERTURA DE COMPROMISSOS
- Reserved Instances
- Savings Plans

### 4. ANALISE DE WASTE
- Recursos ociosos
- Waste ratio por servico

### 5. MATURIDADE FINOPS
| Dominio | Nivel | Meta |
|---------|-------|------|

**Tom**: Analitico e data-driven.
"""
        }
        
        return instructions.get(persona, instructions[PersonaType.EXECUTIVE])
