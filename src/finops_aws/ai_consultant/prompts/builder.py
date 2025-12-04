"""
Prompt Builder

Construtor de prompts estruturados para Amazon Q Business.
Gera prompts otimizados para diferentes tipos de análise FinOps.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from .personas import PromptPersona, PersonaConfig, get_persona_config
from .templates.executive import EXECUTIVE_REPORT_TEMPLATE
from .templates.technical import TECHNICAL_REPORT_TEMPLATE
from .templates.operational import OPERATIONAL_REPORT_TEMPLATE
from .templates.analyst import ANALYST_REPORT_TEMPLATE


class PromptBuilder:
    """
    Construtor de prompts para Amazon Q Business
    
    Gera prompts estruturados e otimizados para:
    - Análises de custo
    - Relatórios executivos
    - Planos de otimização
    - Comparativos de períodos
    - Explicações de anomalias
    
    Example:
        ```python
        builder = PromptBuilder()
        
        prompt = builder.build_analysis_prompt(
            cost_data={"total_cost": 47523.89, ...},
            period="2024-11-01 a 2024-11-30",
            persona=PromptPersona.EXECUTIVE
        )
        ```
    """
    
    TEMPLATE_MAP = {
        PromptPersona.EXECUTIVE: EXECUTIVE_REPORT_TEMPLATE,
        PromptPersona.CTO: TECHNICAL_REPORT_TEMPLATE,
        PromptPersona.DEVOPS: OPERATIONAL_REPORT_TEMPLATE,
        PromptPersona.ANALYST: ANALYST_REPORT_TEMPLATE
    }
    
    def __init__(self, default_language: str = "pt-BR"):
        """
        Inicializa builder
        
        Args:
            default_language: Idioma padrão para relatórios
        """
        self.default_language = default_language
    
    def build_analysis_prompt(
        self,
        cost_data: Dict[str, Any],
        period: str,
        persona: PromptPersona = PromptPersona.EXECUTIVE,
        include_recommendations: bool = True,
        include_trends: bool = True,
        include_anomalies: bool = True,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Constrói prompt de análise de custos
        
        Args:
            cost_data: Dados de custo consolidados
            period: Período de análise
            persona: Persona alvo
            include_recommendations: Incluir recomendações
            include_trends: Incluir análise de tendências
            include_anomalies: Incluir detecção de anomalias
            custom_instructions: Instruções customizadas adicionais
            
        Returns:
            Prompt estruturado para Q Business
        """
        persona_config = get_persona_config(persona)
        template = self.TEMPLATE_MAP.get(persona, EXECUTIVE_REPORT_TEMPLATE)
        
        cost_json = json.dumps(cost_data, indent=2, default=str, ensure_ascii=False)
        
        sections = self._get_requested_sections(
            include_recommendations,
            include_trends,
            include_anomalies,
            persona_config
        )
        
        prompt = f"""
{self._get_system_context()}

{persona_config.to_prompt_context()}

## Dados de Custo AWS

**Período de Análise**: {period}
**Data de Geração**: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}

```json
{cost_json}
```

## Instruções de Análise

{template}

## Seções Solicitadas

{sections}

## Diretrizes de Formatação

1. Use Markdown com headers hierárquicos (##, ###)
2. Inclua tabelas para dados comparativos
3. Valores monetários em USD com 2 casas decimais
4. Priorize recomendações por impacto financeiro (maior economia primeiro)
5. {"Inclua comandos AWS CLI quando apropriado" if persona_config.include_commands else "Não inclua comandos técnicos"}
6. Idioma: {self.default_language}
7. Tom: {persona_config.tone}
"""
        
        if custom_instructions:
            prompt += f"\n## Instruções Adicionais\n\n{custom_instructions}\n"
        
        return prompt.strip()
    
    def build_question_prompt(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Constrói prompt para pergunta específica
        
        Args:
            question: Pergunta do usuário
            context: Contexto de dados
            
        Returns:
            Prompt formatado
        """
        context_json = json.dumps(context, indent=2, default=str, ensure_ascii=False)
        
        return f"""
{self._get_system_context()}

## Contexto de Dados

```json
{context_json}
```

## Pergunta

{question}

## Instruções

Responda a pergunta acima com base nos dados de contexto fornecidos.
- Seja preciso e objetivo
- Cite números específicos quando disponíveis
- Forneça recomendações práticas quando aplicável
- Idioma: {self.default_language}
"""
    
    def build_cost_explanation_prompt(
        self,
        context: Dict[str, Any]
    ) -> str:
        """
        Constrói prompt para explicar variação de custo
        
        Args:
            context: Dados de variação (service, costs, change_pct)
            
        Returns:
            Prompt formatado
        """
        service = context.get('service', 'Unknown')
        current = context.get('current_cost', 0)
        previous = context.get('previous_cost', 0)
        change_pct = context.get('change_percentage', 0)
        details = context.get('details', {})
        
        return f"""
{self._get_system_context()}

## Análise de Variação de Custo

**Serviço**: {service}
**Custo Atual**: ${current:,.2f}
**Custo Anterior**: ${previous:,.2f}
**Variação**: {change_pct:+.1f}%

### Detalhes Adicionais

```json
{json.dumps(details, indent=2, default=str, ensure_ascii=False)}
```

## Solicitação

Explique detalhadamente:

1. **Por que o custo {"aumentou" if change_pct > 0 else "diminuiu"}?**
   - Identifique as causas raiz prováveis
   - Correlacione com eventos ou mudanças de uso

2. **Quais recursos específicos contribuíram para essa variação?**
   - Liste os principais contribuintes
   - Quantifique o impacto de cada um

3. **Essa variação é esperada ou anômala?**
   - Compare com padrões históricos
   - Identifique se é sazonal ou pontual

4. **O que pode ser feito para otimizar?**
   - Recomendações práticas
   - Estimativa de economia potencial

Seja específico e forneça dados quantitativos quando possível.
"""
    
    def build_optimization_plan_prompt(
        self,
        cost_data: Dict[str, Any],
        target_reduction: float,
        timeframe_days: int
    ) -> str:
        """
        Constrói prompt para plano de otimização
        
        Args:
            cost_data: Dados de custo atuais
            target_reduction: Meta de redução (%)
            timeframe_days: Prazo em dias
            
        Returns:
            Prompt formatado
        """
        cost_json = json.dumps(cost_data, indent=2, default=str, ensure_ascii=False)
        
        return f"""
{self._get_system_context()}

## Solicitação de Plano de Otimização

**Meta de Redução**: {target_reduction}%
**Prazo**: {timeframe_days} dias

## Dados de Custo Atuais

```json
{cost_json}
```

## Estrutura do Plano Solicitado

### 1. Resumo Executivo
- Meta em valores absolutos (USD)
- Viabilidade da meta
- Principais alavancas de economia

### 2. Fase 1: Quick Wins (0-30 dias)
Para cada ação:
- Descrição clara
- Economia estimada (USD/mês)
- Esforço de implementação
- Risco associado
- Passos de implementação

### 3. Fase 2: Otimizações de Médio Prazo (31-60 dias)
- Rightsizing de recursos
- Compromissos de uso (Reserved/Savings Plans)
- Automação de desligamento

### 4. Fase 3: Transformações (61-{timeframe_days} dias)
- Mudanças arquiteturais
- Modernização (containers, serverless)
- Renegociações e consolidações

### 5. Cronograma Visual
- Timeline com marcos
- Economia acumulada esperada

### 6. Riscos e Mitigações
- Riscos de cada fase
- Plano de contingência

### 7. KPIs de Acompanhamento
- Métricas para monitorar progresso
- Frequência de revisão

Seja específico com números, serviços e recursos.
Priorize ações por ROI (maior economia com menor esforço primeiro).
"""
    
    def build_comparison_prompt(
        self,
        current_data: Dict[str, Any],
        previous_data: Dict[str, Any],
        labels: tuple = ("Atual", "Anterior")
    ) -> str:
        """
        Constrói prompt para comparação entre períodos
        
        Args:
            current_data: Dados do período atual
            previous_data: Dados do período anterior
            labels: Labels para os períodos
            
        Returns:
            Prompt formatado
        """
        return f"""
{self._get_system_context()}

## Análise Comparativa de Custos AWS

### Período {labels[0]}

```json
{json.dumps(current_data, indent=2, default=str, ensure_ascii=False)}
```

### Período {labels[1]}

```json
{json.dumps(previous_data, indent=2, default=str, ensure_ascii=False)}
```

## Solicitação de Análise

Produza uma análise comparativa detalhada incluindo:

1. **Resumo da Variação**
   - Diferença total em USD e percentual
   - Tendência geral (crescimento, estabilidade, redução)

2. **Top 5 Serviços com Maior Variação**
   | Serviço | {labels[1]} | {labels[0]} | Δ USD | Δ % |
   |---------|-------------|-------------|-------|-----|
   (preencher com dados reais)

3. **Análise por Serviço**
   Para cada serviço com variação significativa (>10%):
   - Causa provável da variação
   - Se é tendência ou evento pontual
   - Ação recomendada

4. **Oportunidades Identificadas**
   - Novas oportunidades de economia
   - Otimizações que surgiram da comparação

5. **Alertas**
   - Tendências preocupantes
   - Serviços que merecem atenção

Formate como relatório profissional com tabelas e seções claras.
"""
    
    def _get_system_context(self) -> str:
        """Retorna contexto do sistema para o prompt"""
        return """
## Contexto do Sistema

Você é um consultor sênior de FinOps especializado em AWS, com mais de 15 anos 
de experiência em otimização de custos cloud. Você trabalha para uma empresa 
de consultoria de excelência e está produzindo uma análise para um cliente 
enterprise.

Seu conhecimento inclui:
- Todos os 253 serviços AWS e seus modelos de precificação
- AWS Well-Architected Framework (Cost Optimization Pillar)
- FinOps Framework e melhores práticas
- Estratégias de Reserved Instances, Savings Plans e Spot
- Rightsizing, automação e governança de custos

Suas análises são:
- Precisas e baseadas em dados
- Práticas e acionáveis
- Priorizadas por impacto financeiro
- Claras para a audiência alvo
"""
    
    def _get_requested_sections(
        self,
        include_recommendations: bool,
        include_trends: bool,
        include_anomalies: bool,
        persona_config: PersonaConfig
    ) -> str:
        """Gera lista de seções solicitadas"""
        sections = ["1. Resumo Executivo"]
        
        if include_trends:
            sections.append("2. Análise de Tendências")
        
        sections.append("3. Análise por Serviço (Top 10)")
        
        if include_anomalies:
            sections.append("4. Anomalias Detectadas")
        
        if include_recommendations:
            sections.append("5. Top 5 Oportunidades de Economia")
            sections.append("6. Quick Wins (próximos 7 dias)")
            sections.append("7. Plano 30-60-90 dias")
        
        sections.append("8. Riscos e Alertas")
        
        if persona_config.include_commands:
            sections.append("9. Comandos AWS CLI (para ações imediatas)")
        
        return '\n'.join(f"- {s}" for s in sections[:persona_config.max_sections])
