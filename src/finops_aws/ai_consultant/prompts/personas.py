"""
Prompt Personas

Define diferentes personas para relatórios FinOps,
cada uma com tom, foco e nível de detalhe específicos.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any


class PromptPersona(Enum):
    """Tipos de persona para relatórios"""
    EXECUTIVE = "executive"
    CTO = "cto"
    DEVOPS = "devops"
    ANALYST = "analyst"
    CUSTOM = "custom"


@dataclass
class PersonaConfig:
    """Configuração de persona para prompts"""
    
    name: str
    description: str
    tone: str
    focus_areas: List[str]
    detail_level: str
    include_technical_details: bool
    include_commands: bool
    max_sections: int
    language: str = "pt-BR"
    
    def to_prompt_context(self) -> str:
        """Gera contexto de persona para o prompt"""
        return f"""
## Perfil do Destinatário

- **Cargo/Função**: {self.name}
- **Tom de comunicação**: {self.tone}
- **Áreas de foco**: {', '.join(self.focus_areas)}
- **Nível de detalhamento**: {self.detail_level}
- **Incluir detalhes técnicos**: {'Sim' if self.include_technical_details else 'Não'}
- **Incluir comandos AWS CLI**: {'Sim' if self.include_commands else 'Não'}
- **Idioma**: {self.language}
"""


PERSONA_CONFIGS: Dict[PromptPersona, PersonaConfig] = {
    PromptPersona.EXECUTIVE: PersonaConfig(
        name="CEO/CFO - Executivo",
        description="Liderança executiva focada em ROI e impacto no negócio",
        tone="Executivo, estratégico, orientado a resultados",
        focus_areas=[
            "ROI e economia total",
            "Tendências de custo",
            "Comparativo com budget",
            "Riscos financeiros",
            "Decisões estratégicas"
        ],
        detail_level="Alto nível, 1-2 páginas",
        include_technical_details=False,
        include_commands=False,
        max_sections=5
    ),
    
    PromptPersona.CTO: PersonaConfig(
        name="CTO - Diretor de Tecnologia",
        description="Liderança técnica focada em arquitetura e eficiência",
        tone="Técnico-estratégico, balanceado",
        focus_areas=[
            "Arquitetura e modernização",
            "Trade-offs técnicos",
            "Eficiência operacional",
            "Débito técnico relacionado a custo",
            "Roadmap de otimização"
        ],
        detail_level="Médio, 2-3 páginas",
        include_technical_details=True,
        include_commands=False,
        max_sections=7
    ),
    
    PromptPersona.DEVOPS: PersonaConfig(
        name="DevOps/SRE Lead",
        description="Engenharia focada em implementação e automação",
        tone="Técnico-operacional, prático",
        focus_areas=[
            "Ações práticas de otimização",
            "Scripts e automação",
            "Configurações específicas",
            "Métricas de utilização",
            "Implementação passo-a-passo"
        ],
        detail_level="Detalhado, com comandos",
        include_technical_details=True,
        include_commands=True,
        max_sections=10
    ),
    
    PromptPersona.ANALYST: PersonaConfig(
        name="FinOps Analyst",
        description="Analista especializado em otimização de custos cloud",
        tone="Analítico, data-driven, detalhado",
        focus_areas=[
            "Métricas detalhadas",
            "Benchmarks de mercado",
            "Análise por centro de custo",
            "Showback/Chargeback",
            "KPIs de maturidade FinOps"
        ],
        detail_level="Muito detalhado, todas as métricas",
        include_technical_details=True,
        include_commands=True,
        max_sections=15
    )
}


def get_persona_config(persona: PromptPersona) -> PersonaConfig:
    """
    Obtém configuração de persona
    
    Args:
        persona: Tipo de persona
        
    Returns:
        PersonaConfig correspondente
    """
    return PERSONA_CONFIGS.get(persona, PERSONA_CONFIGS[PromptPersona.EXECUTIVE])


def create_custom_persona(
    name: str,
    tone: str,
    focus_areas: List[str],
    detail_level: str = "Médio",
    include_technical: bool = True,
    include_commands: bool = False
) -> PersonaConfig:
    """
    Cria persona customizada
    
    Args:
        name: Nome/cargo
        tone: Tom de comunicação
        focus_areas: Áreas de foco
        detail_level: Nível de detalhamento
        include_technical: Incluir detalhes técnicos
        include_commands: Incluir comandos AWS CLI
        
    Returns:
        PersonaConfig customizada
    """
    return PersonaConfig(
        name=name,
        description=f"Persona customizada: {name}",
        tone=tone,
        focus_areas=focus_areas,
        detail_level=detail_level,
        include_technical_details=include_technical,
        include_commands=include_commands,
        max_sections=10
    )
