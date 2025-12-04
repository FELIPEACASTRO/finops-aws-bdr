# FinOps Framework

Este documento descreve o Framework FinOps e como aplicá-lo
na análise de custos AWS.

## O que é FinOps?

FinOps (Financial Operations) é uma prática de gerenciamento financeiro 
em nuvem que combina sistemas, melhores práticas e cultura para aumentar 
a capacidade de uma organização entender os custos de cloud, tomar 
decisões baseadas em dados e gerar valor de negócio.

## Os Três Pilares do FinOps

### 1. Inform (Informar)

**Objetivo**: Criar visibilidade e entendimento dos custos

**Práticas**:
- Alocação precisa de custos (tagging)
- Showback/Chargeback para equipes
- Dashboards em tempo real
- Relatórios de tendências

**Métricas-chave**:
- Custo por serviço/aplicação
- Custo por ambiente
- Custo por equipe/centro de custo
- Tendência MoM e YoY

### 2. Optimize (Otimizar)

**Objetivo**: Reduzir custos e melhorar eficiência

**Práticas**:
- Right-sizing de recursos
- Compra de compromissos (RI, SP)
- Uso de Spot/Preemptible
- Eliminação de waste

**Métricas-chave**:
- Cobertura de RI/Savings Plans
- Waste ratio (recursos ociosos)
- Custo unitário (por transação, usuário)
- Economia capturada vs potencial

### 3. Operate (Operar)

**Objetivo**: Governança contínua e melhoria

**Práticas**:
- Budgets e alertas
- Políticas de governança
- Automação de otimização
- Revisões periódicas

**Métricas-chave**:
- Precisão de forecast
- Aderência ao budget
- Tempo para resolver anomalias
- Maturidade FinOps

## Modelo de Maturidade FinOps

### Crawl (Engatinhar)

**Características**:
- Visibilidade básica de custos
- Tagging parcial
- Reação a problemas
- Análise manual

**Ações Prioritárias**:
1. Implementar tagging obrigatório
2. Configurar Cost Explorer
3. Criar alertas de budget
4. Identificar quick wins

### Walk (Andar)

**Características**:
- Alocação completa de custos
- Showback ativo
- Otimização regular
- KPIs definidos

**Ações Prioritárias**:
1. Implementar showback por equipe
2. Comprar Reserved/Savings Plans
3. Automatizar relatórios
4. Definir metas de economia

### Run (Correr)

**Características**:
- FinOps as Code
- Previsão precisa
- Otimização contínua
- Cultura de custo

**Ações Prioritárias**:
1. Automação de otimização
2. Chargeback completo
3. Integração com CI/CD
4. Benchmarking externo

## Domínios FinOps

### 1. Entendimento do Uso e Custo

**Alocação de Custos**:
- Custos diretos (recursos com tag)
- Custos compartilhados (como alocar?)
- Custos não alocados (meta: < 5%)

**Estratégia de Tagging**:
```
Obrigatórias:
  - Environment: prod|staging|dev|sandbox
  - Owner: equipe responsável
  - CostCenter: centro de custo
  - Application: nome da aplicação

Recomendadas:
  - Project: projeto específico
  - BusinessUnit: unidade de negócio
  - Compliance: requisitos regulatórios
```

### 2. Otimização de Taxa

**Compromissos**:
- Reserved Instances: economia até 72%
- Savings Plans: flexibilidade + economia
- Spot Instances: economia até 90%

**Cobertura Ideal**:
| Tipo de Workload | Cobertura Recomendada |
|------------------|----------------------|
| Produção estável | 70-80% RI/SP |
| Produção variável | 50-60% SP Compute |
| Dev/Staging | On-Demand + Spot |
| Batch/CI-CD | 90%+ Spot |

### 3. Otimização de Uso

**Rightsizing**:
- Análise de utilização (CPU, memória, I/O)
- Recomendações de Compute Optimizer
- Migração para Graviton

**Eliminação de Waste**:
- Recursos ociosos (0% utilização)
- Recursos subutilizados (< 10%)
- Recursos órfãos (EBS, EIP, snapshots)

### 4. Planejamento e Previsão

**Orçamento**:
- Budget anual por serviço
- Budget mensal por equipe
- Reserva para crescimento (10-20%)

**Forecast**:
- Baseline histórico
- Ajuste por sazonalidade
- Consideração de projetos futuros

### 5. Cloud Policy e Governança

**Políticas Recomendadas**:

```yaml
Política de Tagging:
  - Recursos sem tags: alerta após 24h, deleção após 7d

Política de Aprovação:
  - Instâncias > $1000/mês: aprovação de gerente
  - Instâncias > $5000/mês: aprovação de diretor
  - Reserved Instances: aprovação de FinOps

Política de Ambiente:
  - Dev/Staging: desligamento automático 20h-8h
  - Sandbox: deleção automática após 7 dias
  - Produção: monitoramento 24/7
```

### 6. Decisões em Tempo Real

**Gatilhos de Ação**:
- Anomalia de custo > 20%: investigação imediata
- Utilização < 10% por 7 dias: candidato a rightsizing
- RI expirando em 30 dias: revisão de renovação

## KPIs FinOps Essenciais

### Eficiência

| KPI | Fórmula | Meta |
|-----|---------|------|
| Cobertura RI/SP | Horas cobertas / Total horas | > 70% |
| Utilização RI | Horas usadas / Horas compradas | > 90% |
| Waste Ratio | Custo ocioso / Custo total | < 5% |

### Financeiro

| KPI | Fórmula | Meta |
|-----|---------|------|
| Unit Economics | Custo / Unidade de negócio | Decrescente |
| Forecast Accuracy | 1 - |Forecast - Actual| / Actual | > 90% |
| Budget Variance | (Actual - Budget) / Budget | ±10% |

### Operacional

| KPI | Fórmula | Meta |
|-----|---------|------|
| Tag Compliance | Recursos com tags / Total | > 95% |
| Anomaly Response Time | Tempo para resolver | < 24h |
| Optimization Adoption | Recomendações implementadas | > 60% |

## Ciclo de Melhoria Contínua

```
    ┌──────────────────────┐
    │     ANALISAR         │
    │  (Custos e Uso)      │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │    IDENTIFICAR       │
    │  (Oportunidades)     │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │     PRIORIZAR        │
    │  (Por ROI/Esforço)   │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │    IMPLEMENTAR       │
    │  (Otimizações)       │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │     VALIDAR          │
    │  (Economia Real)     │
    └──────────┬───────────┘
               │
               └──────────────► (Repetir)
```

## Estrutura Organizacional

### FinOps Team (Centro de Excelência)

**Responsabilidades**:
- Definir políticas e padrões
- Ferramentas e automação
- Treinamento e capacitação
- Relatórios executivos

### Cloud Teams (Execução)

**Responsabilidades**:
- Implementar otimizações
- Taggar recursos corretamente
- Responder a anomalias
- Propor melhorias

### Liderança (Patrocínio)

**Responsabilidades**:
- Aprovar investimentos (RI/SP)
- Definir metas de economia
- Cultura de custo
- Accountability
