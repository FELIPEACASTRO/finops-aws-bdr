# FinOps AWS - Manual do Usuario

## Versao 2.0 - Dezembro 2024

---

```
+==============================================================================+
|                                                                              |
|                    MANUAL DO USUARIO - FINOPS AWS                           |
|                                                                              |
|   Guia completo para usar o Dashboard FinOps AWS e otimizar seus custos.    |
|                                                                              |
+==============================================================================+
```

---

## Indice

1. [Introducao](#1-introducao)
2. [Acessando o Dashboard](#2-acessando-o-dashboard)
3. [Visao Geral do Dashboard](#3-visao-geral-do-dashboard)
4. [Analise de Custos](#4-analise-de-custos)
5. [Recomendacoes de Otimizacao](#5-recomendacoes-de-otimizacao)
6. [Integracoes AWS](#6-integracoes-aws)
7. [Exportacao de Dados](#7-exportacao-de-dados)
8. [Amazon Q - Consultor IA](#8-amazon-q-consultor-ia)
9. [Perguntas Frequentes](#9-perguntas-frequentes)
10. [Glossario](#10-glossario)

---

# 1. Introducao

## 1.1 O que e o FinOps AWS?

```
+-----------------------------------------------------------------------------+
|                                                                             |
|  O FinOps AWS e uma ferramenta visual para ANALISAR e OTIMIZAR seus        |
|  custos na Amazon Web Services (AWS).                                       |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                                                                       |  |
|  |   O QUE O FINOPS AWS FAZ POR VOCE:                                   |  |
|  |                                                                       |  |
|  |   [x] Mostra QUANTO voce esta gastando na AWS                        |  |
|  |   [x] Identifica ONDE voce pode economizar                           |  |
|  |   [x] Sugere COMO reduzir custos                                     |  |
|  |   [x] Gera RELATORIOS automaticos                                    |  |
|  |                                                                       |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
+-----------------------------------------------------------------------------+
```

## 1.2 Para quem e este manual?

Este manual foi criado para:

- Gerentes que precisam entender os custos AWS
- Equipes de TI que gerenciam infraestrutura
- Analistas financeiros que acompanham gastos cloud
- Qualquer pessoa que quer economizar na AWS

---

# 2. Acessando o Dashboard

## 2.1 Como Acessar

```
+-----------------------------------------------------------------------------+
|                                                                             |
|  PASSO A PASSO PARA ACESSAR:                                                |
|                                                                             |
|  1. Abra seu navegador (Chrome, Firefox, Edge, Safari)                      |
|                                                                             |
|  2. Digite a URL do dashboard                                               |
|     |                                                                       |
|     +---> Se for local: http://localhost:5000                              |
|     +---> Se for na nuvem: https://seu-dominio.com                         |
|                                                                             |
|  3. Aguarde carregar                                                        |
|     |                                                                       |
|     +---> Voce vera: "Buscando dados da AWS..."                            |
|     +---> Isso pode levar alguns segundos                                  |
|                                                                             |
|  4. Pronto! O dashboard aparecera                                           |
|                                                                             |
+-----------------------------------------------------------------------------+
```

## 2.2 Primeira Visualizacao

```
+-----------------------------------------------------------------------------+
|                                                                             |
|  Quando voce acessa o dashboard pela primeira vez, vera:                    |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                     FINOPS AWS DASHBOARD                              |  |
|  +-----------------------------------------------------------------------+  |
|  |                                                                       |  |
|  |   +-----------+  +-----------+  +-----------+  +-----------+         |  |
|  |   | CUSTO     |  | ECONOMIA  |  | SERVICOS  |  | RECOMEN-  |         |  |
|  |   | TOTAL     |  | POTENCIAL |  | ANALISADOS|  | DACOES    |         |  |
|  |   |           |  |           |  |           |  |           |         |  |
|  |   | $1,234.56 |  | $234.56   |  | 246       |  | 15        |         |  |
|  |   +-----------+  +-----------+  +-----------+  +-----------+         |  |
|  |                                                                       |  |
|  |   [Analise Completa] [Apenas Custos] [Apenas Recs] [Multi-Region]    |  |
|  |                                                                       |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 3. Visao Geral do Dashboard

## 3.1 Os 4 Cards Principais

```
+==============================================================================+
|                        OS 4 CARDS DO DASHBOARD                               |
+==============================================================================+
|                                                                              |
|  +---------------------------+  +---------------------------+                |
|  |                           |  |                           |                |
|  |  CUSTO TOTAL (30 DIAS)    |  |  ECONOMIA POTENCIAL       |                |
|  |  =====================    |  |  ===================       |                |
|  |                           |  |                           |                |
|  |  Quanto voce gastou nos   |  |  Quanto voce PODE         |                |
|  |  ultimos 30 dias na AWS.  |  |  economizar seguindo      |                |
|  |                           |  |  as recomendacoes.        |                |
|  |  Exemplo: $1,234.56       |  |  Exemplo: $234.56         |                |
|  |                           |  |                           |                |
|  +---------------------------+  +---------------------------+                |
|                                                                              |
|  +---------------------------+  +---------------------------+                |
|  |                           |  |                           |                |
|  |  SERVICOS ANALISADOS      |  |  RECOMENDACOES            |                |
|  |  ====================      |  |  ==============            |                |
|  |                           |  |                           |                |
|  |  Quantos servicos AWS     |  |  Quantas sugestoes de     |                |
|  |  foram verificados.       |  |  otimizacao foram         |                |
|  |                           |  |  encontradas.             |                |
|  |  Maximo: 246              |  |  Exemplo: 15              |                |
|  |                           |  |                           |                |
|  +---------------------------+  +---------------------------+                |
|                                                                              |
+==============================================================================+
```

## 3.2 Botoes de Acao

```
+-----------------------------------------------------------------------------+
|                          BOTOES DO DASHBOARD                                |
+-----------------------------------------------------------------------------+
|                                                                             |
|  +-------------------+                                                      |
|  | ANALISE COMPLETA  |  <-- Executa analise de custos E recomendacoes      |
|  +-------------------+      Use quando quiser uma visao completa            |
|                                                                             |
|  +-------------------+                                                      |
|  | APENAS CUSTOS     |  <-- Mostra apenas dados de custo                   |
|  +-------------------+      Use para verificar gastos rapidamente           |
|                                                                             |
|  +-------------------+                                                      |
|  | APENAS RECOMEN.   |  <-- Mostra apenas sugestoes de economia            |
|  +-------------------+      Use para focar em otimizacoes                   |
|                                                                             |
|  +-------------------+                                                      |
|  | MULTI-REGION      |  <-- Analisa TODAS as regioes AWS                   |
|  +-------------------+      Use para visao global da conta                  |
|                                                                             |
+-----------------------------------------------------------------------------+
```

## 3.3 Tabela de Top Servicos

```
+-----------------------------------------------------------------------------+
|                    TOP 10 SERVICOS POR CUSTO                                |
+-----------------------------------------------------------------------------+
|                                                                             |
|  Esta tabela mostra seus 10 servicos AWS mais caros:                        |
|                                                                             |
|  +------+-------------------+----------+----------+-----------+             |
|  | Rank | Servico           | Custo    | % Total  | Tendencia |             |
|  +------+-------------------+----------+----------+-----------+             |
|  | 1    | Amazon EC2        | $500.00  | 40%      | Subindo   |             |
|  | 2    | Amazon RDS        | $300.00  | 24%      | Estavel   |             |
|  | 3    | Amazon S3         | $200.00  | 16%      | Descendo  |             |
|  | 4    | AWS Lambda        | $100.00  | 8%       | Subindo   |             |
|  | 5    | Amazon CloudFront | $75.00   | 6%       | Estavel   |             |
|  | ...  | ...               | ...      | ...      | ...       |             |
|  +------+-------------------+----------+----------+-----------+             |
|                                                                             |
|  COMO INTERPRETAR:                                                          |
|                                                                             |
|  - Servico: Nome do servico AWS                                             |
|  - Custo: Valor gasto nos ultimos 30 dias                                  |
|  - % Total: Percentual do seu gasto total                                  |
|  - Tendencia: Se o custo esta subindo, estavel ou descendo                 |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 4. Analise de Custos

## 4.1 Entendendo seus Custos

```
+==============================================================================+
|                      ANALISE DE CUSTOS AWS                                   |
+==============================================================================+
|                                                                              |
|  O dashboard divide seus custos em categorias:                               |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  COMPUTACAO (EC2, Lambda, ECS)                                        |  |
|  |  ================================                                      |  |
|  |                                                                        |  |
|  |  +--------------------------------------------+                       |  |
|  |  |            45% DO CUSTO TOTAL             |                       |  |
|  |  +--------------------------------------------+                       |  |
|  |                                                                        |  |
|  |  Inclui:                                                               |  |
|  |  - Instancias EC2 (servidores virtuais)                               |  |
|  |  - Funcoes Lambda (codigo serverless)                                 |  |
|  |  - Containers ECS/EKS                                                 |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  ARMAZENAMENTO (S3, EBS, EFS)                                         |  |
|  |  ============================                                          |  |
|  |                                                                        |  |
|  |  +-----------------------------+                                       |  |
|  |  |     25% DO CUSTO TOTAL     |                                       |  |
|  |  +-----------------------------+                                       |  |
|  |                                                                        |  |
|  |  Inclui:                                                               |  |
|  |  - Buckets S3 (objetos)                                               |  |
|  |  - Volumes EBS (discos)                                               |  |
|  |  - Sistemas de arquivo EFS                                            |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  BANCO DE DADOS (RDS, DynamoDB)                                       |  |
|  |  ==============================                                        |  |
|  |                                                                        |  |
|  |  +--------------------+                                                |  |
|  |  | 20% DO CUSTO TOTAL |                                                |  |
|  |  +--------------------+                                                |  |
|  |                                                                        |  |
|  |  Inclui:                                                               |  |
|  |  - Instancias RDS (MySQL, PostgreSQL, etc.)                           |  |
|  |  - Tabelas DynamoDB                                                   |  |
|  |  - Clusters ElastiCache                                               |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  REDE (ELB, CloudFront, NAT Gateway)                                  |  |
|  |  ===================================                                   |  |
|  |                                                                        |  |
|  |  +------------+                                                        |  |
|  |  | 10% CUSTO  |                                                        |  |
|  |  +------------+                                                        |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

## 4.2 Dicas para Reduzir Custos

```
+-----------------------------------------------------------------------------+
|                    DICAS RAPIDAS DE ECONOMIA                                |
+-----------------------------------------------------------------------------+
|                                                                             |
|  1. EC2 - INSTANCIAS                                                        |
|     ==================                                                      |
|                                                                             |
|     - Desligue instancias fora do horario comercial                        |
|     - Use Reserved Instances para cargas estaveis (30-60% desconto)        |
|     - Considere Spot Instances para tarefas flexiveis (ate 90% desconto)   |
|                                                                             |
|  2. S3 - ARMAZENAMENTO                                                      |
|     ====================                                                    |
|                                                                             |
|     - Configure lifecycle policies (mover dados antigos para Glacier)      |
|     - Use classes de storage adequadas (Standard-IA, Glacier)              |
|     - Delete objetos que nao precisa mais                                  |
|                                                                             |
|  3. RDS - BANCOS DE DADOS                                                   |
|     =====================                                                   |
|                                                                             |
|     - Desative Multi-AZ em ambientes de desenvolvimento                    |
|     - Reduza o tamanho da instancia se subutilizada                        |
|     - Use Aurora Serverless para cargas variaveis                          |
|                                                                             |
|  4. GERAL                                                                   |
|     =====                                                                   |
|                                                                             |
|     - Sempre verifique recursos orfaos (volumes, IPs, snapshots)           |
|     - Configure alertas de custo no AWS Budgets                            |
|     - Revise custos semanalmente                                           |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 5. Recomendacoes de Otimizacao

## 5.1 Tipos de Recomendacoes

```
+==============================================================================+
|                     TIPOS DE RECOMENDACOES                                   |
+==============================================================================+
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  PRIORIDADE ALTA (VERMELHO)                                           |  |
|  |  ==========================                                            |  |
|  |                                                                        |  |
|  |  Acao IMEDIATA necessaria!                                            |  |
|  |                                                                        |  |
|  |  Exemplos:                                                             |  |
|  |  - Volumes EBS orfaos (custando dinheiro sem uso)                     |  |
|  |  - Elastic IPs nao associados ($3.60/mes cada)                        |  |
|  |  - Instancias EC2 paradas (ainda pagam pelo disco)                    |  |
|  |                                                                        |  |
|  |  O QUE FAZER: Resolver hoje mesmo!                                    |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  PRIORIDADE MEDIA (AMARELO)                                           |  |
|  |  ==========================                                            |  |
|  |                                                                        |  |
|  |  Revisar em breve (esta semana)                                       |  |
|  |                                                                        |  |
|  |  Exemplos:                                                             |  |
|  |  - S3 sem lifecycle policy (dados crescendo infinitamente)            |  |
|  |  - S3 sem versionamento (risco de perda de dados)                     |  |
|  |  - RDS Multi-AZ em ambiente de desenvolvimento                        |  |
|  |                                                                        |  |
|  |  O QUE FAZER: Planejar para esta semana                               |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  PRIORIDADE BAIXA (VERDE)                                             |  |
|  |  ========================                                              |  |
|  |                                                                        |  |
|  |  Otimizacao opcional                                                  |  |
|  |                                                                        |  |
|  |  Exemplos:                                                             |  |
|  |  - Migrar para tipos de instancia mais novos                          |  |
|  |  - Considerar Reserved Instances                                      |  |
|  |  - Implementar tags de custo                                          |  |
|  |                                                                        |  |
|  |  O QUE FAZER: Quando tiver tempo                                      |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  INFORMATIVO (AZUL)                                                   |  |
|  |  ==================                                                    |  |
|  |                                                                        |  |
|  |  Apenas informacao, sem acao necessaria                               |  |
|  |                                                                        |  |
|  |  Exemplos:                                                             |  |
|  |  - NAT Gateway tem custo base de ~$32/mes                             |  |
|  |  - Quantidade de recursos na regiao                                   |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

## 5.2 Top 10 Recomendacoes Mais Comuns

```
+-----------------------------------------------------------------------------+
|                  TOP 10 RECOMENDACOES MAIS COMUNS                           |
+-----------------------------------------------------------------------------+
|                                                                             |
|  +----+------------------------+-----------------------+-------------------+|
|  | #  | Recomendacao           | O que fazer           | Economia estimada||
|  +----+------------------------+-----------------------+-------------------+|
|  | 1  | EBS Volume orfao       | Deletar volume nao    | $0.10/GB/mes     ||
|  |    |                        | anexado               |                   ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 2  | Elastic IP sem uso     | Liberar o IP          | $3.60/mes cada   ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 3  | S3 sem Lifecycle       | Configurar transicao  | 20-40% storage   ||
|  |    |                        | automatica            |                   ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 4  | EC2 instancia parada   | Terminar ou desligar  | Custo do EBS     ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 5  | RDS Multi-AZ em dev    | Desabilitar Multi-AZ  | 50% do RDS       ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 6  | EC2 superdimensionada  | Migrar para tipo      | 20-40% EC2       ||
|  |    |                        | menor                 |                   ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 7  | Snapshots antigos      | Deletar snapshots     | $0.05/GB/mes     ||
|  |    |                        | desnecessarios        |                   ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 8  | CloudWatch Logs sem    | Configurar retencao   | 80%+ logs        ||
|  |    | retencao               | (ex: 30 dias)         |                   ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 9  | Load Balancer ocioso   | Remover LB sem        | $16-33/mes       ||
|  |    |                        | targets               |                   ||
|  +----+------------------------+-----------------------+-------------------+|
|  | 10 | Sem Reserved Instances | Comprar RI para       | 30-60% EC2/RDS   ||
|  |    |                        | workloads estaveis    |                   ||
|  +----+------------------------+-----------------------+-------------------+|
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 6. Integracoes AWS

## 6.1 Visao Geral das Integracoes

```
+==============================================================================+
|                       INTEGRACOES DISPONIVEIS                                |
+==============================================================================+
|                                                                              |
|  O FinOps AWS se conecta com 4 servicos AWS para dar recomendacoes          |
|  mais inteligentes:                                                          |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  1. AWS COMPUTE OPTIMIZER                                             |  |
|  |  ============================                                          |  |
|  |                                                                        |  |
|  |  O que faz: Sugere o tamanho ideal para suas instancias EC2           |  |
|  |                                                                        |  |
|  |  Exemplo de recomendacao:                                             |  |
|  |  "Sua instancia m5.xlarge esta usando apenas 10% da CPU.              |  |
|  |   Considere migrar para m5.large e economizar 50%."                   |  |
|  |                                                                        |  |
|  |  Requisito: Precisa ser habilitado na sua conta AWS                   |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  2. AWS COST EXPLORER                                                 |  |
|  |  ========================                                              |  |
|  |                                                                        |  |
|  |  O que faz: Recomenda Reserved Instances e Savings Plans              |  |
|  |                                                                        |  |
|  |  Exemplo de recomendacao:                                             |  |
|  |  "Voce gastou $500/mes em EC2 nos ultimos 3 meses.                    |  |
|  |   Comprando RI, voce economizaria $200/mes (40%)."                    |  |
|  |                                                                        |  |
|  |  Requisito: Precisa ter dados de uso (minimo 7 dias)                  |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  3. AWS TRUSTED ADVISOR                                               |  |
|  |  ==========================                                            |  |
|  |                                                                        |  |
|  |  O que faz: Verificacoes de boas praticas AWS                         |  |
|  |                                                                        |  |
|  |  Exemplo de recomendacao:                                             |  |
|  |  "Voce tem 3 volumes EBS nao anexados custando $30/mes."              |  |
|  |                                                                        |  |
|  |  Requisito: Plano de suporte Business ou Enterprise                   |  |
|  |  (Plano Basic tem acesso limitado)                                    |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  4. AMAZON Q BUSINESS                                                 |  |
|  |  ======================                                                |  |
|  |                                                                        |  |
|  |  O que faz: Gera relatorios inteligentes com IA                       |  |
|  |                                                                        |  |
|  |  Exemplo de recomendacao:                                             |  |
|  |  Gera um relatorio executivo completo explicando seus custos          |  |
|  |  e sugerindo acoes prioritarias.                                      |  |
|  |                                                                        |  |
|  |  Requisito: Configurar Q_BUSINESS_APPLICATION_ID                      |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

## 6.2 Status das Integracoes

```
+-----------------------------------------------------------------------------+
|                      STATUS DAS INTEGRACOES                                 |
+-----------------------------------------------------------------------------+
|                                                                             |
|  No dashboard, voce vera o status de cada integracao:                       |
|                                                                             |
|  +------------------------+-----------+------------------------------------+|
|  | Integracao             | Status    | Significado                        ||
|  +------------------------+-----------+------------------------------------+|
|  | Compute Optimizer      | ATIVO     | Funcionando normalmente            ||
|  +------------------------+-----------+------------------------------------+|
|  | Compute Optimizer      | INATIVO   | Precisa ser habilitado na AWS      ||
|  +------------------------+-----------+------------------------------------+|
|  | Cost Explorer          | ATIVO     | Dados disponiveis                  ||
|  +------------------------+-----------+------------------------------------+|
|  | Cost Explorer          | SEM DADOS | Conta nova (aguarde 7+ dias)       ||
|  +------------------------+-----------+------------------------------------+|
|  | Trusted Advisor        | ATIVO     | Plano Business/Enterprise          ||
|  +------------------------+-----------+------------------------------------+|
|  | Trusted Advisor        | LIMITADO  | Plano Basic (poucas verificacoes)  ||
|  +------------------------+-----------+------------------------------------+|
|  | Amazon Q               | ATIVO     | Configurado e funcionando          ||
|  +------------------------+-----------+------------------------------------+|
|  | Amazon Q               | NAO CONFIG| Precisa configurar APP ID          ||
|  +------------------------+-----------+------------------------------------+|
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 7. Exportacao de Dados

## 7.1 Formatos Disponiveis

```
+==============================================================================+
|                      EXPORTACAO DE DADOS                                     |
+==============================================================================+
|                                                                              |
|  Voce pode exportar os dados do dashboard em 3 formatos:                    |
|                                                                              |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  EXPORTAR CSV                                                         |  |
|  |  ============                                                          |  |
|  |                                                                        |  |
|  |  Ideal para: Excel, Google Sheets, analises em planilhas             |  |
|  |                                                                        |  |
|  |  Contem:                                                               |  |
|  |  - Lista de custos por servico                                        |  |
|  |  - Lista de recomendacoes                                             |  |
|  |  - Metricas de recursos                                               |  |
|  |                                                                        |  |
|  |  Como usar:                                                            |  |
|  |  1. Clique em [Exportar CSV]                                          |  |
|  |  2. Salve o arquivo                                                   |  |
|  |  3. Abra no Excel ou Google Sheets                                    |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  EXPORTAR JSON                                                        |  |
|  |  =============                                                         |  |
|  |                                                                        |  |
|  |  Ideal para: Integracao com outros sistemas, APIs, automacao         |  |
|  |                                                                        |  |
|  |  Contem:                                                               |  |
|  |  - Dados estruturados completos                                       |  |
|  |  - Todos os detalhes tecnicos                                         |  |
|  |                                                                        |  |
|  |  Como usar:                                                            |  |
|  |  1. Clique em [Exportar JSON]                                         |  |
|  |  2. Salve o arquivo                                                   |  |
|  |  3. Use em suas integracoes                                           |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|  |                                                                        |  |
|  |  VERSAO IMPRESSAO                                                     |  |
|  |  ================                                                      |  |
|  |                                                                        |  |
|  |  Ideal para: Reunioes, apresentacoes, relatorios fisicos             |  |
|  |                                                                        |  |
|  |  Contem:                                                               |  |
|  |  - Relatorio formatado para impressao                                 |  |
|  |  - Graficos e tabelas                                                 |  |
|  |  - Resumo executivo                                                   |  |
|  |                                                                        |  |
|  |  Como usar:                                                            |  |
|  |  1. Clique em [Versao Impressao]                                      |  |
|  |  2. Use Ctrl+P (ou Cmd+P no Mac)                                      |  |
|  |  3. Imprima ou salve como PDF                                         |  |
|  |                                                                        |  |
|  +------------------------------------------------------------------------+  |
|                                                                              |
+==============================================================================+
```

---

# 8. Amazon Q - Consultor IA

## 8.1 O que e o Amazon Q?

```
+-----------------------------------------------------------------------------+
|                         AMAZON Q BUSINESS                                   |
+-----------------------------------------------------------------------------+
|                                                                             |
|  O Amazon Q e um assistente de IA que gera RELATORIOS PERSONALIZADOS       |
|  baseados nos seus dados de custo AWS.                                      |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  |                                                                       |  |
|  |  VOCE ESCOLHE PARA QUEM E O RELATORIO:                               |  |
|  |                                                                       |  |
|  |  +-------------------------------------------------------------------+|  |
|  |  |                                                                   ||  |
|  |  |  EXECUTIVO (CEO/CFO)                                             ||  |
|  |  |  ====================                                             ||  |
|  |  |                                                                   ||  |
|  |  |  Recebe: Resumo de 2 paginas, foco em ROI e decisoes             ||  |
|  |  |                                                                   ||  |
|  |  +-------------------------------------------------------------------+|  |
|  |  |                                                                   ||  |
|  |  |  CTO (Lideranca Tecnica)                                         ||  |
|  |  |  ========================                                         ||  |
|  |  |                                                                   ||  |
|  |  |  Recebe: Roadmap de otimizacao, trade-offs tecnicos              ||  |
|  |  |                                                                   ||  |
|  |  +-------------------------------------------------------------------+|  |
|  |  |                                                                   ||  |
|  |  |  DEVOPS (Engenheiros)                                            ||  |
|  |  |  =====================                                            ||  |
|  |  |                                                                   ||  |
|  |  |  Recebe: Comandos AWS CLI prontos para copiar e colar            ||  |
|  |  |                                                                   ||  |
|  |  +-------------------------------------------------------------------+|  |
|  |  |                                                                   ||  |
|  |  |  ANALYST (Analistas FinOps)                                      ||  |
|  |  |  ===========================                                      ||  |
|  |  |                                                                   ||  |
|  |  |  Recebe: KPIs detalhados, metricas, benchmarks                   ||  |
|  |  |                                                                   ||  |
|  |  +-------------------------------------------------------------------+|  |
|  |                                                                       |  |
|  +-----------------------------------------------------------------------+  |
|                                                                             |
+-----------------------------------------------------------------------------+
```

---

# 9. Perguntas Frequentes

```
+==============================================================================+
|                       PERGUNTAS FREQUENTES                                   |
+==============================================================================+
|                                                                              |
|  P: Por que meu custo mostra $0?                                            |
|  ================================                                            |
|                                                                              |
|  R: Isso pode acontecer se:                                                 |
|     - Sua conta AWS e nova (menos de 24 horas)                              |
|     - Voce tem poucos recursos ativos                                       |
|     - Os dados do Cost Explorer ainda nao foram processados                 |
|                                                                              |
|  Solucao: Aguarde 24 horas e tente novamente                                |
|                                                                              |
|  ---------------------------------------------------------------------------|
|                                                                              |
|  P: Por que algumas integracoes estao inativas?                             |
|  ==============================================                              |
|                                                                              |
|  R: Cada integracao tem requisitos:                                         |
|     - Compute Optimizer: Precisa ser habilitado manualmente                 |
|     - Trusted Advisor: Precisa de plano Business/Enterprise                 |
|     - Amazon Q: Precisa configurar Q_BUSINESS_APPLICATION_ID                |
|                                                                              |
|  ---------------------------------------------------------------------------|
|                                                                              |
|  P: Com que frequencia os dados sao atualizados?                            |
|  ===============================================                             |
|                                                                              |
|  R: - Os dados de custo sao atualizados pela AWS a cada 24 horas           |
|     - Voce pode clicar em "Analise Completa" para buscar dados novos        |
|                                                                              |
|  ---------------------------------------------------------------------------|
|                                                                              |
|  P: O que e um recurso "orfao"?                                             |
|  ==============================                                              |
|                                                                              |
|  R: E um recurso que esta custando dinheiro mas nao esta sendo usado.       |
|     Exemplos:                                                               |
|     - Volume EBS nao anexado a nenhuma instancia                            |
|     - Elastic IP nao associado a nenhum recurso                             |
|     - Snapshot antigo sem necessidade                                       |
|                                                                              |
|  ---------------------------------------------------------------------------|
|                                                                              |
|  P: O que sao Reserved Instances?                                           |
|  ================================                                            |
|                                                                              |
|  R: E um compromisso de 1 ou 3 anos com a AWS em troca de desconto.         |
|     - RI de 1 ano: 30-40% desconto                                          |
|     - RI de 3 anos: 50-60% desconto                                         |
|     Ideal para workloads estaveis que rodam 24/7.                           |
|                                                                              |
+==============================================================================+
```

---

# 10. Glossario

```
+==============================================================================+
|                            GLOSSARIO                                         |
+==============================================================================+
|                                                                              |
|  +--------------------+----------------------------------------------------+|
|  | Termo              | Definicao                                          ||
|  +--------------------+----------------------------------------------------+|
|  | AWS                | Amazon Web Services - provedor de nuvem           ||
|  +--------------------+----------------------------------------------------+|
|  | EC2                | Elastic Compute Cloud - servidores virtuais       ||
|  +--------------------+----------------------------------------------------+|
|  | S3                 | Simple Storage Service - armazenamento de objetos ||
|  +--------------------+----------------------------------------------------+|
|  | RDS                | Relational Database Service - bancos de dados     ||
|  +--------------------+----------------------------------------------------+|
|  | EBS                | Elastic Block Store - discos virtuais             ||
|  +--------------------+----------------------------------------------------+|
|  | EIP                | Elastic IP - endereco IP fixo                     ||
|  +--------------------+----------------------------------------------------+|
|  | Lambda             | Funcoes serverless (codigo sem servidor)          ||
|  +--------------------+----------------------------------------------------+|
|  | FinOps             | Financial Operations - gestao financeira cloud    ||
|  +--------------------+----------------------------------------------------+|
|  | Right-sizing       | Ajustar recursos ao tamanho correto               ||
|  +--------------------+----------------------------------------------------+|
|  | Reserved Instance  | Compromisso 1-3 anos com desconto                 ||
|  +--------------------+----------------------------------------------------+|
|  | Savings Plan       | Compromisso flexivel com desconto                 ||
|  +--------------------+----------------------------------------------------+|
|  | Spot Instance      | Capacidade ociosa AWS com grande desconto         ||
|  +--------------------+----------------------------------------------------+|
|  | Lifecycle Policy   | Regra automatica para mover/deletar dados         ||
|  +--------------------+----------------------------------------------------+|
|  | Multi-AZ           | Replicacao em multiplas zonas de disponibilidade  ||
|  +--------------------+----------------------------------------------------+|
|  | Waste              | Desperdicio - recursos pagos mas nao utilizados   ||
|  +--------------------+----------------------------------------------------+|
|                                                                              |
+==============================================================================+
```

---

```
+==============================================================================+
|                                                                              |
|                      FIM DO MANUAL DO USUARIO                               |
|                                                                              |
|   Versao 2.0 - Dezembro 2024                                                |
|   FinOps AWS - Dashboard de Otimizacao de Custos                            |
|                                                                              |
+==============================================================================+
```
