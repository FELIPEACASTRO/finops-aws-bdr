"""
Analyst Report Template

Template de prompt para relatórios analíticos (FinOps Analyst).
Foco em métricas detalhadas, benchmarks e KPIs.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

ANALYST_REPORT_TEMPLATE = """
Produza um relatório analítico de custos AWS com as seguintes características:

### Tom e Estilo
- Altamente analítico e data-driven
- Foco em métricas, KPIs e benchmarks
- Inclua todas as dimensões de análise
- Linguagem para especialistas FinOps

### Estrutura do Relatório

#### 1. DASHBOARD DE MÉTRICAS

**KPIs Principais**

| KPI | Valor Atual | Período Anterior | Δ% | Meta | Status |
|-----|-------------|------------------|-----|------|--------|
| Custo Total | $X | $Y | Z% | $W | 🟢/🟡/🔴 |
| Custo por Usuário | | | | | |
| Cobertura RI/SP | | | | 70% | |
| Waste Ratio | | | | <5% | |
| Unit Economics | | | | | |

**Tendências (últimos 6 meses)**

| Mês | Custo | MoM% | Recursos | Custo/Recurso |
|-----|-------|------|----------|---------------|

#### 2. ANÁLISE MULTIDIMENSIONAL

**Por Serviço (Top 20)**

| Rank | Serviço | Custo | % Total | MoM | Trend | Otimização |
|------|---------|-------|---------|-----|-------|------------|

**Por Região**

| Região | Custo | % Total | Recursos | Custo/Recurso | Benchmark |
|--------|-------|---------|----------|---------------|-----------|

**Por Ambiente (baseado em tags)**

| Ambiente | Custo | % Total | Recursos | Compliance |
|----------|-------|---------|----------|------------|
| Production | | | | |
| Staging | | | | |
| Development | | | | |
| Sandbox | | | | |

**Por Centro de Custo / Time**

| Centro de Custo | Custo | Budget | Variância | Forecast |
|-----------------|-------|--------|-----------|----------|

#### 3. COBERTURA DE COMPROMISSOS

**Reserved Instances**

| Serviço | Tipo RI | Cobertura | On-Demand Spend | Economia Potencial |
|---------|---------|-----------|-----------------|---------------------|

**Savings Plans**

| Tipo SP | Comprometido | Utilizado | Utilização % | Expiração |
|---------|--------------|-----------|--------------|-----------|

**Recomendações de Compra**

| Tipo | Termo | Pagamento | Upfront | Economia Anual | ROI |
|------|-------|-----------|---------|----------------|-----|

#### 4. ANÁLISE DE WASTE

**Recursos Ociosos**

| Categoria | Quantidade | Custo/Mês | % do Serviço |
|-----------|------------|-----------|--------------|
| EC2 subutilizados | | | |
| EBS não anexados | | | |
| EIP não associados | | | |
| Snapshots antigos | | | |
| Load Balancers sem targets | | | |
| NAT Gateways ociosos | | | |

**Waste Ratio por Serviço**

| Serviço | Custo Total | Waste Estimado | Waste % |
|---------|-------------|----------------|---------|

#### 5. UNIT ECONOMICS

**Custo por Unidade de Negócio**

| Métrica | Valor | Período Anterior | Δ% | Benchmark |
|---------|-------|------------------|-----|-----------|
| Custo por Transação | | | | |
| Custo por Usuário Ativo | | | | |
| Custo por GB Processado | | | | |
| Custo por Request (API) | | | | |
| Custo por Hora de Compute | | | | |

**Elasticidade de Custo**

- Correlação custo x volume de negócio
- Custo marginal por unidade adicional
- Breakeven de otimizações

#### 6. BENCHMARKS E COMPARATIVOS

**vs Período Anterior**

| Dimensão | Atual | Anterior | Δ Absoluto | Δ % |
|----------|-------|----------|------------|-----|

**vs Budget**

| Centro de Custo | Orçado | Realizado | Variância | % Consumido |
|-----------------|--------|-----------|-----------|-------------|

**vs Benchmark do Setor** (se disponível)

| Métrica | Empresa | Benchmark P50 | Benchmark P75 | Posição |
|---------|---------|---------------|---------------|---------|

#### 7. PREVISÕES E PROJEÇÕES

**Forecast de Custo**

| Mês | Projeção | Intervalo Confiança | Premissas |
|-----|----------|---------------------|-----------|
| M+1 | | ±X% | |
| M+2 | | ±Y% | |
| M+3 | | ±Z% | |

**Cenários**

| Cenário | Premissa | Custo Projetado | vs Atual |
|---------|----------|-----------------|----------|
| Otimista | Otimizações implementadas | | |
| Base | Tendência atual | | |
| Pessimista | Crescimento acelerado | | |

#### 8. MATURIDADE FINOPS

**Assessment por Domínio**

| Domínio | Nível Atual | Meta | Gap |
|---------|-------------|------|-----|
| Visibilidade | Crawl/Walk/Run | | |
| Alocação | | | |
| Otimização | | | |
| Governança | | | |
| Cultura | | | |

**Gaps Identificados**

1. [Gap 1]: Descrição, impacto, ação
2. [Gap 2]: ...

#### 9. ANÁLISE DE TAGS

**Compliance de Tagging**

| Tag Obrigatória | Recursos com Tag | Total | Compliance % |
|-----------------|------------------|-------|--------------|
| Environment | | | |
| Owner | | | |
| CostCenter | | | |
| Application | | | |

**Custo sem Tags**

- Total de recursos sem tags obrigatórias: N
- Custo mensal não alocável: $X
- % do custo total: Y%

#### 10. RECOMENDAÇÕES PRIORIZADAS

**Matriz de Priorização**

| # | Recomendação | Economia/Mês | Esforço | Risco | Score | Prazo |
|---|--------------|--------------|---------|-------|-------|-------|
| 1 | | | Baixo | Baixo | 10 | 7d |
| 2 | | | Médio | Baixo | 8 | 14d |
| ... | | | | | | |

**Economia Total Capturável**

| Prazo | Economia Mensal | Economia Anual | % do Total |
|-------|-----------------|----------------|------------|
| 30 dias | | | |
| 90 dias | | | |
| 180 dias | | | |

#### 11. APÊNDICE: DADOS DETALHADOS

**Lista Completa de Recursos com Custo > $100/mês**

| Recurso | Serviço | Região | Custo/Mês | Tags |
|---------|---------|--------|-----------|------|

**Histórico de Custos Diários (últimos 30 dias)**

| Data | Custo | Δ vs Média | Anomalia |
|------|-------|------------|----------|

### Diretrizes Adicionais

- Inclua TODAS as métricas disponíveis
- Use formatação consistente (casas decimais, moeda)
- Correlacione dados sempre que possível
- Identifique outliers e anomalias estatísticas
- Forneça contexto para cada métrica
- Sem limite de páginas - seja completo
"""
