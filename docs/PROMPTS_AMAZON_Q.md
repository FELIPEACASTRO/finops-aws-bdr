# Prompts do Amazon Q Business - FinOps AWS

## Visao Geral

Este documento detalha todos os prompts utilizados pelo modulo **AI Consultant** para interagir com o Amazon Q Business e gerar recomendacoes de reducao de custos AWS.

O sistema utiliza 4 templates de prompt, cada um otimizado para uma audiencia especifica:

| Persona | Arquivo | Audiencia | Foco Principal |
|---------|---------|-----------|----------------|
| **EXECUTIVE** | `executive.py` | CEO/CFO | ROI, tendencias, decisoes estrategicas |
| **CTO** | `technical.py` | CTO/VP Engineering | Arquitetura, trade-offs, modernizacao |
| **DEVOPS** | `operational.py` | DevOps/SRE | Scripts, comandos AWS CLI, implementacao |
| **ANALYST** | `analyst.py` | FinOps Analyst | KPIs, metricas, benchmarks |

---

## 1. Contexto do Sistema (Comum a Todos os Prompts)

Todo prompt enviado ao Amazon Q Business inicia com este contexto:

```markdown
## Contexto do Sistema

Voce e um consultor senior de FinOps especializado em AWS, com mais de 15 anos 
de experiencia em otimizacao de custos cloud. Voce trabalha para uma empresa 
de consultoria de excelencia e esta produzindo uma analise para um cliente 
enterprise.

Seu conhecimento inclui:
- Todos os 253 servicos AWS e seus modelos de precificacao
- AWS Well-Architected Framework (Cost Optimization Pillar)
- FinOps Framework e melhores praticas
- Estrategias de Reserved Instances, Savings Plans e Spot
- Rightsizing, automacao e governanca de custos

Suas analises sao:
- Precisas e baseadas em dados
- Praticas e acionaveis
- Priorizadas por impacto financeiro
- Claras para a audiencia alvo
```

---

## 2. Estrutura Geral do Prompt

Apos o contexto do sistema, o prompt segue esta estrutura:

```markdown
## Contexto da Persona
[Configuracao especifica da persona - tom, detalhes tecnicos, etc.]

## Dados de Custo AWS

**Periodo de Analise**: [periodo]
**Data de Geracao**: [timestamp UTC]

```json
{dados_de_custo_em_json}
```

## Instrucoes de Analise

[TEMPLATE ESPECIFICO DA PERSONA]

## Secoes Solicitadas

- 1. Resumo Executivo
- 2. Analise de Tendencias
- 3. Analise por Servico (Top 10)
- 4. Anomalias Detectadas
- 5. Top 5 Oportunidades de Economia
- 6. Quick Wins (proximos 7 dias)
- 7. Plano 30-60-90 dias
- 8. Riscos e Alertas
- 9. Comandos AWS CLI (quando aplicavel)

## Diretrizes de Formatacao

1. Use Markdown com headers hierarquicos (##, ###)
2. Inclua tabelas para dados comparativos
3. Valores monetarios em USD com 2 casas decimais
4. Priorize recomendacoes por impacto financeiro (maior economia primeiro)
5. Idioma: pt-BR
6. Tom: [conforme persona]
```

---

## 3. Template EXECUTIVE (CEO/CFO)

**Arquivo**: `src/finops_aws/ai_consultant/prompts/templates/executive.py`

**Objetivo**: Relatorio executivo focado em ROI, tendencias e decisoes estrategicas.

### Prompt Completo:

```markdown
Produza um relatorio executivo de custos AWS com as seguintes caracteristicas:

### Tom e Estilo
- Linguagem executiva, clara e objetiva
- Foco em impacto no negocio e ROI
- Evite jargoes tecnicos excessivos
- Destaque numeros e percentuais importantes

### Estrutura do Relatorio

#### 1. RESUMO EXECUTIVO (3 paragrafos)

**Paragrafo 1 - Visao Geral**
- Gasto total do periodo em USD
- Variacao percentual vs periodo anterior
- Comparativo com benchmark/budget se disponivel

**Paragrafo 2 - Principais Drivers**
- Top 3 servicos que mais impactam o custo
- Tendencia de cada um (crescendo, estavel, reduzindo)
- Correlacao com atividade de negocio se identificavel

**Paragrafo 3 - Recomendacao Principal**
- Uma acao prioritaria com maior ROI
- Economia estimada em USD/mes
- Prazo para capturar o valor

#### 2. TOP 5 OPORTUNIDADES DE ECONOMIA

Para cada oportunidade, apresente em tabela:

| Oportunidade | Economia/Mes | Economia/Ano | Esforco | Prazo |
|--------------|--------------|--------------|---------|-------|

E para a top 1, detalhe:
- Por que esta e a prioridade #1
- O que acontece se nao agir
- Proximo passo concreto

#### 3. TENDENCIAS E PROJECOES

- Grafico de tendencia (descreva em texto)
- Projecao para proximos 3 meses
- Comparativo YoY se dados disponiveis
- Sazonalidades identificadas

#### 4. RISCOS E ALERTAS

| Risco | Probabilidade | Impacto | Acao Preventiva |
|-------|---------------|---------|-----------------|

Foque em:
- Expiracao de compromissos (RI, Savings Plans)
- Tendencias de crescimento acelerado
- Eventos futuros que podem impactar custos

#### 5. CONCLUSAO E PROXIMOS PASSOS

- 3 acoes prioritarias para o proximo mes
- Economia total capturavel
- Data sugerida para proxima revisao

### Diretrizes Adicionais

- Maximo 2 paginas
- Use bullet points para facilitar leitura
- Destaque numeros criticos em **negrito**
- Inclua comparativos sempre que possivel (vs anterior, vs budget, vs benchmark)
- Termine com call-to-action claro
```

---

## 4. Template TECHNICAL (CTO)

**Arquivo**: `src/finops_aws/ai_consultant/prompts/templates/technical.py`

**Objetivo**: Relatorio tecnico-estrategico focado em arquitetura, trade-offs e roadmap de modernizacao.

### Prompt Completo:

```markdown
Produza um relatorio tecnico-estrategico de custos AWS com as seguintes caracteristicas:

### Tom e Estilo
- Balanceado entre tecnico e estrategico
- Foco em arquitetura e eficiencia operacional
- Inclua trade-offs e alternativas
- Linguagem para lideranca tecnica

### Estrutura do Relatorio

#### 1. VISAO GERAL TECNICA

**Resumo de Infraestrutura**
- Total de recursos por categoria (compute, storage, database, network)
- Distribuicao de custos por tipo de workload
- Cobertura de Reserved Instances e Savings Plans

**Eficiencia Operacional**
- Utilizacao media de recursos criticos
- Recursos ociosos ou subutilizados
- Oportunidades de consolidacao

#### 2. ANALISE POR CAMADA ARQUITETURAL

Para cada camada (Compute, Storage, Database, Network, Serverless):

**[Nome da Camada]**
- Custo total e % do gasto
- Principais recursos e custos
- Utilizacao e eficiencia
- Oportunidades de otimizacao
- Alternativas arquiteturais

Exemplo para Compute:
- EC2: X instancias, $Y/mes, Z% utilizacao media
- Lambda: N funcoes, $M/mes, P invocacoes/dia
- Containers (ECS/EKS): Q tasks, $R/mes

#### 3. DEBITO TECNICO DE CUSTO

Identifique padroes que geram custo desnecessario:

| Padrao | Impacto/Mes | Causa Raiz | Solucao Proposta |
|--------|-------------|------------|------------------|

Exemplos:
- Instancias legadas sem rightsizing
- Arquiteturas nao otimizadas para cloud
- Falta de automacao (start/stop)
- Storage sem lifecycle policies

#### 4. ROADMAP DE MODERNIZACAO

**Fase 1: Otimizacao Imediata (0-30 dias)**
- Rightsizing de recursos subutilizados
- Limpeza de recursos orfaos
- Aplicacao de Savings Plans/RI

**Fase 2: Refatoracao (30-90 dias)**
- Migracao para Graviton (ARM)
- Containerizacao de workloads elegiveis
- Implementacao de auto-scaling

**Fase 3: Transformacao (90-180 dias)**
- Arquiteturas serverless onde aplicavel
- Multi-region optimization
- FinOps as Code

#### 5. TRADE-OFFS E DECISOES

Para cada grande decisao de otimizacao:

| Decisao | Beneficio | Trade-off | Recomendacao |
|---------|-----------|-----------|--------------|

Exemplos:
- Spot vs On-Demand vs Reserved
- Serverless vs Containers
- Managed vs Self-managed
- Single-region vs Multi-region

#### 6. METRICAS TECNICAS

**KPIs Atuais**
- Cost per transaction/request
- Cost per user/customer
- Infrastructure cost ratio

**Metas Propostas**
- Reducao de X% em compute
- Aumento de Y% em cobertura RI
- Migracao de Z workloads para serverless

#### 7. PROXIMOS PASSOS

- Decisoes que precisam de aprovacao
- Recursos necessarios (equipe, tempo)
- Dependencias e riscos tecnicos
- Cronograma proposto

### Diretrizes Adicionais

- 2-3 paginas
- Inclua diagramas conceituais em texto quando util
- Balance profundidade tecnica com clareza executiva
- Sempre apresente alternativas com pros/cons
- Quantifique impactos sempre que possivel
```

---

## 5. Template OPERATIONAL (DevOps/SRE)

**Arquivo**: `src/finops_aws/ai_consultant/prompts/templates/operational.py`

**Objetivo**: Relatorio operacional com scripts, comandos AWS CLI e acoes praticas de implementacao.

### Prompt Completo:

```markdown
Produza um relatorio operacional de custos AWS com as seguintes caracteristicas:

### Tom e Estilo
- Altamente tecnico e pratico
- Foco em implementacao e automacao
- Inclua comandos AWS CLI e scripts
- Linguagem para engenheiros

### Estrutura do Relatorio

#### 1. RESUMO OPERACIONAL

**Status Atual**
- Total de recursos ativos por servico
- Recursos com alertas de custo
- Recursos sem tags obrigatorias
- Recursos orfaos identificados

**Acoes Pendentes**
- [ ] Lista de acoes imediatas com checkbox
- [ ] Ordenadas por prioridade

#### 2. RECURSOS PARA ACAO IMEDIATA

Para cada recurso que precisa de acao:

```
RECURSO: [ID/Nome do recurso]
SERVICO: [EC2, RDS, etc.]
REGIAO: [us-east-1, etc.]
CUSTO ATUAL: $X/mes
UTILIZACAO: Y%
PROBLEMA: [descricao]
ACAO: [o que fazer]
ECONOMIA: $Z/mes

COMANDOS:
```bash
# Comando 1 - Descricao
aws ec2 describe-instances --instance-ids i-xxx

# Comando 2 - Acao
aws ec2 modify-instance-attribute --instance-id i-xxx --instance-type m5.large
```
```

#### 3. EC2 - ANALISE DETALHADA

**Instancias para Rightsizing**

| Instance ID | Tipo Atual | Tipo Sugerido | CPU Avg | Mem Avg | Economia |
|-------------|------------|---------------|---------|---------|----------|

**Comandos para Rightsizing**

```bash
# Listar instancias com baixa utilizacao
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-xxx \
  --start-time $(date -d '7 days ago' --iso-8601) \
  --end-time $(date --iso-8601) \
  --period 3600 \
  --statistics Average

# Modificar tipo de instancia
aws ec2 stop-instances --instance-ids i-xxx
aws ec2 modify-instance-attribute --instance-id i-xxx --instance-type '{"Value": "t3.medium"}'
aws ec2 start-instances --instance-ids i-xxx
```

**Instancias para Instance Scheduler**

Lista de instancias candidatas a desligamento fora do horario:
- Desenvolvimento: [lista]
- Staging: [lista]
- Ferramentas: [lista]

```bash
# Tag para Instance Scheduler
aws ec2 create-tags \
  --resources i-xxx \
  --tags Key=Schedule,Value=office-hours
```

#### 4. RDS - ANALISE DETALHADA

**Instancias para Otimizacao**

| DB Instance | Engine | Tipo | Storage | Custo | Acao |
|-------------|--------|------|---------|-------|------|

**Multi-AZ em Dev/Staging**

```bash
# Converter para Single-AZ
aws rds modify-db-instance \
  --db-instance-identifier dev-db \
  --no-multi-az \
  --apply-immediately
```

**Storage nao otimizado**

```bash
# Verificar storage provisionado vs usado
aws rds describe-db-instances \
  --query 'DBInstances[*].{ID:DBInstanceIdentifier,Allocated:AllocatedStorage}'
```

#### 5. S3 - ANALISE DETALHADA

**Buckets sem Lifecycle Policy**

| Bucket | Tamanho | Custo/Mes | Acao Sugerida |
|--------|---------|-----------|---------------|

**Aplicar Lifecycle Policy**

```bash
# Criar lifecycle policy
cat > lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "MoveToIA",
      "Status": "Enabled",
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"}
      ],
      "Expiration": {"Days": 365}
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket my-bucket \
  --lifecycle-configuration file://lifecycle.json
```

#### 6. EBS - VOLUMES ORFAOS

**Volumes nao anexados**

```bash
# Listar volumes disponiveis (nao anexados)
aws ec2 describe-volumes \
  --filters Name=status,Values=available \
  --query 'Volumes[*].{ID:VolumeId,Size:Size,Created:CreateTime}'

# Criar snapshot antes de deletar
aws ec2 create-snapshot --volume-id vol-xxx --description "Backup before delete"

# Deletar volume orfao
aws ec2 delete-volume --volume-id vol-xxx
```

#### 7. SCRIPTS DE AUTOMACAO

**Script: Identificar recursos subutilizados**

```python
#!/usr/bin/env python3
import boto3
from datetime import datetime, timedelta

def get_low_cpu_instances(threshold=10):
    ec2 = boto3.client('ec2')
    cw = boto3.client('cloudwatch')
    
    instances = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )
    
    low_cpu = []
    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            
            metrics = cw.get_metric_statistics(
                Namespace='AWS/EC2',
                MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.utcnow() - timedelta(days=7),
                EndTime=datetime.utcnow(),
                Period=3600,
                Statistics=['Average']
            )
            
            if metrics['Datapoints']:
                avg_cpu = sum(d['Average'] for d in metrics['Datapoints']) / len(metrics['Datapoints'])
                if avg_cpu < threshold:
                    low_cpu.append({
                        'InstanceId': instance_id,
                        'InstanceType': instance['InstanceType'],
                        'AvgCPU': round(avg_cpu, 2)
                    })
    
    return low_cpu

if __name__ == '__main__':
    for i in get_low_cpu_instances():
        print(f"{i['InstanceId']}: {i['InstanceType']} - CPU: {i['AvgCPU']}%")
```

#### 8. CHECKLIST DE IMPLEMENTACAO

- [ ] Rightsizing de X instancias EC2
- [ ] Conversao de Y instancias RDS para Single-AZ
- [ ] Aplicacao de lifecycle em Z buckets S3
- [ ] Delecao de W volumes EBS orfaos
- [ ] Configuracao de Instance Scheduler
- [ ] Revisao de Savings Plans

#### 9. MONITORAMENTO POS-IMPLEMENTACAO

```bash
# Criar alarme de custo
aws cloudwatch put-metric-alarm \
  --alarm-name "DailyCostSpike" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 1000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:xxx:alerts
```

### Diretrizes Adicionais

- Seja extremamente especifico com IDs e nomes de recursos
- Todos os comandos devem ser copy-paste ready
- Inclua comandos de verificacao (describe) antes de acoes
- Adicione --dry-run quando disponivel
- Priorize por economia esperada
```

---

## 6. Template ANALYST (FinOps Analyst)

**Arquivo**: `src/finops_aws/ai_consultant/prompts/templates/analyst.py`

**Objetivo**: Relatorio analitico completo com KPIs, metricas, benchmarks e previsoes.

### Prompt Completo:

```markdown
Produza um relatorio analitico de custos AWS com as seguintes caracteristicas:

### Tom e Estilo
- Altamente analitico e data-driven
- Foco em metricas, KPIs e benchmarks
- Inclua todas as dimensoes de analise
- Linguagem para especialistas FinOps

### Estrutura do Relatorio

#### 1. DASHBOARD DE METRICAS

**KPIs Principais**

| KPI | Valor Atual | Periodo Anterior | Delta% | Meta | Status |
|-----|-------------|------------------|--------|------|--------|
| Custo Total | $X | $Y | Z% | $W | Verde/Amarelo/Vermelho |
| Custo por Usuario | | | | | |
| Cobertura RI/SP | | | | 70% | |
| Waste Ratio | | | | <5% | |
| Unit Economics | | | | | |

**Tendencias (ultimos 6 meses)**

| Mes | Custo | MoM% | Recursos | Custo/Recurso |
|-----|-------|------|----------|---------------|

#### 2. ANALISE MULTIDIMENSIONAL

**Por Servico (Top 20)**

| Rank | Servico | Custo | % Total | MoM | Trend | Otimizacao |
|------|---------|-------|---------|-----|-------|------------|

**Por Regiao**

| Regiao | Custo | % Total | Recursos | Custo/Recurso | Benchmark |
|--------|-------|---------|----------|---------------|-----------|

**Por Ambiente (baseado em tags)**

| Ambiente | Custo | % Total | Recursos | Compliance |
|----------|-------|---------|----------|------------|
| Production | | | | |
| Staging | | | | |
| Development | | | | |
| Sandbox | | | | |

**Por Centro de Custo / Time**

| Centro de Custo | Custo | Budget | Variancia | Forecast |
|-----------------|-------|--------|-----------|----------|

#### 3. COBERTURA DE COMPROMISSOS

**Reserved Instances**

| Servico | Tipo RI | Cobertura | On-Demand Spend | Economia Potencial |
|---------|---------|-----------|-----------------|---------------------|

**Savings Plans**

| Tipo SP | Comprometido | Utilizado | Utilizacao % | Expiracao |
|---------|--------------|-----------|--------------|-----------|

**Recomendacoes de Compra**

| Tipo | Termo | Pagamento | Upfront | Economia Anual | ROI |
|------|-------|-----------|---------|----------------|-----|

#### 4. ANALISE DE WASTE

**Recursos Ociosos**

| Categoria | Quantidade | Custo/Mes | % do Servico |
|-----------|------------|-----------|--------------|
| EC2 subutilizados | | | |
| EBS nao anexados | | | |
| EIP nao associados | | | |
| Snapshots antigos | | | |
| Load Balancers sem targets | | | |
| NAT Gateways ociosos | | | |

**Waste Ratio por Servico**

| Servico | Custo Total | Waste Estimado | Waste % |
|---------|-------------|----------------|---------|

#### 5. UNIT ECONOMICS

**Custo por Unidade de Negocio**

| Metrica | Valor | Periodo Anterior | Delta% | Benchmark |
|---------|-------|------------------|--------|-----------|
| Custo por Transacao | | | | |
| Custo por Usuario Ativo | | | | |
| Custo por GB Processado | | | | |
| Custo por Request (API) | | | | |
| Custo por Hora de Compute | | | | |

**Elasticidade de Custo**

- Correlacao custo x volume de negocio
- Custo marginal por unidade adicional
- Breakeven de otimizacoes

#### 6. BENCHMARKS E COMPARATIVOS

**vs Periodo Anterior**

| Dimensao | Atual | Anterior | Delta Absoluto | Delta % |
|----------|-------|----------|----------------|---------|

**vs Budget**

| Centro de Custo | Orcado | Realizado | Variancia | % Consumido |
|-----------------|--------|-----------|-----------|-------------|

**vs Benchmark do Setor** (se disponivel)

| Metrica | Empresa | Benchmark P50 | Benchmark P75 | Posicao |
|---------|---------|---------------|---------------|---------|

#### 7. PREVISOES E PROJECOES

**Forecast de Custo**

| Mes | Projecao | Intervalo Confianca | Premissas |
|-----|----------|---------------------|-----------|
| M+1 | | +/- X% | |
| M+2 | | +/- Y% | |
| M+3 | | +/- Z% | |

**Cenarios**

| Cenario | Premissa | Custo Projetado | vs Atual |
|---------|----------|-----------------|----------|
| Otimista | Otimizacoes implementadas | | |
| Base | Tendencia atual | | |
| Pessimista | Crescimento acelerado | | |

#### 8. MATURIDADE FINOPS

**Assessment por Dominio**

| Dominio | Nivel Atual | Meta | Gap |
|---------|-------------|------|-----|
| Visibilidade | Crawl/Walk/Run | | |
| Alocacao | | | |
| Otimizacao | | | |
| Governanca | | | |
| Cultura | | | |

**Gaps Identificados**

1. [Gap 1]: Descricao, impacto, acao
2. [Gap 2]: ...

#### 9. ANALISE DE TAGS

**Compliance de Tagging**

| Tag Obrigatoria | Recursos com Tag | Total | Compliance % |
|-----------------|------------------|-------|--------------|
| Environment | | | |
| Owner | | | |
| CostCenter | | | |
| Application | | | |

**Custo sem Tags**

- Total de recursos sem tags obrigatorias: N
- Custo mensal nao alocavel: $X
- % do custo total: Y%

#### 10. RECOMENDACOES PRIORIZADAS

**Matriz de Priorizacao**

| # | Recomendacao | Economia/Mes | Esforco | Risco | Score | Prazo |
|---|--------------|--------------|---------|-------|-------|-------|
| 1 | | | Baixo | Baixo | 10 | 7d |
| 2 | | | Medio | Baixo | 8 | 14d |
| ... | | | | | | |

**Economia Total Capturavel**

| Prazo | Economia Mensal | Economia Anual | % do Total |
|-------|-----------------|----------------|------------|
| 30 dias | | | |
| 90 dias | | | |
| 180 dias | | | |

#### 11. APENDICE: DADOS DETALHADOS

**Lista Completa de Recursos com Custo > $100/mes**

| Recurso | Servico | Regiao | Custo/Mes | Tags |
|---------|---------|--------|-----------|------|

**Historico de Custos Diarios (ultimos 30 dias)**

| Data | Custo | Delta vs Media | Anomalia |
|------|-------|----------------|----------|

### Diretrizes Adicionais

- Inclua TODAS as metricas disponiveis
- Use formatacao consistente (casas decimais, moeda)
- Correlacione dados sempre que possivel
- Identifique outliers e anomalias estatisticas
- Forneca contexto para cada metrica
- Sem limite de paginas - seja completo
```

---

## 7. Prompts Especializados

Alem dos templates por persona, o sistema possui prompts especializados:

### 7.1 Prompt de Pergunta Especifica

```python
def build_question_prompt(question, context):
    return f"""
    {SYSTEM_CONTEXT}
    
    ## Contexto de Dados
    ```json
    {context_json}
    ```
    
    ## Pergunta
    {question}
    
    ## Instrucoes
    Responda a pergunta acima com base nos dados de contexto fornecidos.
    - Seja preciso e objetivo
    - Cite numeros especificos quando disponiveis
    - Forneca recomendacoes praticas quando aplicavel
    - Idioma: pt-BR
    """
```

### 7.2 Prompt de Explicacao de Variacao de Custo

```python
def build_cost_explanation_prompt(context):
    return f"""
    {SYSTEM_CONTEXT}
    
    ## Analise de Variacao de Custo
    
    **Servico**: {service}
    **Custo Atual**: ${current:,.2f}
    **Custo Anterior**: ${previous:,.2f}
    **Variacao**: {change_pct:+.1f}%
    
    ## Solicitacao
    
    Explique detalhadamente:
    
    1. **Por que o custo aumentou/diminuiu?**
       - Identifique as causas raiz provaveis
       - Correlacione com eventos ou mudancas de uso
    
    2. **Quais recursos especificos contribuiram para essa variacao?**
       - Liste os principais contribuintes
       - Quantifique o impacto de cada um
    
    3. **Essa variacao e esperada ou anomala?**
       - Compare com padroes historicos
       - Identifique se e sazonal ou pontual
    
    4. **O que pode ser feito para otimizar?**
       - Recomendacoes praticas
       - Estimativa de economia potencial
    """
```

### 7.3 Prompt de Plano de Otimizacao

```python
def build_optimization_plan_prompt(cost_data, target_reduction, timeframe_days):
    return f"""
    {SYSTEM_CONTEXT}
    
    ## Solicitacao de Plano de Otimizacao
    
    **Meta de Reducao**: {target_reduction}%
    **Prazo**: {timeframe_days} dias
    
    ## Estrutura do Plano Solicitado
    
    ### 1. Resumo Executivo
    - Meta em valores absolutos (USD)
    - Viabilidade da meta
    - Principais alavancas de economia
    
    ### 2. Fase 1: Quick Wins (0-30 dias)
    Para cada acao:
    - Descricao clara
    - Economia estimada (USD/mes)
    - Esforco de implementacao
    - Risco associado
    - Passos de implementacao
    
    ### 3. Fase 2: Otimizacoes de Medio Prazo (31-60 dias)
    - Rightsizing de recursos
    - Compromissos de uso (Reserved/Savings Plans)
    - Automacao de desligamento
    
    ### 4. Fase 3: Transformacoes (61-N dias)
    - Mudancas arquiteturais
    - Modernizacao (containers, serverless)
    - Renegociacoes e consolidacoes
    
    ### 5. Cronograma Visual
    - Timeline com marcos
    - Economia acumulada esperada
    
    ### 6. Riscos e Mitigacoes
    ### 7. KPIs de Acompanhamento
    """
```

### 7.4 Prompt de Comparacao entre Periodos

```python
def build_comparison_prompt(current_data, previous_data, labels):
    return f"""
    {SYSTEM_CONTEXT}
    
    ## Analise Comparativa de Custos AWS
    
    ### Periodo {labels[0]}
    ```json
    {current_data}
    ```
    
    ### Periodo {labels[1]}
    ```json
    {previous_data}
    ```
    
    ## Solicitacao de Analise
    
    Produza uma analise comparativa detalhada incluindo:
    
    1. **Resumo da Variacao**
       - Diferenca total em USD e percentual
       - Tendencia geral (crescimento, estabilidade, reducao)
    
    2. **Top 5 Servicos com Maior Variacao**
       | Servico | Anterior | Atual | Delta USD | Delta % |
    
    3. **Analise por Servico**
       Para cada servico com variacao significativa (>10%):
       - Causa provavel da variacao
       - Se e tendencia ou evento pontual
       - Acao recomendada
    
    4. **Oportunidades Identificadas**
    5. **Alertas**
    """
```

---

## 8. Como Usar na Pratica

### Exemplo de Uso via Codigo

```python
from finops_aws.ai_consultant import PromptBuilder, PromptPersona
from finops_aws.ai_consultant import QBusinessClient, QBusinessConfig

# 1. Configurar cliente
config = QBusinessConfig.from_env()
client = QBusinessClient(config)

# 2. Construir prompt
builder = PromptBuilder()
prompt = builder.build_analysis_prompt(
    cost_data={
        "total_cost": 47523.89,
        "period": "2024-11",
        "services": [
            {"name": "EC2", "cost": 18500.00, "change_pct": 12.5},
            {"name": "RDS", "cost": 9800.00, "change_pct": -3.2},
            {"name": "S3", "cost": 4200.00, "change_pct": 8.1}
        ]
    },
    period="Novembro 2024",
    persona=PromptPersona.EXECUTIVE,
    include_recommendations=True,
    include_trends=True,
    include_anomalies=True
)

# 3. Enviar para Amazon Q Business
response = client.chat(prompt)

# 4. Processar resposta
print(response.message)
```

### Fluxo de Execucao

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Cost       │───>│   Prompt     │───>│  Amazon Q    │───>│  Response    │
│   Data       │    │   Builder    │    │  Business    │    │  Parser      │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                           │                                        │
                           ▼                                        ▼
                    ┌──────────────┐                        ┌──────────────┐
                    │   Template   │                        │   Report     │
                    │   (Persona)  │                        │   (MD/HTML)  │
                    └──────────────┘                        └──────────────┘
```

---

## 9. Personalizacao de Prompts

### Adicionar Instrucoes Customizadas

```python
prompt = builder.build_analysis_prompt(
    cost_data=data,
    period="Nov 2024",
    persona=PromptPersona.EXECUTIVE,
    custom_instructions="""
    Foco adicional:
    - Comparar com o budget aprovado de $50.000/mes
    - Destacar projetos do time de Data Science
    - Incluir projecao para Q1 2025
    """
)
```

### Criar Nova Persona

```python
# Em src/finops_aws/ai_consultant/prompts/personas.py

class PromptPersona(Enum):
    EXECUTIVE = "executive"
    CTO = "cto"
    DEVOPS = "devops"
    ANALYST = "analyst"
    SECURITY = "security"  # Nova persona

# Adicionar configuracao
PERSONA_CONFIGS = {
    PromptPersona.SECURITY: PersonaConfig(
        name="Security Analyst",
        focus="Custos de seguranca, compliance, vulnerabilidades",
        tone="Tecnico e focado em riscos",
        include_commands=True,
        include_technical_details=True,
        max_sections=8
    )
}
```

---

## 10. Referencias

- **Codigo Fonte**: `src/finops_aws/ai_consultant/prompts/`
- **Templates**: `src/finops_aws/ai_consultant/prompts/templates/`
- **Builder**: `src/finops_aws/ai_consultant/prompts/builder.py`
- **Personas**: `src/finops_aws/ai_consultant/prompts/personas.py`
- **Documentacao Tecnica**: `docs/TECHNICAL_GUIDE.md` (Secao 17)

---

*Documento: PROMPTS_AMAZON_Q.md*
*Versao: 1.0*
*Data: Dezembro 2024*
*FinOps AWS Enterprise Solution*
