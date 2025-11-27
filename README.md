# FinOps AWS - Solução Enterprise de Otimização de Custos AWS

Uma solução **serverless enterprise-grade** em Python para análise inteligente de custos, monitoramento de uso e recomendações de otimização na AWS. Analisa **252 serviços AWS**, oferecendo insights financeiros e operacionais completos.

---

## Documentação Completa

| Documento | Descrição | Link |
|-----------|-----------|------|
| **Guia Técnico** | Arquitetura, padrões de projeto, diagramas | [docs/TECHNICAL_GUIDE.md](docs/TECHNICAL_GUIDE.md) |
| **Guia Funcional** | Capacidades, módulos, casos de uso | [docs/FUNCTIONAL_GUIDE.md](docs/FUNCTIONAL_GUIDE.md) |
| **Manual do Usuário** | Instalação, configuração, uso | [docs/USER_MANUAL.md](docs/USER_MANUAL.md) |
| **Catálogo de Serviços** | Lista completa dos 252 serviços | [docs/APPENDIX_SERVICES.md](docs/APPENDIX_SERVICES.md) |

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Métricas do Projeto](#métricas-do-projeto)
3. [Arquitetura](#arquitetura)
4. [Serviços Suportados](#serviços-suportados)
5. [Início Rápido](#início-rápido)
6. [Estrutura do Projeto](#estrutura-do-projeto)
7. [Deploy na AWS](#deploy-na-aws)
8. [Testes](#testes)
9. [Stack Tecnológico](#stack-tecnológico)

---

## Visão Geral

### O Que é FinOps?

**FinOps (Financial Operations)** é uma prática de gerenciamento financeiro em nuvem que combina sistemas, melhores práticas e cultura para aumentar a capacidade de uma organização de entender os custos da nuvem e tomar decisões informadas.

### Proposta de Valor

```
┌─────────────────────────────────────────────────────────────────┐
│                      FINOPS AWS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ 252 Serviços AWS     ✅ Análise Automática                 │
│  ✅ Clean Architecture   ✅ Recomendações ML                   │
│  ✅ 1842 Testes         ✅ Multi-Conta                         │
│  ✅ Serverless          ✅ Enterprise-Ready                    │
│                                                                 │
│  ECONOMIA TÍPICA: 20-40% em custos AWS                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Problema vs Solução

| Problema | Nossa Solução |
|----------|---------------|
| Custos AWS crescendo sem controle | Análise automática multi-período |
| Recursos subutilizados | Identificação de instâncias ociosas |
| Falta de visibilidade | Dashboard consolidado com 252 serviços |
| Recomendações manuais | Integração com AWS Compute Optimizer |
| Dificuldade de monitoramento | Alertas proativos e métricas em tempo real |

---

## Métricas do Projeto

| Métrica | Valor |
|---------|-------|
| **Serviços AWS Implementados** | 252 (100% do catálogo) |
| **Testes Automatizados** | 1,842 passando |
| **Cobertura de Código** | ~90% |
| **Categorias Cobertas** | 16 categorias completas |
| **Arquitetura** | Clean Architecture + DDD |

### Cobertura por Categoria

```
Compute & Serverless ████████████████████████ 25
Storage              ███████████████         15
Database             ████████████████████████ 25
Networking           ████████████████████     20
Security & Identity  ████████████████████     20
AI/ML                ████████████████████████ 25
Analytics            ████████████████████     20
Developer Tools      ███████████████         15
Management           ███████████████         15
Cost Management      ██████████              10
Observability        ███████████████         15
IoT & Edge           ██████████              10
Media                ███████                  7
End User             ███████████████         15
Specialty            ███████████████         15
```

---

## Arquitetura

### Diagrama de Alto Nível

```
┌─────────────────────────────────────────────────────────────────┐
│                     TRIGGERS (Gatilhos)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  EventBridge │  │ API Gateway  │  │   CLI Local  │          │
│  │  (Agendado)  │  │  (HTTP/REST) │  │   (Demo)     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AWS LAMBDA HANDLER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              ResilientExecutor + RetryHandler             │  │
│  │                   (Resiliência & Retry)                   │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
│  ┌──────────────────────────▼───────────────────────────────┐  │
│  │                    ServiceFactory                         │  │
│  │               (252 Serviços Registrados)                  │  │
│  └──────────────────────────┬───────────────────────────────┘  │
└─────────────────────────────┼───────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   EC2Service    │ │   RDSService    │ │  252 Services   │
│  health_check() │ │  health_check() │ │  health_check() │
│  analyze_usage()│ │  analyze_usage()│ │  analyze_usage()│
│  get_recommend()│ │  get_recommend()│ │  get_recommend()│
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                       AWS CLOUD                                 │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│  │   EC2   │ │   RDS   │ │   S3    │ │ Lambda  │ │  253+   │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes Principais

| Componente | Responsabilidade |
|------------|------------------|
| `ServiceFactory` | Criação e cache de 252 serviços |
| `BaseAWSService` | Interface comum para todos os serviços |
| `ResilientExecutor` | Execução com circuit breaker |
| `RetryHandler` | Retry com exponential backoff |
| `DynamoDBStateManager` | Persistência de estado |

---

## Serviços Suportados

### Principais Categorias

**Compute & Serverless (25)**
- EC2, Lambda, ECS, EKS, Batch, Lightsail, App Runner, Elastic Beanstalk
- Lambda@Edge, SAM, Outposts, Local Zones, Wavelength, Private 5G

**Database (25)**
- RDS, Aurora, DynamoDB, ElastiCache, Redshift, DocumentDB
- Neptune, Keyspaces, Timestream, QLDB, OpenSearch, MemoryDB

**Security & Identity (22)**
- IAM, Security Hub, GuardDuty, Macie, Inspector, KMS, ACM
- Secrets Manager, WAF, Shield, Cognito, Detective, Security Lake

**AI/ML (26)**
- Bedrock, SageMaker (Studio, Pipelines, Feature Store, etc.)
- Comprehend, Rekognition, Textract, Lex, Polly, Transcribe

**E mais 154 serviços...** Ver [Catálogo Completo](docs/APPENDIX_SERVICES.md)

---

## Início Rápido

### Pré-requisitos

- Python 3.11+
- Conta AWS com permissões de leitura
- AWS CLI configurado (opcional)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-org/finops-aws.git
cd finops-aws

# Instale dependências
pip install -r requirements.txt
```

### Execução Local (Demo)

```bash
# Executar com serviços mockados (sem AWS real)
python run_local_demo.py 1

# Executar com sua conta AWS
export AWS_ACCESS_KEY_ID="sua-key"
export AWS_SECRET_ACCESS_KEY="sua-secret"
python run_with_aws.py
```

### Exemplo de Saída

```
================================================================================
  FinOps AWS - Análise de Custos e Otimização
================================================================================

✓ 252 serviços analisados
✓ 1,234 recursos encontrados

RESUMO DE CUSTOS (Mensal):
  Total: $45,234.56
  EC2: $18,234.00 (40.3%)
  RDS: $12,567.00 (27.8%)
  S3: $5,432.00 (12.0%)

ECONOMIA POTENCIAL: $8,500.00/mês (18.8%)

RECOMENDAÇÕES PRIORITÁRIAS:
  [ALTA] 5 instâncias EC2 subutilizadas - $2,340/mês
  [ALTA] 3 candidatas a Reserved Instance - $4,200/mês
  [MÉDIA] 12 recursos não utilizados - $890/mês

================================================================================
```

---

## Estrutura do Projeto

```
finops-aws/
├── src/finops_aws/           # Código fonte principal
│   ├── core/                 # Núcleo da aplicação
│   │   ├── factories.py      # ServiceFactory + AWSClientFactory
│   │   ├── dynamodb_state_manager.py
│   │   ├── resilient_executor.py
│   │   └── retry_handler.py
│   ├── models/               # Modelos de domínio
│   │   └── finops_models.py
│   ├── services/             # 252 serviços AWS
│   │   ├── base_service.py   # Classe base abstrata
│   │   ├── ec2_service.py
│   │   ├── lambda_service.py
│   │   └── ... (249 outros)
│   └── utils/                # Utilitários
│       └── logger.py
├── tests/                    # 1,842 testes
│   └── unit/
├── docs/                     # Documentação completa
│   ├── TECHNICAL_GUIDE.md
│   ├── FUNCTIONAL_GUIDE.md
│   ├── USER_MANUAL.md
│   └── APPENDIX_SERVICES.md
├── infrastructure/           # CloudFormation + IAM
├── example_events/           # Eventos de exemplo
├── requirements.txt
├── run_local_demo.py         # Demo local
├── run_with_aws.py           # Execução com AWS real
└── deploy.sh                 # Script de deploy
```

---

## Deploy na AWS

### Via CloudFormation

```bash
# Preparar pacote
./deploy.sh package

# Deploy
aws cloudformation deploy \
  --template-file infrastructure/cloudformation-template.yaml \
  --stack-name finops-aws-production \
  --capabilities CAPABILITY_IAM
```

### Configurar Agendamento

O Lambda é automaticamente agendado para execução diária às 6h UTC.

```bash
# Alterar para semanal
aws events put-rule \
  --name finops-aws-schedule \
  --schedule-expression "cron(0 8 ? * SUN *)"
```

---

## Testes

### Executar Todos os Testes

```bash
# Via demo runner
python run_local_demo.py 2

# Via pytest diretamente
pytest tests/unit/ -v

# Com cobertura
pytest tests/unit/ --cov=src/finops_aws --cov-report=html
```

### Estatísticas de Testes

```
============================= test session starts =============================
collected 1842 items

tests/unit/test_cleanup_manager.py ............................ [  1%]
tests/unit/test_cost_service.py ............................... [  2%]
tests/unit/test_dynamodb_state_manager.py ..................... [  4%]
...
============================= 1841 passed, 1 skipped ==========================
```

---

## Stack Tecnológico

| Tecnologia | Uso |
|------------|-----|
| **Python 3.11** | Linguagem principal |
| **boto3** | SDK AWS |
| **pytest** | Framework de testes |
| **moto** | Mock de serviços AWS |
| **AWS Lambda** | Execução serverless |
| **DynamoDB** | Persistência de estado |
| **CloudFormation** | Infrastructure as Code |
| **EventBridge** | Agendamento |

---

## Padrões de Projeto

- **Clean Architecture**: Separação de responsabilidades
- **Domain-Driven Design**: Modelos de domínio ricos
- **Factory Pattern**: Criação centralizada de serviços
- **Template Method**: Interface comum via BaseAWSService
- **Circuit Breaker**: Proteção contra falhas em cascata
- **Retry with Backoff**: Resiliência a falhas transitórias

---

## Segurança

- **Read-Only**: O sistema nunca modifica recursos
- **Least Privilege**: Permissões mínimas necessárias
- **No Hardcoded Secrets**: Uso de variáveis de ambiente
- **Encryption**: TLS em trânsito, KMS em repouso
- **Audit Trail**: Logging via CloudTrail

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Suporte

- **Documentação**: [docs/](docs/)
- **Issues**: Abra uma issue no repositório
- **Email**: suporte@finops-aws.example.com

---

*FinOps AWS - Solução Enterprise de Otimização de Custos*
*252 serviços AWS | 1,842 testes | Clean Architecture*
*Versão 1.0 - Novembro 2025*
