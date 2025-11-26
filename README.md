# FinOps AWS - Solução Completa de Otimização de Custos

Uma solução serverless completa em Python para análise de custos, monitoramento de uso e recomendações de otimização na AWS.

## 🎯 Objetivo

Esta solução utiliza AWS Lambda para coletar, analisar e consolidar informações de:
- **Custos** por serviço AWS (7, 15 e 30 dias)
- **Métricas de uso** de recursos (EC2, Lambda, etc.)
- **Recomendações de otimização** via AWS Compute Optimizer

## 🏗️ Arquitetura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   EventBridge   │───▶│  Lambda Function │───▶│  CloudWatch     │
│   (Schedule)    │    │   (Python 3.11)  │    │   (Logs)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  API Gateway    │◀───│   FinOps Core    │───▶│ Cost Explorer   │
│   (Optional)    │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Compute Optimizer│
                       │   CloudWatch     │
                       │      EC2         │
                       └──────────────────┘
```

## 🚀 Funcionalidades

### 📊 Análise de Custos
- Coleta custos por serviço AWS via Cost Explorer
- Períodos: últimos 7, 15 e 30 dias
- Identificação dos serviços mais caros
- Cálculo de percentuais de gasto

### 📈 Métricas de Uso
- **EC2**: Utilização média de CPU por instância
- **Lambda**: Invocações, duração, erros e throttles
- Análise de recursos subutilizados/superdimensionados

### 🎯 Recomendações de Otimização
- Integração com AWS Compute Optimizer
- Recomendações de redimensionamento para EC2 e Lambda
- Estimativas de economia mensal
- Identificação de recursos OVER_PROVISIONED

### 📋 Relatório Consolidado
Gera um JSON estruturado com:
- Resumo executivo de custos
- Insights de utilização por serviço
- Oportunidades de otimização priorizadas
- Potencial total de economia

## 🛠️ Tecnologias

- **Runtime**: Python 3.11
- **Cloud**: AWS Lambda, CloudWatch, Cost Explorer
- **IaC**: CloudFormation
- **Testes**: pytest, moto
- **Logging**: JSON estruturado

## 📦 Estrutura do Projeto

```
finops-aws-bdr/
├── src/finops_aws/
│   ├── services/           # Serviços de negócio
│   │   ├── cost_service.py        # Cost Explorer
│   │   ├── metrics_service.py     # CloudWatch metrics
│   │   └── optimizer_service.py   # Compute Optimizer
│   ├── models/             # Modelos de dados
│   │   └── finops_models.py
│   ├── utils/              # Utilitários
│   │   ├── logger.py              # Logging estruturado
│   │   └── aws_helpers.py         # Helpers AWS
│   └── lambda_handler.py   # Handler principal
├── tests/                  # Testes unitários
│   └── unit/
├── infrastructure/         # CloudFormation
│   └── cloudformation-template.yaml
├── deploy.sh              # Script de deploy
├── requirements.txt       # Dependências Python
└── README.md
```

## 🔧 Instalação e Configuração

### Pré-requisitos

1. **AWS CLI** configurado com credenciais adequadas
2. **Python 3.11+**
3. **Bucket S3** para deploy do código
4. **Permissões IAM** necessárias (veja seção de Permissões)

### Deploy Rápido

```bash
# Clone o repositório
git clone <repository-url>
cd finops-aws-bdr

# Instale dependências
pip install -r requirements.txt

# Execute testes
python -m pytest tests/ -v

# Deploy na AWS
./deploy.sh -b SEU_BUCKET_S3
```

### Deploy Personalizado

```bash
# Deploy com configurações específicas
./deploy.sh \
  --stack-name finops-prod \
  --function-name finops-analyzer \
  --region us-west-2 \
  --bucket meu-bucket-deploy \
  --log-level DEBUG
```

### Opções do Deploy

| Parâmetro | Descrição | Padrão |
|-----------|-----------|---------|
| `--stack-name` | Nome da stack CloudFormation | `finops-aws-stack` |
| `--function-name` | Nome da função Lambda | `finops-aws-analyzer` |
| `--region` | Região AWS | `us-east-1` |
| `--bucket` | Bucket S3 para código | **obrigatório** |
| `--log-level` | Nível de log | `INFO` |
| `--no-schedule` | Desabilitar execução agendada | - |
| `--no-api` | Não criar API Gateway | - |
| `--update-only` | Apenas atualizar código | - |

## 🔐 Permissões IAM Necessárias

A função Lambda precisa das seguintes permissões:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "cloudwatch:GetMetricData",
        "cloudwatch:GetMetricStatistics",
        "ec2:DescribeInstances",
        "lambda:ListFunctions",
        "compute-optimizer:GetEC2InstanceRecommendations",
        "compute-optimizer:GetLambdaFunctionRecommendations",
        "compute-optimizer:GetEnrollmentStatus",
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🧪 Execução Local

### Teste Básico
```bash
# Configure credenciais AWS
aws configure

# Execute localmente
python -m src.finops_aws.lambda_handler
```

### Com Variáveis de Ambiente
```bash
export LOG_LEVEL=DEBUG
export AWS_DEFAULT_REGION=us-east-1
python -m src.finops_aws.lambda_handler
```

## 📊 Exemplo de Resposta

```json
{
  "account_id": "123456789012",
  "generated_at": "2025-01-26T10:00:00Z",
  "costs": {
    "last_7_days": {
      "Amazon Elastic Compute Cloud - Compute": 123.45,
      "Amazon Simple Storage Service": 12.34
    },
    "last_15_days": { ... },
    "last_30_days": { ... }
  },
  "usage": {
    "ec2": [
      {
        "instance_id": "i-0123456789abcdef0",
        "instance_type": "t3.xlarge",
        "avg_cpu_7d": 27.3,
        "avg_cpu_15d": 29.1,
        "avg_cpu_30d": 30.0
      }
    ],
    "lambda": [
      {
        "function_name": "my-function",
        "invocations_7d": 1500,
        "avg_duration_7d": 245.2,
        "errors_7d": 3
      }
    ]
  },
  "optimizer": {
    "ec2_recommendations": [
      {
        "resource_id": "i-0123456789abcdef0",
        "current_configuration": "t3.xlarge",
        "recommended_configurations": ["t3.large"],
        "estimated_monthly_savings": 45.67,
        "finding": "OVER_PROVISIONED"
      }
    ]
  },
  "summary": {
    "total_estimated_monthly_savings": 145.23,
    "cost_analysis": {
      "total_cost_last_30_days": 1234.56,
      "top_5_services": [...]
    },
    "optimization_opportunities": [...]
  }
}
```

## 🔄 Uso da API

Se habilitada, a API Gateway fornece acesso HTTP:

```bash
# GET request para análise
curl https://api-id.execute-api.region.amazonaws.com/prod/analyze

# Com autenticação (se configurada)
curl -H "Authorization: Bearer TOKEN" \
     https://api-id.execute-api.region.amazonaws.com/prod/analyze
```

## 📅 Execução Agendada

Por padrão, a função executa diariamente via EventBridge:
- **Agendamento**: `rate(1 day)` (configurável)
- **Logs**: CloudWatch Logs `/aws/lambda/function-name`
- **Dashboard**: CloudWatch Dashboard automático

## 🧪 Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Testes específicos
python -m pytest tests/unit/test_cost_service.py -v

# Com cobertura
python -m pytest tests/ --cov=src --cov-report=html
```

## 🔍 Monitoramento

### CloudWatch Logs
```bash
# Visualizar logs
aws logs tail /aws/lambda/finops-aws-analyzer --follow

# Filtrar erros
aws logs filter-log-events \
  --log-group-name /aws/lambda/finops-aws-analyzer \
  --filter-pattern "ERROR"
```

### Métricas Lambda
- Duration, Errors, Invocations
- Dashboard automático criado
- Alertas configuráveis

## ⚠️ Limitações e Considerações

### AWS Compute Optimizer
- Deve ser habilitado previamente na conta
- Requer pelo menos 12 horas de dados para recomendações
- Disponível apenas em regiões específicas

### Cost Explorer
- Dados podem ter até 24h de atraso
- Custos em USD por padrão
- Paginação automática implementada

### Timeouts
- Função Lambda: 5 minutos máximo
- Comandos de lint/test: 5 minutos máximo
- Retry automático para throttling

## 🚀 Próximos Passos

1. **Multi-conta**: Suporte a AWS Organizations
2. **Mais serviços**: RDS, EBS, ELB métricas
3. **Alertas**: Integração com SNS
4. **Histórico**: Armazenamento em DynamoDB
5. **Dashboard**: Interface web personalizada

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Add nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os logs no CloudWatch
2. Confirme permissões IAM
3. Valide configuração do Compute Optimizer
4. Abra uma issue no repositório

---

**Desenvolvido com ❤️ para otimização de custos AWS**
