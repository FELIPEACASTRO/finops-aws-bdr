# FinOps AWS - Guia Tecnico Completo

## Versao 2.1 - Dezembro 2025

**Status**: Clean Architecture + React 18 Frontend + 5 AI Providers + 100% Real Data

---

```
+==============================================================================+
|                                                                              |
|                    GUIA TECNICO COMPLETO - FINOPS AWS                       |
|                                                                              |
|   Documentacao tecnica detalhada para desenvolvedores, arquitetos e         |
|   engenheiros que trabalham com a solucao FinOps AWS.                       |
|                                                                              |
+==============================================================================+
```

---

## Indice

1. [Visao Geral da Solucao](#1-visao-geral-da-solucao)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Stack Tecnologica](#3-stack-tecnologica)
4. [Modulo de Analyzers](#4-modulo-de-analyzers)
5. [Integracoes AWS](#5-integracoes-aws)
6. [Amazon Q Business](#6-amazon-q-business)
7. [API Endpoints](#7-api-endpoints)
8. [Configuracao](#8-configuracao)
9. [Testes](#9-testes)
10. [Deploy e Operacao](#10-deploy-e-operacao)

---

# 1. Visao Geral da Solucao

## 1.1 Numeros do Sistema

```
+==============================================================================+
|                        FINOPS AWS EM NUMEROS                                 |
+==============================================================================+
|                                                                              |
|   +----------------------+  +----------------------+  +----------------------+
|   |                      |  |                      |  |                      |
|   |   246 SERVICOS AWS   |  |   23 VERIFICACOES    |  |   4 INTEGRACOES      |
|   |                      |  |                      |  |                      |
|   |   Suportados na      |  |   De otimizacao      |  |   AWS ativas:        |
|   |   enum AWSServiceType|  |   automaticas        |  |   - Compute Optimizer|
|   |   (60% boto3)        |  |   por servico        |  |   - Cost Explorer    |
|   |                      |  |                      |  |   - Trusted Advisor  |
|   +----------------------+  +----------------------+  |   - Amazon Q         |
|                                                       +----------------------+
|   +----------------------+  +----------------------+  +----------------------+
|   |                      |  |                      |  |                      |
|   |   6 ANALYZERS        |  |   5 DESIGN PATTERNS  |  |   2,204 TESTES       |
|   |                      |  |                      |  |                      |
|   |   Especializados:    |  |   GoF aplicados:     |  |   Automatizados:     |
|   |   - Compute          |  |   - Strategy         |  |   - 1,865 Unit       |
|   |   - Storage          |  |   - Factory          |  |   - 44 Integration   |
|   |   - Database         |  |   - Template Method  |  |   - 240 QA           |
|   |   - Network          |  |   - Registry         |  |   - 55 E2E           |
|   |   - Security         |  |   - Facade           |  |                      |
|   |   - Analytics        |  |                      |  |   100% passing       |
|   |                      |  |                      |  |                      |
|   +----------------------+  +----------------------+  +----------------------+
|                                                                              |
+==============================================================================+
```

## 1.2 Caracteristicas Principais

```
+-----------------------------------------------------------------------------+
|                       CARACTERISTICAS DO SISTEMA                            |
+-----------------------------------------------------------------------------+
|                                                                             |
|  ARQUITETURA                                                                |
|  ===========                                                                |
|                                                                             |
|  +--------------------+----------------------------------------------------+|
|  | Clean Architecture | Separacao clara de responsabilidades               ||
|  +--------------------+----------------------------------------------------+|
|  | DDD                | Domain-Driven Design com entidades ricas           ||
|  +--------------------+----------------------------------------------------+|
|  | Design Patterns    | Strategy, Factory, Template Method, Registry, Facade|
|  +--------------------+----------------------------------------------------+|
|  | SOLID              | Todos os 5 principios aplicados                    ||
|  +--------------------+----------------------------------------------------+|
|                                                                             |
|  FUNCIONALIDADES                                                            |
|  ===============                                                            |
|                                                                             |
|  +--------------------+----------------------------------------------------+|
|  | Multi-Region       | Analise paralela em todas as regioes AWS           ||
|  +--------------------+----------------------------------------------------+|
|  | Exportacao         | CSV, JSON, PDF (versao impressao)                  ||
|  +--------------------+----------------------------------------------------+|
|  | Dashboard          | Interface web moderna com dados em tempo real      ||
|  +--------------------+----------------------------------------------------+|
|  | AI Insights        | Amazon Q Business com 4 personas                   ||
|  +--------------------+----------------------------------------------------+|
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 2. Arquitetura do Sistema

## 2.1 Diagrama de Arquitetura Completo

```
+==============================================================================+
|                       ARQUITETURA FINOPS AWS                                 |
+==============================================================================+
|                                                                              |
|                              +-------------+                                 |
|                              |   USUARIO   |                                 |
|                              +------+------+                                 |
|                                     |                                        |
|                                     v                                        |
|  +------------------------------------------------------------------------+  |
|  |                         PRESENTATION LAYER                             |  |
|  |                                                                        |  |
|  |   +----------------+    +----------------+    +----------------+       |  |
|  |   |  Flask Routes  |    |  HTML/CSS/JS   |    |   REST API     |       |  |
|  |   |                |    |                |    |                |       |  |
|  |   |  /             |    | dashboard.html |    | /api/v1/...    |       |  |
|  |   |  /api/v1/...   |    | styles.css     |    | JSON responses |       |  |
|  |   |  /export/...   |    | scripts.js     |    |                |       |  |
|  |   +----------------+    +----------------+    +----------------+       |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                     |                                        |
|                                     v                                        |
|  +------------------------------------------------------------------------+  |
|  |                        APPLICATION LAYER                               |  |
|  |                                                                        |  |
|  |   +----------------------------------------------------------------+   |  |
|  |   |                     FACADE (analysis.py)                       |   |  |
|  |   |                                                                |   |  |
|  |   |   get_dashboard_analysis()                                     |   |  |
|  |   |       |                                                        |   |  |
|  |   |       +---> get_cost_data()           --> Cost Explorer API    |   |  |
|  |   |       +---> get_analyzers_analysis()  --> 6 Analyzers          |   |  |
|  |   |       +---> get_compute_optimizer()   --> Compute Optimizer    |   |  |
|  |   |       +---> get_cost_explorer_ri()    --> RI/SP Recommendations|   |  |
|  |   |       +---> get_trusted_advisor()     --> Trusted Advisor      |   |  |
|  |   |       +---> get_amazon_q_insights()   --> Amazon Q Business    |   |  |
|  |   |                                                                |   |  |
|  |   +----------------------------------------------------------------+   |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                     |                                        |
|                                     v                                        |
|  +------------------------------------------------------------------------+  |
|  |                          DOMAIN LAYER                                  |  |
|  |                                                                        |  |
|  |   +-----------------------------+    +-----------------------------+   |  |
|  |   |    ANALYZERS (Strategy)     |    |      DOMAIN ENTITIES        |   |  |
|  |   |                             |    |                             |   |  |
|  |   |   BaseAnalyzer (ABC)        |    |   AWSResource               |   |  |
|  |   |       |                     |    |   CostBreakdown             |   |  |
|  |   |       +-- ComputeAnalyzer   |    |   Recommendation            |   |  |
|  |   |       +-- StorageAnalyzer   |    |   AnalysisResult            |   |  |
|  |   |       +-- DatabaseAnalyzer  |    |                             |   |  |
|  |   |       +-- NetworkAnalyzer   |    +-----------------------------+   |  |
|  |   |       +-- SecurityAnalyzer  |                                      |  |
|  |   |       +-- AnalyticsAnalyzer |    +-----------------------------+   |  |
|  |   |                             |    |       EXCEPTIONS            |   |  |
|  |   +-----------------------------+    |                             |   |  |
|  |                                      |   FinOpsError               |   |  |
|  |   +-----------------------------+    |   AWSServiceError           |   |  |
|  |   | FACTORY + REGISTRY          |    |   AnalysisError             |   |  |
|  |   |                             |    |   IntegrationError          |   |  |
|  |   | AnalyzerFactory             |    |   (15 tipos totais)         |   |  |
|  |   | AnalyzerRegistry            |    |                             |   |  |
|  |   +-----------------------------+    +-----------------------------+   |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                     |                                        |
|                                     v                                        |
|  +------------------------------------------------------------------------+  |
|  |                       INFRASTRUCTURE LAYER                             |  |
|  |                                                                        |  |
|  |   +--------------------+  +--------------------+  +------------------+ |  |
|  |   |   boto3 Clients    |  |  AWS Integrations  |  |  State Manager   | |  |
|  |   |                    |  |                    |  |                  | |  |
|  |   |   ec2, s3, rds     |  |  Compute Optimizer |  |  S3 Storage      | |  |
|  |   |   lambda, ecs      |  |  Cost Explorer     |  |  DynamoDB State  | |  |
|  |   |   iam, cloudwatch  |  |  Trusted Advisor   |  |                  | |  |
|  |   |   (246 servicos)   |  |  Amazon Q Business |  |                  | |  |
|  |   |                    |  |                    |  |                  | |  |
|  |   +--------------------+  +--------------------+  +------------------+ |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                     |                                        |
|                                     v                                        |
|  +------------------------------------------------------------------------+  |
|  |                            AWS CLOUD                                   |  |
|  |                                                                        |  |
|  |   EC2   S3   RDS   Lambda   ECS   EKS   DynamoDB   CloudWatch         |  |
|  |   ELB   IAM   EBS   VPC     NAT   EIP   Route53    API Gateway        |  |
|  |   EMR   Glue  Kinesis  Redshift  ElastiCache  Aurora  ...             |  |
|  |                                                                        |  |
|  |                      (246 servicos suportados)                        |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

## 2.2 Fluxo de Requisicao

```
+-----------------------------------------------------------------------------+
|                       FLUXO DE REQUISICAO HTTP                              |
+-----------------------------------------------------------------------------+
|                                                                             |
|  1. Browser                                                                 |
|     |                                                                       |
|     | GET /api/v1/analyze?region=us-east-1                                 |
|     v                                                                       |
|  2. Flask Router (app.py)                                                   |
|     |                                                                       |
|     | @app.route('/api/v1/analyze')                                        |
|     | def analyze_endpoint():                                               |
|     v                                                                       |
|  3. Facade (analysis.py)                                                    |
|     |                                                                       |
|     | result = get_dashboard_analysis(region='us-east-1')                  |
|     v                                                                       |
|  4. Coleta Paralela                                                         |
|     |                                                                       |
|     +-----+-----+-----+-----+-----+-----+                                   |
|     |     |     |     |     |     |     |                                   |
|     v     v     v     v     v     v     v                                   |
|   Cost  Comp. Stor. Data. Netw. Sec.  Anal.                                 |
|   Expl. Anal. Anal. Anal. Anal. Anal. Anal.                                 |
|     |     |     |     |     |     |     |                                   |
|     +-----+-----+-----+-----+-----+-----+                                   |
|                     |                                                       |
|                     v                                                       |
|  5. Consolidacao                                                            |
|     |                                                                       |
|     | merge_results()                                                       |
|     | calculate_savings()                                                   |
|     | sort_by_priority()                                                    |
|     v                                                                       |
|  6. Response JSON                                                           |
|     |                                                                       |
|     | {                                                                     |
|     |   "costs": {...},                                                    |
|     |   "resources": {...},                                                |
|     |   "recommendations": [...],                                          |
|     |   "potential_savings": 123.45                                        |
|     | }                                                                     |
|     v                                                                       |
|  7. Dashboard Update                                                        |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 3. Stack Tecnologica

```
+==============================================================================+
|                          STACK TECNOLOGICA                                   |
+==============================================================================+
|                                                                              |
|  LINGUAGEM E RUNTIME                                                         |
|  ===================                                                         |
|                                                                              |
|  +---------------------+----------------------------------------------+      |
|  | Python              | 3.11                                        |      |
|  +---------------------+----------------------------------------------+      |
|  | Tipo                | Type hints completos (PEP 484)              |      |
|  +---------------------+----------------------------------------------+      |
|  | Async               | asyncio para operacoes paralelas            |      |
|  +---------------------+----------------------------------------------+      |
|                                                                              |
|  FRAMEWORK WEB                                                               |
|  =============                                                               |
|                                                                              |
|  +---------------------+----------------------------------------------+      |
|  | Flask               | 2.3+ (WSGI framework)                       |      |
|  +---------------------+----------------------------------------------+      |
|  | Jinja2              | Template engine para HTML                   |      |
|  +---------------------+----------------------------------------------+      |
|  | Werkzeug            | WSGI utilities                              |      |
|  +---------------------+----------------------------------------------+      |
|                                                                              |
|  AWS SDK                                                                     |
|  =======                                                                     |
|                                                                              |
|  +---------------------+----------------------------------------------+      |
|  | boto3               | 1.34+ (AWS SDK para Python)                 |      |
|  +---------------------+----------------------------------------------+      |
|  | botocore            | Core boto3                                  |      |
|  +---------------------+----------------------------------------------+      |
|                                                                              |
|  DEPENDENCIAS PRINCIPAIS                                                     |
|  =======================                                                     |
|                                                                              |
|  +---------------------+----------------------------------------------+      |
|  | dataclasses         | DTOs e Value Objects                        |      |
|  +---------------------+----------------------------------------------+      |
|  | typing              | Type hints                                  |      |
|  +---------------------+----------------------------------------------+      |
|  | abc                 | Abstract Base Classes                       |      |
|  +---------------------+----------------------------------------------+      |
|  | json                | Serializacao JSON                           |      |
|  +---------------------+----------------------------------------------+      |
|  | csv                 | Exportacao CSV                              |      |
|  +---------------------+----------------------------------------------+      |
|  | datetime            | Manipulacao de datas                        |      |
|  +---------------------+----------------------------------------------+      |
|                                                                              |
+==============================================================================+
```

---

# 4. Modulo de Analyzers

## 4.1 Visao Geral dos 6 Analyzers

```
+==============================================================================+
|                           OS 6 ANALYZERS                                     |
+==============================================================================+
|                                                                              |
|                          +------------------+                                |
|                          |  BaseAnalyzer    |                                |
|                          |  (ABC)           |                                |
|                          +--------+---------+                                |
|                                   |                                          |
|       +-------------+-------------+-------------+-------------+              |
|       |             |             |             |             |              |
|       v             v             v             v             v              |
|  +---------+  +---------+  +---------+  +---------+  +---------+            |
|  | COMPUTE |  | STORAGE |  | DATABASE|  | NETWORK |  | SECURITY|            |
|  +---------+  +---------+  +---------+  +---------+  +---------+            |
|  |         |  |         |  |         |  |         |  |         |            |
|  | EC2     |  | S3      |  | RDS     |  | ELB     |  | IAM     |            |
|  | Lambda  |  | EBS     |  | Aurora  |  | ALB     |  | CloudW. |            |
|  | ECS     |  | EFS     |  | DynamoDB|  | NLB     |  | ECR     |            |
|  | EKS     |  | Glacier |  | ElastiC.|  | CloudFr.|  | Logs    |            |
|  | EIP     |  |         |  | Redshift|  | API GW  |  |         |            |
|  | NAT GW  |  |         |  |         |  | Route53 |  |         |            |
|  |         |  |         |  |         |  |         |  |         |            |
|  +---------+  +---------+  +---------+  +---------+  +---------+            |
|                                                                              |
|                              +---------+                                     |
|                              |ANALYTICS|                                     |
|                              +---------+                                     |
|                              |         |                                     |
|                              | EMR     |                                     |
|                              | Kinesis |                                     |
|                              | Glue    |                                     |
|                              | Athena  |                                     |
|                              |         |                                     |
|                              +---------+                                     |
|                                                                              |
+==============================================================================+
```

## 4.2 Tabela de Verificacoes (23 Regras)

```
+==============================================================================+
|                    23 VERIFICACOES DE OTIMIZACAO                             |
+==============================================================================+
|                                                                              |
|  COMPUTE ANALYZER (6 verificacoes)                                          |
|  ================================                                            |
|                                                                              |
|  +----+-------------------+---------------------------+-------------------+  |
|  | #  | Recurso           | Verificacao               | Economia Estimada |  |
|  +----+-------------------+---------------------------+-------------------+  |
|  | 1  | EC2               | Instancias paradas        | EBS: $0.10/GB/mes |  |
|  | 2  | EC2               | Tipos de instancia antigos| 10-30% com Nitro  |  |
|  | 3  | EBS               | Volumes nao anexados      | $0.10/GB/mes      |  |
|  | 4  | EIP               | IPs nao associados        | $3.60/mes cada    |  |
|  | 5  | NAT Gateway       | Alertas de custo          | ~$32/mes base     |  |
|  | 6  | Lambda            | Timeout excessivo         | Variavel          |  |
|  +----+-------------------+---------------------------+-------------------+  |
|                                                                              |
|  STORAGE ANALYZER (4 verificacoes)                                          |
|  ================================                                            |
|                                                                              |
|  +----+-------------------+---------------------------+-------------------+  |
|  | #  | Recurso           | Verificacao               | Economia Estimada |  |
|  +----+-------------------+---------------------------+-------------------+  |
|  | 7  | S3                | Sem versionamento         | Governanca        |  |
|  | 8  | S3                | Sem lifecycle policy      | 40-90% storage    |  |
|  | 9  | S3                | Sem encryption            | Seguranca         |  |
|  | 10 | EFS               | Sem lifecycle policy      | 50%+ com IA       |  |
|  +----+-------------------+---------------------------+-------------------+  |
|                                                                              |
|  DATABASE ANALYZER (4 verificacoes)                                         |
|  =================================                                           |
|                                                                              |
|  +----+-------------------+---------------------------+-------------------+  |
|  | #  | Recurso           | Verificacao               | Economia Estimada |  |
|  +----+-------------------+---------------------------+-------------------+  |
|  | 11 | RDS               | Multi-AZ em dev           | 50% do custo      |  |
|  | 12 | RDS               | Instancias paradas        | Storage continua  |  |
|  | 13 | DynamoDB          | Billing mode inadequado   | Variavel          |  |
|  | 14 | ElastiCache       | Nodes subutilizados       | 30-50%            |  |
|  +----+-------------------+---------------------------+-------------------+  |
|                                                                              |
|  NETWORK ANALYZER (4 verificacoes)                                          |
|  ================================                                            |
|                                                                              |
|  +----+-------------------+---------------------------+-------------------+  |
|  | #  | Recurso           | Verificacao               | Economia Estimada |  |
|  +----+-------------------+---------------------------+-------------------+  |
|  | 15 | ELB/ALB/NLB       | Sem targets registrados   | $16-33/mes cada   |  |
|  | 16 | CloudFront        | Distributions inativas    | Variavel          |  |
|  | 17 | API Gateway       | APIs sem uso              | Por requisicao    |  |
|  | 18 | Route 53          | Hosted zones orfas        | $0.50/mes cada    |  |
|  +----+-------------------+---------------------------+-------------------+  |
|                                                                              |
|  SECURITY ANALYZER (3 verificacoes)                                         |
|  =================================                                           |
|                                                                              |
|  +----+-------------------+---------------------------+-------------------+  |
|  | #  | Recurso           | Verificacao               | Economia Estimada |  |
|  +----+-------------------+---------------------------+-------------------+  |
|  | 19 | IAM               | Access keys >90 dias      | Seguranca         |  |
|  | 20 | CloudWatch Logs   | Sem retention policy      | 80%+ storage      |  |
|  | 21 | ECR               | Imagens sem tag           | $0.10/GB/mes      |  |
|  +----+-------------------+---------------------------+-------------------+  |
|                                                                              |
|  ANALYTICS ANALYZER (2 verificacoes)                                        |
|  ==================================                                          |
|                                                                              |
|  +----+-------------------+---------------------------+-------------------+  |
|  | #  | Recurso           | Verificacao               | Economia Estimada |  |
|  +----+-------------------+---------------------------+-------------------+  |
|  | 22 | EMR               | Clusters longa duracao    | Variavel          |  |
|  | 23 | Redshift          | Clusters subutilizados    | 30-50%            |  |
|  +----+-------------------+---------------------------+-------------------+  |
|                                                                              |
+==============================================================================+
```

---

# 5. Integracoes AWS

## 5.1 Diagrama de Integracoes

```
+==============================================================================+
|                         4 INTEGRACOES AWS ATIVAS                             |
+==============================================================================+
|                                                                              |
|                          +-------------------+                               |
|                          |   FinOps AWS      |                               |
|                          |   Dashboard       |                               |
|                          +--------+----------+                               |
|                                   |                                          |
|          +------------+-----------+-----------+------------+                 |
|          |            |           |           |            |                 |
|          v            v           v           v            v                 |
|   +------------+ +------------+ +------------+ +------------+                |
|   | COMPUTE    | | COST       | | TRUSTED    | | AMAZON Q   |                |
|   | OPTIMIZER  | | EXPLORER   | | ADVISOR    | | BUSINESS   |                |
|   +------------+ +------------+ +------------+ +------------+                |
|   |            | |            | |            | |            |                |
|   | Right-     | | RI/SP      | | Best       | | AI         |                |
|   | sizing     | | Recommend. | | Practices  | | Insights   |                |
|   | EC2        | |            | | Checks     | |            |                |
|   |            | |            | |            | | 4 Personas |                |
|   +------------+ +------------+ +------------+ +------------+                |
|   |            | |            | |            | |            |                |
|   | Requisito: | | Requisito: | | Requisito: | | Requisito: |                |
|   | Opt-in     | | Dados de   | | Business/  | | Q_BUSINESS_|                |
|   | habilitado | | uso >7 dias| | Enterprise | | APP_ID     |                |
|   +------------+ +------------+ +------------+ +------------+                |
|                                                                              |
+==============================================================================+
```

## 5.2 Detalhes de Cada Integracao

```
+-----------------------------------------------------------------------------+
|                      1. AWS COMPUTE OPTIMIZER                               |
+-----------------------------------------------------------------------------+
|                                                                             |
|  FUNCAO: Right-sizing automatico de instancias EC2                         |
|                                                                             |
|  TIPOS DE RECOMENDACAO:                                                     |
|  +------------------+--------------------------------------------------+    |
|  | OVER_PROVISIONED | Instancia maior que o necessario                |    |
|  |                  | Economia: Migrar para tipo menor                |    |
|  +------------------+--------------------------------------------------+    |
|  | UNDER_PROVISIONED| Instancia menor que o necessario                |    |
|  |                  | Acao: Aumentar para evitar gargalos             |    |
|  +------------------+--------------------------------------------------+    |
|  | OPTIMIZED        | Instancia com tamanho adequado                  |    |
|  |                  | Nenhuma acao necessaria                         |    |
|  +------------------+--------------------------------------------------+    |
|                                                                             |
|  CODIGO DE INTEGRACAO:                                                      |
|                                                                             |
|  def get_compute_optimizer_recommendations(region: str) -> List[dict]:      |
|      co = boto3.client('compute-optimizer', region_name=region)             |
|      try:                                                                   |
|          response = co.get_ec2_instance_recommendations()                   |
|          return process_co_recommendations(response)                        |
|      except co.exceptions.OptInRequiredException:                           |
|          return []  # Compute Optimizer nao habilitado                      |
|                                                                             |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
|                       2. AWS COST EXPLORER                                  |
+-----------------------------------------------------------------------------+
|                                                                             |
|  FUNCAO: Recomendacoes de Reserved Instances e Savings Plans               |
|                                                                             |
|  TIPOS DE RECOMENDACAO:                                                     |
|  +-------------------+-------------------------------------------------+    |
|  | Reserved Instance | Compromisso 1-3 anos para EC2, RDS, ElastiCache|    |
|  |                   | Economia: 30-60% vs On-Demand                  |    |
|  +-------------------+-------------------------------------------------+    |
|  | Savings Plans     | Compromisso flexivel de uso                    |    |
|  |                   | Economia: 20-40% com flexibilidade             |    |
|  +-------------------+-------------------------------------------------+    |
|                                                                             |
|  CODIGO DE INTEGRACAO:                                                      |
|                                                                             |
|  def get_ri_recommendations(region: str) -> List[dict]:                     |
|      ce = boto3.client('ce', region_name='us-east-1')  # CE e global       |
|      response = ce.get_reservation_purchase_recommendation(                 |
|          Service='Amazon Elastic Compute Cloud - Compute',                  |
|          LookbackPeriodInDays='THIRTY_DAYS',                                |
|          TermInYears='ONE_YEAR',                                            |
|          PaymentOption='NO_UPFRONT'                                         |
|      )                                                                      |
|      return process_ri_recommendations(response)                            |
|                                                                             |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
|                      3. AWS TRUSTED ADVISOR                                 |
+-----------------------------------------------------------------------------+
|                                                                             |
|  FUNCAO: Verificacoes de boas praticas AWS (custo, seguranca, etc.)        |
|                                                                             |
|  CATEGORIAS:                                                                |
|  +-------------------+-------------------------------------------------+    |
|  | cost_optimizing   | Economia de custos                             |    |
|  | security          | Seguranca                                      |    |
|  | fault_tolerance   | Resiliencia                                    |    |
|  | performance       | Performance                                    |    |
|  | service_limits    | Limites de servico                             |    |
|  +-------------------+-------------------------------------------------+    |
|                                                                             |
|  REQUISITO: Plano de suporte Business ou Enterprise                        |
|                                                                             |
|  CODIGO DE INTEGRACAO:                                                      |
|                                                                             |
|  def get_trusted_advisor_checks() -> List[dict]:                            |
|      support = boto3.client('support', region_name='us-east-1')             |
|      try:                                                                   |
|          checks = support.describe_trusted_advisor_checks(                  |
|              language='en'                                                  |
|          )                                                                  |
|          cost_checks = [c for c in checks['checks']                         |
|                         if c['category'] == 'cost_optimizing']              |
|          return process_ta_checks(cost_checks)                              |
|      except support.exceptions.SubscriptionRequiredException:               |
|          return []  # Plano Basic nao tem acesso                            |
|                                                                             |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
|                      4. AMAZON Q BUSINESS                                   |
+-----------------------------------------------------------------------------+
|                                                                             |
|  FUNCAO: Analise inteligente com IA generativa                             |
|                                                                             |
|  4 PERSONAS DISPONIVEIS:                                                    |
|  +-------------+-------------------------------------------------------+    |
|  | EXECUTIVE   | CEO/CFO - Foco em ROI e decisoes estrategicas        |    |
|  +-------------+-------------------------------------------------------+    |
|  | CTO         | Lideranca tecnica - Arquitetura e modernizacao       |    |
|  +-------------+-------------------------------------------------------+    |
|  | DEVOPS      | Engenheiros - Scripts AWS CLI, implementacao         |    |
|  +-------------+-------------------------------------------------------+    |
|  | ANALYST     | FinOps - KPIs, metricas, benchmarks                   |    |
|  +-------------+-------------------------------------------------------+    |
|                                                                             |
|  REQUISITO: Q_BUSINESS_APPLICATION_ID configurado                          |
|                                                                             |
|  CODIGO DE INTEGRACAO:                                                      |
|                                                                             |
|  def get_amazon_q_insights(costs, resources, persona='EXECUTIVE'):          |
|      q_app_id = os.environ.get('Q_BUSINESS_APPLICATION_ID')                 |
|      if not q_app_id:                                                       |
|          return []                                                          |
|                                                                             |
|      q = boto3.client('qbusiness')                                          |
|      prompt = build_finops_prompt(costs, resources, persona)                |
|                                                                             |
|      response = q.chat_sync(                                                |
|          applicationId=q_app_id,                                            |
|          userMessage=prompt                                                 |
|      )                                                                      |
|      return response.get('systemMessage', '')                               |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 6. Amazon Q Business

## 6.1 Estrutura do Prompt

```
+==============================================================================+
|                      ESTRUTURA DO PROMPT AMAZON Q                            |
+==============================================================================+
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  ## Contexto do Sistema                                                |  |
|  |                                                                        |  |
|  |  Voce e um consultor senior de FinOps especializado em AWS,            |  |
|  |  com mais de 15 anos de experiencia em otimizacao de custos cloud.    |  |
|  |                                                                        |  |
|  |  Seu conhecimento inclui:                                              |  |
|  |  - Todos os 246 servicos AWS e seus modelos de precificacao           |  |
|  |  - AWS Well-Architected Framework (Cost Optimization Pillar)          |  |
|  |  - FinOps Framework e melhores praticas                               |  |
|  |  - Estrategias de Reserved Instances, Savings Plans e Spot            |  |
|  |  - Rightsizing, automacao e governanca de custos                      |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  ## Dados de Custo AWS                                                 |  |
|  |                                                                        |  |
|  |  **Custo Total (ultimos 30 dias):** $X.XX                             |  |
|  |                                                                        |  |
|  |  **Top Servicos por Custo:**                                          |  |
|  |    - Amazon RDS: $0.14                                                |  |
|  |    - Amazon S3: $0.004                                                |  |
|  |    - [outros servicos...]                                             |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  ## Recursos AWS Ativos                                                |  |
|  |                                                                        |  |
|  |    - ec2_instances: 0                                                  |  |
|  |    - s3_buckets: 1                                                     |  |
|  |    - rds_instances: 0                                                  |  |
|  |    - lambda_functions: 0                                               |  |
|  |    - [outros recursos...]                                             |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  ## Instrucoes                                                         |  |
|  |                                                                        |  |
|  |  [TEMPLATE ESPECIFICO DA PERSONA]                                      |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  ## Formato de Saida                                                   |  |
|  |                                                                        |  |
|  |  - Use Markdown com headers hierarquicos                               |  |
|  |  - Valores monetarios em USD                                          |  |
|  |  - Priorize por impacto financeiro                                    |  |
|  |  - Idioma: Portugues do Brasil                                        |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

## 6.2 Exemplos de Resposta por Persona

```
+-----------------------------------------------------------------------------+
|                     EXEMPLO: PERSONA EXECUTIVE                              |
+-----------------------------------------------------------------------------+
|                                                                             |
|  # Relatorio Executivo FinOps                                               |
|                                                                             |
|  ## Resumo Executivo                                                        |
|                                                                             |
|  O custo total foi de **$0.15**, distribuido entre RDS (95%) e S3 (3%).    |
|                                                                             |
|  ## Top 3 Oportunidades                                                     |
|                                                                             |
|  | # | Oportunidade         | Economia/Mes     |                          |
|  |---|----------------------|------------------|                          |
|  | 1 | Versionamento S3     | $0 (governanca)  |                          |
|  | 2 | Lifecycle policies   | $0-5             |                          |
|  | 3 | Dimensionamento RDS  | TBD              |                          |
|                                                                             |
|  ## Proximos Passos                                                         |
|                                                                             |
|  1. Habilitar versionamento S3 (esta semana)                               |
|  2. Implementar lifecycle policies (2 semanas)                             |
|  3. Revisar utilizacao RDS (este mes)                                      |
|                                                                             |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
|                        EXEMPLO: PERSONA CTO                                 |
+-----------------------------------------------------------------------------+
|                                                                             |
|  # Relatorio Tecnico FinOps                                                 |
|                                                                             |
|  ## Distribuicao de Recursos                                                |
|                                                                             |
|  | Categoria | Custo/Mes | % Total |                                       |
|  |-----------|-----------|---------|                                       |
|  | Database  | $0.14     | 95%     |                                       |
|  | Storage   | $0.004    | 3%      |                                       |
|                                                                             |
|  ## Roadmap de Modernizacao                                                 |
|                                                                             |
|  **Fase 1 (0-30d)**: Lifecycle policies S3                                 |
|  **Fase 2 (30-90d)**: Avaliar Aurora Serverless                            |
|  **Fase 3 (90-180d)**: FinOps as Code                                      |
|                                                                             |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
|                       EXEMPLO: PERSONA DEVOPS                               |
+-----------------------------------------------------------------------------+
|                                                                             |
|  # Relatorio Operacional                                                    |
|                                                                             |
|  ## Acao Imediata: Habilitar Versionamento S3                              |
|                                                                             |
|  ```bash                                                                    |
|  aws s3api put-bucket-versioning \                                         |
|    --bucket meu-bucket \                                                   |
|    --versioning-configuration Status=Enabled                               |
|  ```                                                                        |
|                                                                             |
|  ## Checklist                                                               |
|                                                                             |
|  - [ ] Habilitar versionamento S3                                          |
|  - [ ] Configurar lifecycle policies                                       |
|  - [ ] Criar alarme de custo                                               |
|                                                                             |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
|                       EXEMPLO: PERSONA ANALYST                              |
+-----------------------------------------------------------------------------+
|                                                                             |
|  # Relatorio Analitico FinOps                                               |
|                                                                             |
|  ## Dashboard de Metricas                                                   |
|                                                                             |
|  | KPI             | Valor  | Meta  | Status |                             |
|  |-----------------|--------|-------|--------|                             |
|  | Custo Total     | $0.15  | $10   | OK     |                             |
|  | Cobertura RI/SP | 0%     | 70%   | ALERTA |                             |
|  | Waste Ratio     | 0%     | <5%   | OK     |                             |
|                                                                             |
|  ## Analise por Servico                                                     |
|                                                                             |
|  | Servico | Custo  | % Total | Tendencia  |                              |
|  |---------|--------|---------|------------|                              |
|  | RDS     | $0.14  | 95%     | Estavel    |                              |
|  | S3      | $0.004 | 3%      | Estavel    |                              |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 7. API Endpoints

```
+==============================================================================+
|                           API ENDPOINTS                                      |
+==============================================================================+
|                                                                              |
|  BASE URL: http://localhost:5000                                             |
|                                                                              |
|  +--------+---------------------+--------------------------------------------+
|  | Metodo | Endpoint            | Descricao                                 |
|  +--------+---------------------+--------------------------------------------+
|  | GET    | /                   | Dashboard HTML principal                  |
|  +--------+---------------------+--------------------------------------------+
|  | GET    | /api/v1/analyze     | Analise completa (custos + recomendacoes)|
|  +--------+---------------------+--------------------------------------------+
|  | GET    | /api/v1/costs       | Apenas dados de custo                    |
|  +--------+---------------------+--------------------------------------------+
|  | GET    | /api/v1/recommend   | Apenas recomendacoes                     |
|  +--------+---------------------+--------------------------------------------+
|  | GET    | /api/v1/multi-region| Analise multi-region                     |
|  +--------+---------------------+--------------------------------------------+
|  | GET    | /export/csv         | Exportar para CSV                        |
|  +--------+---------------------+--------------------------------------------+
|  | GET    | /export/json        | Exportar para JSON                       |
|  +--------+---------------------+--------------------------------------------+
|  | GET    | /print              | Versao para impressao                    |
|  +--------+---------------------+--------------------------------------------+
|                                                                              |
|  PARAMETROS COMUNS:                                                          |
|  +------------------+-------------------------------------------------------+
|  | region           | Regiao AWS (default: us-east-1)                      |
|  | include_costs    | Incluir dados de custo (default: true)               |
|  | include_recs     | Incluir recomendacoes (default: true)                |
|  | persona          | Persona Amazon Q (EXECUTIVE, CTO, DEVOPS, ANALYST)   |
|  +------------------+-------------------------------------------------------+
|                                                                              |
+==============================================================================+
```

---

# 8. Configuracao

```
+==============================================================================+
|                           CONFIGURACAO                                       |
+==============================================================================+
|                                                                              |
|  VARIAVEIS DE AMBIENTE                                                       |
|  =====================                                                       |
|                                                                              |
|  +-----------------------------+--------------+-----------------------------+
|  | Variavel                    | Obrigatorio  | Descricao                   |
|  +-----------------------------+--------------+-----------------------------+
|  | AWS_ACCESS_KEY_ID           | Sim          | Access Key da conta AWS     |
|  +-----------------------------+--------------+-----------------------------+
|  | AWS_SECRET_ACCESS_KEY       | Sim          | Secret Key da conta AWS     |
|  +-----------------------------+--------------+-----------------------------+
|  | AWS_REGION                  | Nao          | Regiao padrao (us-east-1)   |
|  +-----------------------------+--------------+-----------------------------+
|  | Q_BUSINESS_APPLICATION_ID   | Nao          | ID do app Amazon Q Business |
|  +-----------------------------+--------------+-----------------------------+
|                                                                              |
|  PERMISSOES IAM NECESSARIAS                                                  |
|  ==========================                                                  |
|                                                                              |
|  {                                                                           |
|    "Version": "2012-10-17",                                                  |
|    "Statement": [                                                            |
|      {                                                                       |
|        "Effect": "Allow",                                                    |
|        "Action": [                                                           |
|          "ce:GetCostAndUsage",                                               |
|          "ce:GetReservationPurchaseRecommendation",                          |
|          "ce:GetSavingsPlansPurchaseRecommendation",                         |
|          "compute-optimizer:GetEC2InstanceRecommendations",                  |
|          "support:DescribeTrustedAdvisorChecks",                             |
|          "ec2:Describe*",                                                    |
|          "s3:List*",                                                         |
|          "rds:Describe*",                                                    |
|          "lambda:List*",                                                     |
|          "ecs:List*",                                                        |
|          "elasticloadbalancing:Describe*",                                   |
|          "iam:List*",                                                        |
|          "cloudwatch:GetMetricData"                                          |
|        ],                                                                    |
|        "Resource": "*"                                                       |
|      }                                                                       |
|    ]                                                                         |
|  }                                                                           |
|                                                                              |
+==============================================================================+
```

---

# 9. Testes

```
+==============================================================================+
|                              TESTES                                          |
+==============================================================================+
|                                                                              |
|  RESUMO                                                                      |
|  ======                                                                      |
|                                                                              |
|  +------------------+-------------+-------------+-------------+              |
|  | Categoria        | Quantidade  | Passando    | Status      |              |
|  +------------------+-------------+-------------+-------------+              |
|  | Unit Tests       | 1,865       | 100%        | OK          |              |
|  +------------------+-------------+-------------+-------------+              |
|  | Integration      | 44          | 95.5%       | OK          |              |
|  +------------------+-------------+-------------+-------------+              |
|  | QA Tests         | 240         | 100%        | OK          |              |
|  +------------------+-------------+-------------+-------------+              |
|  | E2E Tests        | 55          | 100%        | OK          |              |
|  +------------------+-------------+-------------+-------------+              |
|  | TOTAL            | 2,204       | 100%        | OK          |              |
|  +------------------+-------------+-------------+-------------+              |
|                                                                              |
|  EXECUTAR TESTES                                                             |
|  ===============                                                             |
|                                                                              |
|  # Todos os testes                                                           |
|  pytest tests/ -v                                                            |
|                                                                              |
|  # Apenas unit tests                                                         |
|  pytest tests/unit/ -v                                                       |
|                                                                              |
|  # Apenas integration tests                                                  |
|  pytest tests/integration/ -v                                                |
|                                                                              |
|  # Com cobertura                                                             |
|  pytest tests/ --cov=src/finops_aws --cov-report=html                        |
|                                                                              |
+==============================================================================+
```

---

# 10. Deploy e Operacao

```
+==============================================================================+
|                         DEPLOY E OPERACAO                                    |
+==============================================================================+
|                                                                              |
|  DESENVOLVIMENTO LOCAL                                                       |
|  =====================                                                       |
|                                                                              |
|  # 1. Configurar variaveis de ambiente                                       |
|  export AWS_ACCESS_KEY_ID=sua-access-key                                     |
|  export AWS_SECRET_ACCESS_KEY=sua-secret-key                                 |
|  export AWS_REGION=us-east-1                                                 |
|                                                                              |
|  # 2. Instalar dependencias                                                  |
|  pip install -r requirements.txt                                             |
|                                                                              |
|  # 3. Executar servidor                                                      |
|  python app.py                                                               |
|                                                                              |
|  # 4. Acessar dashboard                                                      |
|  http://localhost:5000                                                       |
|                                                                              |
|  DEPLOY AWS LAMBDA (FUTURO)                                                  |
|  ==========================                                                  |
|                                                                              |
|  # Empacotamento                                                             |
|  sam build                                                                   |
|                                                                              |
|  # Deploy                                                                    |
|  sam deploy --guided                                                         |
|                                                                              |
|  MONITORAMENTO                                                               |
|  =============                                                               |
|                                                                              |
|  - CloudWatch Logs para logs de execucao                                    |
|  - CloudWatch Metrics para metricas customizadas                            |
|  - X-Ray para tracing distribuido                                           |
|                                                                              |
+==============================================================================+
```

---

```
+==============================================================================+
|                                                                              |
|                      FIM DO GUIA TECNICO                                    |
|                                                                              |
|   Versao 2.0 - Dezembro 2024                                                |
|   FinOps AWS - Enterprise-Grade Solution                                    |
|                                                                              |
+==============================================================================+
```
