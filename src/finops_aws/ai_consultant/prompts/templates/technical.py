"""
Technical Report Template

Template de prompt para relatórios técnico-estratégicos (CTO).
Foco em arquitetura, trade-offs e roadmap de modernização.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

TECHNICAL_REPORT_TEMPLATE = """
Produza um relatório técnico-estratégico de custos AWS com as seguintes características:

### Tom e Estilo
- Balanceado entre técnico e estratégico
- Foco em arquitetura e eficiência operacional
- Inclua trade-offs e alternativas
- Linguagem para liderança técnica

### Estrutura do Relatório

#### 1. VISÃO GERAL TÉCNICA

**Resumo de Infraestrutura**
- Total de recursos por categoria (compute, storage, database, network)
- Distribuição de custos por tipo de workload
- Cobertura de Reserved Instances e Savings Plans

**Eficiência Operacional**
- Utilização média de recursos críticos
- Recursos ociosos ou subutilizados
- Oportunidades de consolidação

#### 2. ANÁLISE POR CAMADA ARQUITETURAL

Para cada camada (Compute, Storage, Database, Network, Serverless):

**[Nome da Camada]**
- Custo total e % do gasto
- Principais recursos e custos
- Utilização e eficiência
- Oportunidades de otimização
- Alternativas arquiteturais

Exemplo para Compute:
- EC2: X instâncias, $Y/mês, Z% utilização média
- Lambda: N funções, $M/mês, P invocações/dia
- Containers (ECS/EKS): Q tasks, $R/mês

#### 3. DÉBITO TÉCNICO DE CUSTO

Identifique padrões que geram custo desnecessário:

| Padrão | Impacto/Mês | Causa Raiz | Solução Proposta |
|--------|-------------|------------|------------------|

Exemplos:
- Instâncias legadas sem rightsizing
- Arquiteturas não otimizadas para cloud
- Falta de automação (start/stop)
- Storage sem lifecycle policies

#### 4. ROADMAP DE MODERNIZAÇÃO

**Fase 1: Otimização Imediata (0-30 dias)**
- Rightsizing de recursos subutilizados
- Limpeza de recursos órfãos
- Aplicação de Savings Plans/RI

**Fase 2: Refatoração (30-90 dias)**
- Migração para Graviton (ARM)
- Containerização de workloads elegíveis
- Implementação de auto-scaling

**Fase 3: Transformação (90-180 dias)**
- Arquiteturas serverless onde aplicável
- Multi-region optimization
- FinOps as Code

#### 5. TRADE-OFFS E DECISÕES

Para cada grande decisão de otimização:

| Decisão | Benefício | Trade-off | Recomendação |
|---------|-----------|-----------|--------------|

Exemplos:
- Spot vs On-Demand vs Reserved
- Serverless vs Containers
- Managed vs Self-managed
- Single-region vs Multi-region

#### 6. MÉTRICAS TÉCNICAS

**KPIs Atuais**
- Cost per transaction/request
- Cost per user/customer
- Infrastructure cost ratio

**Metas Propostas**
- Redução de X% em compute
- Aumento de Y% em cobertura RI
- Migração de Z workloads para serverless

#### 7. PRÓXIMOS PASSOS

- Decisões que precisam de aprovação
- Recursos necessários (equipe, tempo)
- Dependências e riscos técnicos
- Cronograma proposto

### Diretrizes Adicionais

- 2-3 páginas
- Inclua diagramas conceituais em texto quando útil
- Balance profundidade técnica com clareza executiva
- Sempre apresente alternativas com pros/cons
- Quantifique impactos sempre que possível
"""
