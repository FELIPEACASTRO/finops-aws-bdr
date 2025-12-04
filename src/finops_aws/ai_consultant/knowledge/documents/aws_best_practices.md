# AWS Cost Optimization Best Practices

Este documento contém as melhores práticas de otimização de custos AWS 
que devem ser consideradas ao gerar relatórios FinOps.

## 1. Right Sizing

### EC2 Instances

**Problema**: Instâncias superdimensionadas desperdiçam recursos e dinheiro.

**Indicadores**:
- CPU média < 40% por 7+ dias
- Memória média < 60%
- Network I/O consistentemente baixo

**Ações Recomendadas**:
- Migrar para tipo menor (ex: m5.xlarge → m5.large)
- Considerar instâncias Graviton (até 40% mais baratas)
- Usar AWS Compute Optimizer para recomendações

**Economia Típica**: 20-50% do custo da instância

### RDS Instances

**Indicadores**:
- CPU média < 30%
- Conexões ativas < 20% do limite
- Storage provisionado vs usado > 50%

**Ações**:
- Rightsizing de instância
- Considerar Aurora Serverless para workloads variáveis
- Revisar IOPS provisionados

## 2. Reserved Instances e Savings Plans

### Quando Usar Reserved Instances

**Ideal para**:
- Workloads estáveis e previsíveis
- Produção 24/7
- Compromisso de 1 ou 3 anos

**Opções de Pagamento**:
| Opção | Economia | Fluxo de Caixa |
|-------|----------|----------------|
| All Upfront | Máxima (até 72%) | Alto impacto inicial |
| Partial Upfront | Média (até 65%) | Balanceado |
| No Upfront | Menor (até 40%) | Distribuído |

### Quando Usar Savings Plans

**Compute Savings Plans**:
- Flexibilidade entre EC2, Fargate, Lambda
- Economia de até 66%
- Recomendado para ambientes dinâmicos

**EC2 Instance Savings Plans**:
- Economia até 72%
- Menor flexibilidade
- Ideal para workloads estáveis

**Cobertura Recomendada**: 70-80% do baseline de compute

## 3. Spot Instances

### Casos de Uso Ideais

- Processamento batch
- CI/CD pipelines
- Workloads tolerantes a interrupção
- Big Data (EMR, Spark)
- Ambientes de desenvolvimento

### Estratégias

**Diversificação de Pools**:
- Usar múltiplos tipos de instância
- Múltiplas AZs
- Capacity Optimized allocation

**Economia Típica**: 60-90% vs On-Demand

### Não Recomendado

- Bancos de dados
- Workloads stateful críticos
- Aplicações que não toleram interrupção

## 4. Storage Optimization

### S3

**Lifecycle Policies**:
| Classe | Caso de Uso | Economia vs Standard |
|--------|-------------|---------------------|
| IA | Acesso < 1x/mês | 40% |
| Glacier IR | Acesso < 1x/trimestre | 68% |
| Glacier | Acesso < 1x/ano | 82% |
| Deep Archive | Compliance/backup | 95% |

**Intelligent-Tiering**: Recomendado para padrões de acesso desconhecidos

**Multipart Upload Cleanup**: Limpar uploads incompletos

### EBS

**Volumes não anexados**: Deletar ou criar snapshot
**gp2 → gp3**: Economia de até 20% com melhor performance
**Snapshots antigos**: Implementar política de retenção

## 5. Auto Scaling

### Políticas Recomendadas

**Target Tracking**: 
- CPU target: 60-70%
- Request count: baseado em baseline

**Scheduled Scaling**:
- Dev/Staging: Desligar fora do horário
- Reduzir capacidade em horários de baixo uso

**Economia Típica**: 30-50% em ambientes não-produção

## 6. Networking

### NAT Gateway

**Custo**: $0.045/hora + $0.045/GB processado

**Otimizações**:
- Consolidar NAT Gateways onde possível
- Usar VPC Endpoints para serviços AWS (S3, DynamoDB)
- Gateway Endpoints são gratuitos

### Data Transfer

**Prioridades de otimização**:
1. Evitar transferência entre regiões
2. Usar mesma AZ quando possível
3. Compressão de dados
4. CDN (CloudFront) para conteúdo estático

## 7. Database

### RDS

**Multi-AZ**:
- Produção: Sim
- Dev/Staging: Não (economia de 50%)

**Backups**:
- Produção: Retenção 7-35 dias
- Dev: Retenção 1-7 dias

### DynamoDB

**On-Demand vs Provisioned**:
- Tráfego imprevisível: On-Demand
- Tráfego estável: Provisioned (mais barato)

**Reserved Capacity**: Até 77% de economia

## 8. Serverless

### Lambda

**Otimizações de memória**:
- Usar AWS Lambda Power Tuning
- Balancear custo x duração

**Provisioned Concurrency**:
- Somente para latência crítica
- Custo significativo se mal dimensionado

### Fargate

**Spot Fargate**: Economia de até 70%

**ARM (Graviton)**: Economia de 20%

## 9. Monitoramento

### Cost Anomaly Detection

- Configurar para todos os serviços críticos
- Threshold de 10% para alertas

### Budgets

- Budget mensal total
- Budgets por serviço principal
- Budgets por tag (centro de custo)

### Tagging

**Tags obrigatórias**:
- Environment (prod, staging, dev)
- Owner (equipe responsável)
- CostCenter (alocação financeira)
- Application (sistema)

## 10. Governança

### Políticas Recomendadas

- Aprovação para instâncias > $X/mês
- Revisão mensal de custos por equipe
- Automação de desligamento fora do horário
- Limpeza automática de recursos não-tagged

### FinOps Maturity

| Nível | Características |
|-------|-----------------|
| Crawl | Visibilidade básica, alertas reativos |
| Walk | Otimização ativa, budgets por equipe |
| Run | FinOps as Code, previsões, showback |
