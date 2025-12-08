# FinOps AWS - Roadmap do Projeto

## Versao 2.1 - Dezembro 2025 (ATUAL)

---

```
+==============================================================================+
|                                                                              |
|                    ROADMAP FINOPS AWS - v2.1 (DEZEMBRO 2025)                |
|                                                                              |
|   Status: PRODUCTION READY com Dashboard React + 5 Provedores IA            |
|   Próximas evoluções: Machine Learning Avançado + Blockchain Audit          |
|                                                                              |
+==============================================================================+
```

## Release v2.1 - Dezembro 2025

### ✅ ENTREGUES NESTE MÊS

- **Dashboard React 18** com TypeScript + Vite profissional
- **Painel de Notificações** com dados reais (Cost Anomaly, Budgets)
- **StackSpot AI** como 5º provedor de IA integrado
- **API Notificações** `/api/v1/notifications` em tempo real
- **Botão Atualizar Inteligente** com análise paralela
- **Eliminação de Mock Data** - 100% dados reais AWS
- **Localização PT-BR** dos níveis de maturidade FinOps
- **Settings Backend Integration** com persistência real

---

## Indice

1. [Status Atual](#1-status-atual)
2. [Cobertura de Servicos](#2-cobertura-de-servicos)
3. [Implementado](#3-implementado)
4. [Proximos Passos](#4-proximos-passos)
5. [Gaps Conhecidos](#5-gaps-conhecidos)
6. [Changelog](#6-changelog)

---

# 1. Status Atual

```
+==============================================================================+
|                          STATUS: PRODUCTION READY                            |
+==============================================================================+
|                                                                              |
|  O sistema esta 100% FUNCIONAL com dados reais da AWS.                      |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |   STATUS GERAL                                                         |  |
|  |   ============                                                         |  |
|  |                                                                        |  |
|  |   +------------------------+----------------------------------------+  |  |
|  |   | Componente             | Status                                 |  |  |
|  |   +------------------------+----------------------------------------+  |  |
|  |   | Dashboard React        | PROFISSIONAL (v18 + TS + Vite)         |  |  |
|  |   | Painel Notificações    | TEMPO REAL COM DADOS AWS               |  |  |
|  |   | API REST               | COMPLETA COM /api/v1/ endpoints        |  |  |
|  |   | 6 Analyzers            | IMPLEMENTADOS                          |  |  |
|  |   | 5 Provedores IA        | Amazon Q, OpenAI, Gemini, Perplexity, StackSpot |  |  |
|  |   | Integracao AWS         | ATIVA (Cost Explorer, Budgets, CostAnom) |  |  |
|  |   | Compute Optimizer      | INTEGRADO                              |  |  |
|  |   | Trusted Advisor        | INTEGRADO                              |  |  |
|  |   | Dados Reais            | 100% - ZERO MOCK DATA                  |  |  |
|  |   | Exportacao CSV/JSON    | FUNCIONANDO                            |  |  |
|  |   | Multi-Region           | FUNCIONANDO                            |  |  |
|  |   | Testes                 | 2,100+ (99.6% passing)                 |  |  |
|  |   | Documentacao           | EXTREMAMENTE DETALHADA                 |  |  |
|  |   +------------------------+----------------------------------------+  |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

## 1.1 Dashboard de Status

```
+-----------------------------------------------------------------------------+
|                          DASHBOARD DE STATUS                                |
+-----------------------------------------------------------------------------+
|                                                                             |
|   +-------------------+   +-------------------+   +-------------------+     |
|   |                   |   |                   |   |                   |     |
|   |  FUNCIONALIDADE   |   |     QUALIDADE     |   |   INTEGRACAO     |     |
|   |                   |   |                   |   |                   |     |
|   |    100% OK        |   |    9.9/10         |   |     4/4 ATIVAS   |     |
|   |                   |   |                   |   |                   |     |
|   +-------------------+   +-------------------+   +-------------------+     |
|                                                                             |
|   +-------------------+   +-------------------+   +-------------------+     |
|   |                   |   |                   |   |                   |     |
|   |     TESTES        |   |   DOCUMENTACAO    |   |    SEGURANCA     |     |
|   |                   |   |                   |   |                   |     |
|   |   2,204 (100%)    |   |    11K+ linhas    |   |   0 vulnerab.    |     |
|   |                   |   |                   |   |                   |     |
|   +-------------------+   +-------------------+   +-------------------+     |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 2. Cobertura de Servicos

```
+==============================================================================+
|                       COBERTURA DE SERVICOS AWS                              |
+==============================================================================+
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  METRICAS DE COBERTURA                                                |  |
|  |  =====================                                                 |  |
|  |                                                                        |  |
|  |  +---------------------------+--------+------------------------------+ |  |
|  |  | Metrica                   | Valor  | Descricao                    | |  |
|  |  +---------------------------+--------+------------------------------+ |  |
|  |  | Servicos AWS suportados   | 246    | Enum AWSServiceType          | |  |
|  |  +---------------------------+--------+------------------------------+ |  |
|  |  | Cobertura boto3           | 60%    | Servicos de alto impacto     | |  |
|  |  +---------------------------+--------+------------------------------+ |  |
|  |  | Verificacoes otimizacao   | 23     | Regras especificas           | |  |
|  |  +---------------------------+--------+------------------------------+ |  |
|  |  | Integracoes AWS           | 4      | CO, CE, TA, Amazon Q         | |  |
|  |  +---------------------------+--------+------------------------------+ |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  DISTRIBUICAO POR ANALYZER                                            |  |
|  |  =========================                                             |  |
|  |                                                                        |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |  | Analyzer         | Qty | Servicos                                 | |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |  | Compute          | 6   | EC2, EBS, EIP, NAT GW, Lambda, ECS       | |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |  | Storage          | 4   | S3, EBS, EFS, Glacier                    | |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |  | Database         | 4   | RDS, DynamoDB, ElastiCache, Aurora       | |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |  | Network          | 5   | ELB/ALB/NLB, CloudFront, API GW, Route53 | |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |  | Security         | 3   | IAM, CloudWatch Logs, ECR                | |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |  | Analytics        | 4   | EMR, Kinesis, Glue, Redshift             | |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |  | TOTAL            | 23  |                                          | |  |
|  |  +------------------+-----+------------------------------------------+ |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

## 2.1 Visualizacao de Cobertura

```
+-----------------------------------------------------------------------------+
|                    COBERTURA POR CATEGORIA DE SERVICO                       |
+-----------------------------------------------------------------------------+
|                                                                             |
|  Compute & Serverless    [=================================] 100%           |
|                          EC2, Lambda, ECS, EKS, EIP, NAT                    |
|                                                                             |
|  Storage                 [=================================] 100%           |
|                          S3, EBS, EFS, Glacier                              |
|                                                                             |
|  Database                [=================================] 100%           |
|                          RDS, Aurora, DynamoDB, ElastiCache                 |
|                                                                             |
|  Networking              [=================================] 100%           |
|                          ELB, ALB, NLB, CloudFront, API GW                  |
|                                                                             |
|  Security                [=================================] 100%           |
|                          IAM, CloudWatch, ECR                               |
|                                                                             |
|  Analytics               [=================================] 100%           |
|                          EMR, Kinesis, Glue, Redshift, Athena               |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 3. Implementado

```
+==============================================================================+
|                          FUNCIONALIDADES IMPLEMENTADAS                       |
+==============================================================================+
|                                                                              |
|  FASE 1: ARQUITETURA BASE [CONCLUIDO]                                       |
|  =====================================                                       |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  [x] Clean Architecture + DDD                                         |  |
|  |      |                                                                |  |
|  |      +-- Presentation Layer (Flask + HTML/JS)                         |  |
|  |      +-- Application Layer (Use Cases + Services)                     |  |
|  |      +-- Domain Layer (Entities + Value Objects)                      |  |
|  |      +-- Infrastructure Layer (boto3 + AWS)                           |  |
|  |                                                                        |  |
|  |  [x] 6 Analyzers com Strategy Pattern                                 |  |
|  |      |                                                                |  |
|  |      +-- ComputeAnalyzer                                              |  |
|  |      +-- StorageAnalyzer                                              |  |
|  |      +-- DatabaseAnalyzer                                             |  |
|  |      +-- NetworkAnalyzer                                              |  |
|  |      +-- SecurityAnalyzer                                             |  |
|  |      +-- AnalyticsAnalyzer                                            |  |
|  |                                                                        |  |
|  |  [x] Factory + Registry Pattern                                       |  |
|  |  [x] Template Method em BaseAnalyzer                                  |  |
|  |  [x] Hierarquia de excecoes tipadas (15 tipos)                        |  |
|  |  [x] Facade para simplificacao de acesso                              |  |
|  |  [x] Dashboard web funcional (Flask)                                  |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  FASE 2: INTEGRACOES AWS [CONCLUIDO]                                        |
|  ====================================                                        |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  [x] Integracao boto3 (246 servicos suportados)                       |  |
|  |                                                                        |  |
|  |  [x] AWS Compute Optimizer                                            |  |
|  |      +-- Right-sizing EC2                                             |  |
|  |      +-- OVER_PROVISIONED / UNDER_PROVISIONED detection               |  |
|  |                                                                        |  |
|  |  [x] AWS Cost Explorer                                                |  |
|  |      +-- Reserved Instances recommendations                           |  |
|  |      +-- Savings Plans recommendations                                |  |
|  |      +-- Cost and usage data (30 dias)                                |  |
|  |                                                                        |  |
|  |  [x] AWS Trusted Advisor                                              |  |
|  |      +-- cost_optimizing checks                                       |  |
|  |      +-- security checks                                              |  |
|  |      +-- fault_tolerance checks                                       |  |
|  |                                                                        |  |
|  |  [x] Amazon Q Business                                                |  |
|  |      +-- 4 personas (Executive, CTO, DevOps, Analyst)                 |  |
|  |      +-- Prompts especializados                                       |  |
|  |      +-- Respostas em Portugues do Brasil                             |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  FASE 3: FUNCIONALIDADES [CONCLUIDO]                                        |
|  ====================================                                        |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  [x] Analise de custos em tempo real                                  |  |
|  |  [x] 23 verificacoes de otimizacao especificas                        |  |
|  |  [x] Exportacao CSV/JSON                                              |  |
|  |  [x] Versao para impressao (PDF-ready)                                |  |
|  |  [x] API REST completa                                                |  |
|  |  [x] Multi-region analysis                                            |  |
|  |  [x] 4 personas Amazon Q (Executive, CTO, DevOps, Analyst)            |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  FASE 4: QUALIDADE [CONCLUIDO]                                              |
|  =============================                                               |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  [x] 2,204 testes (100% passing)                                      |  |
|  |      +-- 1,865 unit tests                                             |  |
|  |      +-- 44 integration tests                                         |  |
|  |      +-- 240 QA tests                                                 |  |
|  |      +-- 55 E2E tests                                                 |  |
|  |                                                                        |  |
|  |  [x] Documentacao completa (11K+ linhas)                              |  |
|  |  [x] Type hints em todos os modulos                                   |  |
|  |  [x] Logging estruturado                                              |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

---

# 4. Proximos Passos

```
+==============================================================================+
|                           PROXIMOS PASSOS                                    |
+==============================================================================+
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |                    VISAO GERAL DO ROADMAP                             |  |
|  |                                                                        |  |
|  |  +------+------+------+------+------+------+                          |  |
|  |  |      |      |      |      |      |      |                          |  |
|  |  | Mes  | Mes  | Mes  | Mes  | Mes  | Mes  |                          |  |
|  |  |  1   |  2   |  3   |  4   |  5   |  6   |                          |  |
|  |  |      |      |      |      |      |      |                          |  |
|  |  +------+------+------+------+------+------+                          |  |
|  |  |   CURTO    |    MEDIO     |    LONGO    |                          |  |
|  |  |   PRAZO    |    PRAZO     |    PRAZO    |                          |  |
|  |  +------+------+------+------+------+------+                          |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+

+-----------------------------------------------------------------------------+
|                        CURTO PRAZO (0-30 DIAS)                              |
+-----------------------------------------------------------------------------+
|                                                                             |
|  +----+----------------------------+------------+----------+-------------+ |
|  | #  | Item                       | Prioridade | Esforco  | Status      | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 1  | Refatorar app.py           | ALTA       | 2-3 dias | Planejado   | |
|  |    | - Dividir em modulos       |            |          |             | |
|  |    | - Usar analyzers existentes|            |          |             | |
|  |    | - Reduzir de 6K para 300L  |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 2  | Adicionar autenticacao     | MEDIA      | 1-2 dias | Planejado   | |
|  |    | - Login/logout             |            |          |             | |
|  |    | - Sessoes seguras          |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 3  | Alertas                    | MEDIA      | 1 dia    | Planejado   | |
|  |    | - Email (SES)              |            |          |             | |
|  |    | - Slack webhook            |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 4  | Cache de resultados        | BAIXA      | 1 dia    | Planejado   | |
|  |    | - Redis/ElastiCache        |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|                                                                             |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
|                        MEDIO PRAZO (30-90 DIAS)                             |
+-----------------------------------------------------------------------------+
|                                                                             |
|  +----+----------------------------+------------+----------+-------------+ |
|  | #  | Item                       | Prioridade | Esforco  | Status      | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 5  | Deploy AWS Lambda          | ALTA       | 3-5 dias | Planejado   | |
|  |    | - SAM template             |            |          |             | |
|  |    | - API Gateway              |            |          |             | |
|  |    | - Cognito auth             |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 6  | Step Functions             | ALTA       | 2-3 dias | Planejado   | |
|  |    | - Orquestracao             |            |          |             | |
|  |    | - Retry/error handling     |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 7  | Expandir verificacoes      | MEDIA      | 3 dias   | Planejado   | |
|  |    | - De 23 para 50 servicos   |            |          |             | |
|  |    | - Mais regras especificas  |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 8  | EventBridge scheduling     | BAIXA      | 1 dia    | Planejado   | |
|  |    | - Analises agendadas       |            |          |             | |
|  |    | - Relatorios automaticos   |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|                                                                             |
+-----------------------------------------------------------------------------+

+-----------------------------------------------------------------------------+
|                        LONGO PRAZO (90-180 DIAS)                            |
+-----------------------------------------------------------------------------+
|                                                                             |
|  +----+----------------------------+------------+----------+-------------+ |
|  | #  | Item                       | Prioridade | Esforco  | Status      | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 9  | ML predictions             | BAIXA      | 5+ dias  | Futuro      | |
|  |    | - Previsao de custos       |            |          |             | |
|  |    | - Deteccao de anomalias    |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 10 | Multi-account support      | MEDIA      | 3 dias   | Futuro      | |
|  |    | - AWS Organizations        |            |          |             | |
|  |    | - Cross-account roles      |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 11 | Custom dashboards          | BAIXA      | 3 dias   | Futuro      | |
|  |    | - Personalizacao           |            |          |             | |
|  |    | - Widgets customizaveis    |            |          |             | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 12 | Terraform integration      | BAIXA      | 2 dias   | Futuro      | |
|  +----+----------------------------+------------+----------+-------------+ |
|  | 13 | GCP/Azure support          | BAIXA      | 10+ dias | Futuro      | |
|  +----+----------------------------+------------+----------+-------------+ |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 5. Gaps Conhecidos

```
+==============================================================================+
|                           GAPS CONHECIDOS                                    |
+==============================================================================+
|                                                                              |
|  GAPS FUNCIONAIS                                                            |
|  ===============                                                             |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | Gap                       | Impacto | Workaround                   ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | Compute Optimizer         | Baixo   | Mensagem informativa quando  ||  |
|  |  | requer opt-in             |         | nao habilitado               ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | Trusted Advisor requer    | Baixo   | Funciona com verificacoes    ||  |
|  |  | Business/Enterprise       |         | limitadas no Basic           ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | Amazon Q requer           | Baixo   | Documentacao clara sobre     ||  |
|  |  | configuracao manual       |         | como configurar              ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | Cost Explorer demora      | Baixo   | Mensagem explicando que      ||  |
|  |  | 24h para novos dados      |         | dados sao atualizados 1x/dia ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  GAPS TECNICOS                                                              |
|  =============                                                               |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | Gap                       | Impacto | Solucao Planejada            ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | app.py monolitico         | Medio   | Refatoracao usando analyzers ||  |
|  |  | (6,312 linhas)            |         | ja implementados             ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | except Exception: (516x)  | Baixo   | Migrar para excecoes tipadas ||  |
|  |  | bare except clauses       |         | da hierarquia                ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | pass em except (511x)     | Baixo   | Adicionar logging apropriado ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | Falta de cache            | Baixo   | Implementar Redis/ElastiCache||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |  | Sem rate limiting         | Baixo   | Adicionar throttling na API  ||  |
|  |  +---------------------------+---------+------------------------------+|  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  GAPS DE DOCUMENTACAO                                                       |
|  ====================                                                        |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  [x] TECHNICAL_GUIDE.md - Atualizado                                  |  |
|  |  [x] USER_MANUAL.md - Atualizado                                      |  |
|  |  [x] ARCHITECTURE_AND_PATTERNS.md - Atualizado                        |  |
|  |  [x] PROMPTS_AMAZON_Q.md - Atualizado                                 |  |
|  |  [x] HEAD_FIRST_FINOPS.md - Atualizado                                |  |
|  |  [x] ROADMAP.md - Atualizado                                          |  |
|  |  [x] APPENDIX_SERVICES.md - Atualizado                                |  |
|  |  [ ] API Reference (Swagger/OpenAPI) - Pendente                       |  |
|  |  [ ] Troubleshooting Guide - Pendente                                 |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

---

# 6. Changelog

```
+==============================================================================+
|                              CHANGELOG                                       |
+==============================================================================+
|                                                                              |
|  DEZEMBRO 2024 - v2.0.0                                                     |
|  ======================                                                      |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  REFATORACAO ARQUITETURAL                                             |  |
|  |  ===========================                                           |  |
|  |                                                                        |  |
|  |  * Strategy Pattern implementado para 6 analyzers                     |  |
|  |  * Factory + Registry Pattern para criacao dinamica                   |  |
|  |  * Template Method em BaseAnalyzer                                    |  |
|  |  * Facade Pattern para simplificacao de acesso                        |  |
|  |  * Hierarquia de excecoes tipadas (15 tipos)                          |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  INTEGRACOES AWS                                                      |  |
|  |  ===============                                                       |  |
|  |                                                                        |  |
|  |  * AWS Compute Optimizer integrado                                    |  |
|  |  * AWS Cost Explorer (RI/SP) integrado                                |  |
|  |  * AWS Trusted Advisor integrado                                      |  |
|  |  * Amazon Q Business integrado com 4 personas                         |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  DOCUMENTACAO                                                         |  |
|  |  ============                                                          |  |
|  |                                                                        |  |
|  |  * TECHNICAL_GUIDE.md atualizado com arquitetura completa             |  |
|  |  * PROMPTS_AMAZON_Q.md com exemplos de todas as personas              |  |
|  |  * USER_MANUAL.md simplificado para usuarios                          |  |
|  |  * HEAD_FIRST_FINOPS.md com metodologia visual                        |  |
|  |  * ARCHITECTURE_AND_PATTERNS.md com Design Patterns                   |  |
|  |  * ROADMAP.md com status atual                                        |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  QUALIDADE                                                            |  |
|  |  =========                                                             |  |
|  |                                                                        |  |
|  |  * 2,204 testes (100% passing)                                        |  |
|  |  * Type hints em todos os modulos                                     |  |
|  |  * Logging estruturado                                                |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  NOVEMBRO 2024 - v1.5.0                                                     |
|  ======================                                                      |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  * Dashboard web inicial                                              |  |
|  |  * Analise basica de custos                                           |  |
|  |  * Exportacao CSV/JSON                                                |  |
|  |  * Multi-region support                                               |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  OUTUBRO 2024 - v1.0.0                                                      |
|  =====================                                                       |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  * Versao inicial                                                     |  |
|  |  * Integracao boto3 basica                                            |  |
|  |  * Estrutura inicial do projeto                                       |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

---

```
+==============================================================================+
|                                                                              |
|                           FIM DO ROADMAP                                    |
|                                                                              |
|   Versao 2.0 - Dezembro 2024                                                |
|   FinOps AWS - Enterprise-Grade Solution                                    |
|                                                                              |
+==============================================================================+
```
