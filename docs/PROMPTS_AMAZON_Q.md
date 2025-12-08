# Amazon Q Business - Prompts FinOps AWS

## Versão 2.1 - Dezembro 2025

**Status**: Consultor Financeiro Multi-IA (5 Provedores: Amazon Q, OpenAI, Gemini, Perplexity, StackSpot)

---

## 1. Visão Geral

O módulo **AI Consultant** utiliza Amazon Q Business para gerar análises inteligentes de custos AWS. O sistema oferece 4 personas, cada uma com um template de prompt otimizado.

### Personas Disponíveis

| Persona | Audiência | Foco Principal | Tom |
|---------|-----------|----------------|-----|
| **EXECUTIVE** | CEO/CFO | ROI, tendências, decisões estratégicas | Executivo |
| **CTO** | CTO/VP Engineering | Arquitetura, trade-offs, modernização | Técnico-estratégico |
| **DEVOPS** | DevOps/SRE | Scripts AWS CLI, implementação | Prático |
| **ANALYST** | FinOps Analyst | KPIs, métricas, benchmarks | Analítico |

---

## 2. Estrutura Base do Prompt

Todo prompt enviado ao Amazon Q segue esta estrutura:

\`\`\`markdown
## Contexto do Sistema

Você é um consultor senior de FinOps especializado em AWS, com mais de 15 anos 
de experiência em otimização de custos cloud. Você trabalha para uma empresa 
de consultoria de excelência.

Seu conhecimento inclui:
- Todos os 246 serviços AWS e seus modelos de precificação
- AWS Well-Architected Framework (Cost Optimization Pillar)
- FinOps Framework e melhores práticas
- Estratégias de Reserved Instances, Savings Plans e Spot
- Rightsizing, automação e governança de custos

## Dados de Custo AWS

**Custo Total (últimos 30 dias):** $X.XX

**Top Serviços por Custo:**
  - Amazon RDS: $0.14
  - Amazon S3: $0.004
  - [outros serviços...]

## Recursos AWS Ativos

  - ec2_instances: 0
  - s3_buckets: 1
  - rds_instances: 0
  - lambda_functions: 0
  - [outros recursos...]

## Instruções

[TEMPLATE ESPECÍFICO DA PERSONA]

## Formato de Saída

- Use Markdown com headers hierárquicos
- Valores monetários em USD
- Priorize por impacto financeiro
- Idioma: Português do Brasil
\`\`\`

---

## 3. Persona EXECUTIVE - Prompt e Resposta

### 3.1 Template do Prompt

\`\`\`markdown
Produza um relatório executivo de custos AWS com:

### 1. RESUMO EXECUTIVO (2 parágrafos)

**Parágrafo 1 - Visão Geral**
- Gasto total do período em USD
- Variação percentual vs período anterior
- Comparativo com benchmark se disponível

**Parágrafo 2 - Principais Drivers**
- Top 3 serviços que mais impactam o custo
- Tendência de cada um (crescendo, estável, reduzindo)

### 2. TOP 3 OPORTUNIDADES DE ECONOMIA

| Oportunidade | Economia/Mês | Economia/Ano | Prazo |
|--------------|--------------|--------------|-------|

### 3. RISCOS IDENTIFICADOS

| Risco | Probabilidade | Impacto | Ação Preventiva |
|-------|---------------|---------|-----------------|

### 4. PRÓXIMOS PASSOS (3 ações prioritárias)

**Tom**: Executivo, foco em ROI e impacto no negócio.
**Limite**: Máximo 2 páginas.
\`\`\`

### 3.2 Exemplo de Resposta EXECUTIVE

\`\`\`markdown
# Relatório Executivo FinOps - Dezembro 2024

## Resumo Executivo

O custo total da infraestrutura AWS nos últimos 30 dias foi de **$0.15**, 
distribuído principalmente entre Amazon RDS ($0.14, 95%) e Amazon S3 ($0.004, 3%).
Este valor representa uma infraestrutura de baixo consumo, típica de ambientes 
de desenvolvimento ou aplicações com uso mínimo.

A análise identificou 3 oportunidades de otimização focadas em boas práticas 
de governança que, embora não gerem economia imediata, preparam a infraestrutura 
para escala futura e reduzem riscos operacionais.

## Top 3 Oportunidades de Economia

| # | Oportunidade | Economia/Mês | Prazo |
|---|--------------|--------------|-------|
| 1 | Habilitar versionamento S3 | $0 (governança) | 7 dias |
| 2 | Configurar lifecycle policies | $0-5 (storage) | 14 dias |
| 3 | Avaliar dimensionamento RDS | TBD | 30 dias |

## Riscos Identificados

| Risco | Probabilidade | Impacto | Ação |
|-------|---------------|---------|------|
| Perda de dados S3 | Baixa | Alto | Habilitar versionamento |
| Crescimento de storage | Média | Médio | Lifecycle policies |

## Próximos Passos

1. ✅ **Esta semana**: Habilitar versionamento no bucket S3
2. 📋 **Próximas 2 semanas**: Implementar lifecycle policies
3. 📊 **Este mês**: Revisar utilização RDS quando em produção
\`\`\`

---

## 4. Persona CTO - Prompt e Resposta

### 4.1 Template do Prompt

\`\`\`markdown
Produza um relatório técnico-estratégico de custos AWS com:

### 1. VISÃO GERAL TÉCNICA

- Total de recursos por categoria (compute, storage, database)
- Distribuição de custos por tipo de workload
- Cobertura de Reserved Instances e Savings Plans

### 2. ANÁLISE POR CAMADA ARQUITETURAL

Para cada camada (Compute, Storage, Database, Network):
- Custo total e % do gasto
- Utilização e eficiência
- Alternativas arquiteturais

### 3. DÉBITO TÉCNICO DE CUSTO

| Padrão | Impacto/Mês | Causa Raiz | Solução |
|--------|-------------|------------|---------|

### 4. ROADMAP DE MODERNIZAÇÃO

**Fase 1: 0-30 dias** - Otimização imediata
**Fase 2: 30-90 dias** - Refatoração
**Fase 3: 90-180 dias** - Transformação

### 5. TRADE-OFFS

| Decisão | Benefício | Trade-off | Recomendação |
|---------|-----------|-----------|--------------|

**Tom**: Técnico-estratégico, foco em arquitetura.
\`\`\`

### 4.2 Exemplo de Resposta CTO

\`\`\`markdown
# Relatório Técnico FinOps - Dezembro 2024

## Visão Geral Técnica

### Distribuição de Recursos

| Categoria | Recursos | Custo/Mês | % Total |
|-----------|----------|-----------|---------|
| Database | 1 (RDS) | $0.14 | 95% |
| Storage | 1 bucket | $0.004 | 3% |
| Compute | 0 instâncias | $0 | 0% |
| **Total** | **2** | **$0.15** | **100%** |

### Eficiência Atual

- **Cobertura RI/SP**: 0% (não aplicável - uso mínimo)
- **Recursos ociosos**: Nenhum identificado
- **Rightsizing**: N/A (sem instâncias EC2)

## Análise por Camada Arquitetural

### Database (RDS) - 95% do custo

| Aspecto | Status | Recomendação |
|---------|--------|--------------|
| Tipo | Provavelmente db.t3.micro | Adequado para dev |
| Multi-AZ | Desconhecido | Desabilitar em dev |
| Storage | GP2/GP3 | Avaliar I/O |

**Alternativas**: Aurora Serverless v2 para workloads variáveis

### Storage (S3) - 3% do custo

| Aspecto | Status | Recomendação |
|---------|--------|--------------|
| Versionamento | ❌ Desabilitado | Habilitar |
| Lifecycle | ❌ Não configurado | Implementar |
| Classe | Standard | Intelligent-Tiering |

## Débito Técnico de Custo

| Padrão | Impacto | Causa Raiz | Solução |
|--------|---------|------------|---------|
| Falta de lifecycle S3 | Crescimento futuro | Não configurado | Implementar policy |
| Sem versionamento | Risco de perda | Não habilitado | Habilitar |

## Roadmap de Modernização

### Fase 1: Otimização Imediata (0-30 dias)
- [x] Auditoria de recursos concluída
- [ ] Lifecycle policies S3
- [ ] Tags de alocação de custo

### Fase 2: Refatoração (30-90 dias)
- [ ] Avaliar Aurora Serverless
- [ ] Implementar FinOps tags

### Fase 3: Transformação (90-180 dias)
- [ ] FinOps as Code (políticas de custo)
- [ ] Alertas automatizados de budget

## Trade-offs

| Decisão | Benefício | Trade-off | Recomendação |
|---------|-----------|-----------|--------------|
| Aurora Serverless | Pay-per-use | Latência cold start | Avaliar em produção |
| S3 Glacier | 90% economia | Tempo de acesso | Dados históricos |
\`\`\`

---

## 5. Persona DEVOPS - Prompt e Resposta

### 5.1 Template do Prompt

\`\`\`markdown
Produza um relatório operacional de custos AWS com:

### 1. RESUMO OPERACIONAL

- Total de recursos ativos
- Recursos com alertas de custo
- Recursos sem tags obrigatórias

### 2. AÇÕES IMEDIATAS

Para cada recurso que precisa de ação:
- ID do recurso
- Problema identificado
- Comando AWS CLI para resolver

### 3. SCRIPTS DE AUTOMAÇÃO

Forneça scripts Python/Bash para:
- Identificar recursos subutilizados
- Aplicar tags em lote
- Configurar alertas de custo

### 4. COMANDOS AWS CLI

Comandos copy-paste ready para cada otimização.

### 5. CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Lista de ações ordenadas por prioridade

**Tom**: Prático e técnico, foco em implementação.
\`\`\`

### 5.2 Exemplo de Resposta DEVOPS

\`\`\`markdown
# Relatório Operacional FinOps - Dezembro 2024

## Resumo Operacional

| Métrica | Valor |
|---------|-------|
| Recursos ativos | 2 |
| Recursos com alertas | 0 |
| Recursos sem tags | 1 (bucket S3) |

## Ações Imediatas

### 1. Habilitar Versionamento S3

**Recurso**: minha-empresa-app-bucket
**Problema**: Bucket sem versionamento (risco de perda de dados)
**Prioridade**: ALTA

\`\`\`bash
# Verificar status atual
aws s3api get-bucket-versioning \
  --bucket minha-empresa-app-bucket

# Habilitar versionamento
aws s3api put-bucket-versioning \
  --bucket minha-empresa-app-bucket \
  --versioning-configuration Status=Enabled

# Verificar se foi habilitado
aws s3api get-bucket-versioning \
  --bucket minha-empresa-app-bucket
\`\`\`

### 2. Configurar Lifecycle Policy

**Recurso**: minha-empresa-app-bucket
**Problema**: Sem transição automática para classes econômicas
**Prioridade**: MÉDIA

\`\`\`bash
# Criar arquivo de configuração
cat > lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "ID": "TransitionToIA",
      "Status": "Enabled",
      "Filter": {},
      "Transitions": [
        {"Days": 30, "StorageClass": "STANDARD_IA"},
        {"Days": 90, "StorageClass": "GLACIER"}
      ],
      "Expiration": {"Days": 365}
    }
  ]
}
EOF

# Aplicar lifecycle
aws s3api put-bucket-lifecycle-configuration \
  --bucket minha-empresa-app-bucket \
  --lifecycle-configuration file://lifecycle.json

# Verificar configuração
aws s3api get-bucket-lifecycle-configuration \
  --bucket minha-empresa-app-bucket
\`\`\`

### 3. Criar Alarme de Custo

\`\`\`bash
# Criar alarme de custo diário
aws cloudwatch put-metric-alarm \
  --alarm-name "DailyCostAlert-$10" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 86400 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=Currency,Value=USD \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:cost-alerts
\`\`\`

## Script de Automação

\`\`\`python
#!/usr/bin/env python3
"""Verificar buckets S3 sem lifecycle policy."""
import boto3

def check_s3_lifecycle():
    s3 = boto3.client('s3')
    buckets = s3.list_buckets()['Buckets']
    
    results = {'configured': [], 'missing': []}
    
    for bucket in buckets:
        name = bucket['Name']
        try:
            s3.get_bucket_lifecycle_configuration(Bucket=name)
            results['configured'].append(name)
            print(f"✅ {name}: Lifecycle configurado")
        except s3.exceptions.ClientError:
            results['missing'].append(name)
            print(f"❌ {name}: SEM lifecycle policy")
    
    print(f"\n📊 Resumo: {len(results['configured'])} OK, {len(results['missing'])} pendentes")
    return results

if __name__ == '__main__':
    check_s3_lifecycle()
\`\`\`

## Checklist de Implementação

- [ ] Habilitar versionamento S3
- [ ] Configurar lifecycle policies
- [ ] Criar alarme de custo
- [ ] Adicionar tags de custo
- [ ] Documentar procedimentos
\`\`\`

---

## 6. Persona ANALYST - Prompt e Resposta

### 6.1 Template do Prompt

\`\`\`markdown
Produza um relatório analítico de custos AWS com:

### 1. DASHBOARD DE MÉTRICAS

| KPI | Valor | Meta | Status |
|-----|-------|------|--------|

### 2. ANÁLISE MULTIDIMENSIONAL

- Por Serviço (Top 10)
- Por Região
- Por Ambiente (tags)

### 3. COBERTURA DE COMPROMISSOS

- Reserved Instances
- Savings Plans

### 4. ANÁLISE DE WASTE

- Recursos ociosos
- Waste ratio por serviço

### 5. UNIT ECONOMICS

- Custo por transação
- Custo por usuário

### 6. PREVISÕES

| Mês | Projeção | Intervalo |
|-----|----------|-----------|

### 7. MATURIDADE FINOPS

| Domínio | Nível | Meta |
|---------|-------|------|

**Tom**: Analítico e data-driven, sem limite de páginas.
\`\`\`

### 6.2 Exemplo de Resposta ANALYST

\`\`\`markdown
# Relatório Analítico FinOps - Dezembro 2024

## Dashboard de Métricas

| KPI | Valor | Meta | Delta | Status |
|-----|-------|------|-------|--------|
| Custo Total (30d) | $0.15 | $10.00 | -98.5% | 🟢 |
| Cobertura RI/SP | 0% | 70% | -70% | 🔴 |
| Waste Ratio | 0% | <5% | 0% | 🟢 |
| Recursos tagueados | 0% | 100% | -100% | 🔴 |

## Análise por Serviço

| Rank | Serviço | Custo | % Total | MoM | Tendência |
|------|---------|-------|---------|-----|-----------|
| 1 | Amazon RDS | $0.1425 | 95.3% | - | ➡️ Estável |
| 2 | Amazon S3 | $0.0041 | 2.7% | - | ➡️ Estável |
| 3 | Tax | $0.003 | 2.0% | - | ➡️ Estável |
| **Total** | | **$0.15** | **100%** | | |

## Análise por Região

| Região | Custo | % Total | Recursos |
|--------|-------|---------|----------|
| us-east-1 | $0.15 | 100% | 2 |

## Cobertura de Compromissos

| Tipo | Status | Recomendação |
|------|--------|--------------|
| Reserved Instances | N/A | Uso insuficiente |
| Savings Plans | N/A | Uso insuficiente |

**Nota**: Com custo mensal de $0.15, compromissos não são recomendados.
Threshold mínimo sugerido: $100/mês para considerar RI/SP.

## Análise de Waste

| Categoria | Quantidade | Custo/Mês | Waste % |
|-----------|------------|-----------|---------|
| EBS órfãos | 0 | $0 | 0% |
| EIPs não associados | 0 | $0 | 0% |
| Snapshots antigos | 0 | $0 | 0% |
| **Total Waste** | **0** | **$0** | **0%** |

## Unit Economics

| Métrica | Valor | Benchmark |
|---------|-------|-----------|
| Custo por recurso | $0.075 | - |
| Custo por serviço | $0.05 | - |

**Nota**: Métricas de unit economics requerem dados de negócio 
(transações, usuários) para cálculos significativos.

## Previsão de Custos

| Mês | Projeção | Intervalo (95%) | Premissas |
|-----|----------|-----------------|-----------|
| Jan 2025 | $0.15 | $0.12 - $0.20 | Uso estável |
| Fev 2025 | $0.15 | $0.10 - $0.25 | Uso estável |
| Mar 2025 | $0.15 | $0.10 - $0.30 | Uso estável |

## Maturidade FinOps

| Domínio | Nível Atual | Meta | Gap |
|---------|-------------|------|-----|
| Visibilidade | Walk | Run | 1 nível |
| Alocação | Crawl | Walk | 1 nível |
| Otimização | Walk | Run | 1 nível |
| Governança | Crawl | Walk | 1 nível |

### Recomendações por Domínio

1. **Visibilidade**: Implementar Cost Allocation Tags
2. **Alocação**: Definir centros de custo
3. **Otimização**: Lifecycle policies S3
4. **Governança**: Alertas de budget

## Próximos Passos

| Ação | Impacto | Esforço | Prazo |
|------|---------|---------|-------|
| Tags de custo | Alto | Baixo | 7 dias |
| Lifecycle S3 | Médio | Baixo | 7 dias |
| Alertas | Alto | Baixo | 3 dias |
\`\`\`

---

## 7. Configuração

### Variável de Ambiente

\`\`\`bash
export Q_BUSINESS_APPLICATION_ID=seu-application-id
\`\`\`

### Código de Integração

\`\`\`python
import boto3
import os

def get_amazon_q_insights(costs, resources, persona='EXECUTIVE'):
    q_app_id = os.environ.get('Q_BUSINESS_APPLICATION_ID')
    if not q_app_id:
        return []
    
    q = boto3.client('qbusiness')
    prompt = build_finops_prompt(costs, resources, persona)
    
    response = q.chat_sync(
        applicationId=q_app_id,
        userMessage=prompt
    )
    
    return response.get('systemMessage', '')
\`\`\`

---

## 8. Melhores Práticas

1. **Seja específico**: Inclua números e IDs de recursos
2. **Priorize**: Sempre ordene por impacto financeiro
3. **Actionable**: Cada insight deve ter uma ação clara
4. **Contexto**: Forneça dados suficientes para análise precisa

---

*Documento atualizado em: Dezembro 2024*
