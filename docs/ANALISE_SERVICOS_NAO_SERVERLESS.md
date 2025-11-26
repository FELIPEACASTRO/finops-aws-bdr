# Análise de Serviços AWS - Serverless vs Provisionados

Este documento categoriza os 253 serviços AWS do catálogo, identificando quais **NÃO são serverless** (requerem provisionamento de recursos dedicados) e representam maior potencial de otimização de custos.

---

## Resumo Executivo

| Categoria | Quantidade | Impacto de Custo |
|-----------|------------|------------------|
| Serviços Provisionados (não-serverless) | ~85 | ALTO |
| Serviços Serverless | ~75 | MÉDIO |
| Serviços de Gerenciamento/Gratuitos | ~93 | BAIXO/NULO |

---

## Serviços NÃO-SERVERLESS (Provisionados)

Estes serviços cobram por recursos provisionados, independente do uso real. São os maiores candidatos a otimização.

### Compute (Alta Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS EC2** | ✅ Implementado | Instâncias de computação | MUITO ALTO |
| **AWS EC2 Spot** | ❌ Pendente | Instâncias spot | ALTO |
| **AWS EC2 Image Builder** | ❌ Pendente | Construção de AMIs | MÉDIO |
| **AWS Elastic Beanstalk** | ❌ Pendente | PaaS (usa EC2/ECS) | ALTO |
| **AWS Lightsail** | ❌ Pendente | VPS simplificado | MÉDIO |
| **AWS Outposts** | ❌ Pendente | Hardware on-premises | MUITO ALTO |
| **AWS ParallelCluster** | ❌ Pendente | HPC clusters | ALTO |
| **AWS Batch** | ❌ Pendente | Processamento em lote | MÉDIO |
| **AWS AppStream 2.0** | ❌ Pendente | Streaming de aplicações | ALTO |

### Containers (Alta Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS ECS** | ✅ Implementado | Container orchestration | ALTO |
| **AWS EKS** | ❌ Pendente | Kubernetes gerenciado | MUITO ALTO |
| **AWS ECR** | ❌ Pendente | Registro de containers | MÉDIO |

### Databases (Alta Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **Amazon RDS** | ✅ Implementado | Bancos relacionais | MUITO ALTO |
| **Amazon Aurora** | ❌ Pendente | MySQL/PostgreSQL gerenciado | MUITO ALTO |
| **Amazon Redshift** | ✅ Implementado | Data Warehouse | MUITO ALTO |
| **Amazon ElastiCache** | ✅ Implementado | Redis/Memcached | ALTO |
| **Amazon DocumentDB** | ❌ Pendente | MongoDB compatível | ALTO |
| **Amazon Neptune** | ❌ Pendente | Graph database | ALTO |
| **Amazon Keyspaces** | ❌ Pendente | Cassandra compatível | MÉDIO |
| **Amazon Timestream** | ❌ Pendente | Time-series database | MÉDIO |
| **Amazon OpenSearch** | ❌ Pendente | Elasticsearch | ALTO |
| **Amazon MemoryDB** | ❌ Pendente | Redis durável | ALTO |
| **Amazon MQ** | ❌ Pendente | Message broker | MÉDIO |

### Storage (Alta Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS EBS** | ✅ Implementado | Block storage | MUITO ALTO |
| **AWS EFS** | ✅ Implementado | File storage | ALTO |
| **AWS FSx for Lustre** | ❌ Pendente | HPC file system | ALTO |
| **AWS FSx for Windows** | ❌ Pendente | Windows file server | ALTO |
| **AWS FSx for NetApp ONTAP** | ❌ Pendente | Enterprise NAS | ALTO |
| **AWS FSx for OpenZFS** | ❌ Pendente | ZFS file system | MÉDIO |
| **AWS Storage Gateway** | ❌ Pendente | Hybrid storage | MÉDIO |
| **AWS Snowball Edge** | ❌ Pendente | Edge computing | MÉDIO |

### Networking (Alta Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS VPC** | ✅ Implementado | Virtual Private Cloud | ALTO |
| **AWS ELB** | ✅ Implementado | Load Balancers | ALTO |
| **AWS Direct Connect** | ❌ Pendente | Conexão dedicada | MUITO ALTO |
| **AWS Transit Gateway** | ❌ Pendente | Hub de rede | ALTO |
| **AWS Global Accelerator** | ❌ Pendente | Acelerador global | ALTO |
| **AWS PrivateLink** | ❌ Pendente | Endpoints privados | MÉDIO |
| **AWS Site-to-Site VPN** | ❌ Pendente | VPN gerenciada | MÉDIO |
| **AWS Client VPN** | ❌ Pendente | VPN para clientes | MÉDIO |
| **AWS Network Firewall** | ❌ Pendente | Firewall gerenciado | ALTO |
| **AWS App Mesh** | ❌ Pendente | Service mesh | MÉDIO |
| **AWS Cloud Map** | ❌ Pendente | Service discovery | BAIXO |

### Analytics & Big Data (Alta Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS EMR** | ✅ Implementado | Spark/Hadoop clusters | MUITO ALTO |
| **AWS Kinesis Data Streams** | ✅ Implementado | Streaming de dados | ALTO |
| **AWS Kinesis Data Firehose** | ❌ Pendente | Entrega de dados | MÉDIO |
| **AWS Kinesis Video Streams** | ❌ Pendente | Streaming de vídeo | ALTO |
| **AWS Glue** | ✅ Implementado | ETL gerenciado | ALTO |
| **AWS Redshift Spectrum** | ❌ Pendente | Query em S3 | MÉDIO |
| **AWS Lake Formation** | ❌ Pendente | Data lake | MÉDIO |
| **AWS Data Pipeline** | ❌ Pendente | Orquestração ETL | MÉDIO |
| **AWS QuickSight** | ❌ Pendente | BI/Dashboards | ALTO |
| **AWS Managed Grafana** | ❌ Pendente | Observabilidade | MÉDIO |
| **AWS Managed Prometheus** | ❌ Pendente | Métricas | MÉDIO |

### Machine Learning (Alta Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS SageMaker** | ✅ Implementado | ML Platform | MUITO ALTO |
| **Amazon Bedrock** | ❌ Pendente | Foundation Models | ALTO |
| **AWS Elastic Inference** | ❌ Pendente | GPU compartilhada | ALTO |
| **Amazon Comprehend** | ❌ Pendente | NLP | MÉDIO |
| **Amazon Rekognition** | ❌ Pendente | Computer Vision | MÉDIO |
| **Amazon Polly** | ❌ Pendente | Text-to-Speech | BAIXO |
| **Amazon Transcribe** | ❌ Pendente | Speech-to-Text | MÉDIO |
| **Amazon Translate** | ❌ Pendente | Tradução | BAIXO |
| **Amazon Textract** | ❌ Pendente | OCR | MÉDIO |
| **Amazon Forecast** | ❌ Pendente | Previsão | MÉDIO |
| **Amazon Personalize** | ❌ Pendente | Recomendações | MÉDIO |
| **Amazon Kendra** | ❌ Pendente | Enterprise Search | ALTO |
| **Amazon Lex** | ❌ Pendente | Chatbots | MÉDIO |

### End-User Computing (Média Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **Amazon WorkSpaces** | ❌ Pendente | Virtual desktops | MUITO ALTO |
| **Amazon WorkSpaces Web** | ❌ Pendente | Browser virtual | ALTO |
| **Amazon WorkDocs** | ❌ Pendente | Armazenamento docs | MÉDIO |
| **Amazon WorkMail** | ❌ Pendente | Email corporativo | MÉDIO |
| **Amazon Connect** | ❌ Pendente | Contact center | ALTO |
| **Amazon Chime** | ❌ Pendente | Comunicação | MÉDIO |

### Media Services (Média Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS Elemental MediaLive** | ❌ Pendente | Live video | ALTO |
| **AWS Elemental MediaConvert** | ❌ Pendente | Video transcoding | MÉDIO |
| **AWS Elemental MediaPackage** | ❌ Pendente | Video packaging | MÉDIO |
| **AWS Elemental MediaStore** | ❌ Pendente | Video storage | MÉDIO |
| **AWS Elemental MediaConnect** | ❌ Pendente | Video transport | MÉDIO |
| **AWS Elemental MediaTailor** | ❌ Pendente | Ad insertion | MÉDIO |

### Security (Média Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS CloudHSM** | ❌ Pendente | Hardware security | ALTO |
| **AWS Directory Service** | ❌ Pendente | Active Directory | ALTO |
| **AWS Macie** | ❌ Pendente | Data discovery | MÉDIO |
| **AWS GuardDuty** | ❌ Pendente | Threat detection | MÉDIO |
| **AWS Inspector** | ❌ Pendente | Vulnerability scanning | MÉDIO |
| **AWS Security Hub** | ❌ Pendente | Security posture | MÉDIO |
| **AWS WAF** | ❌ Pendente | Web firewall | MÉDIO |
| **AWS Shield** | ❌ Pendente | DDoS protection | ALTO |
| **AWS Firewall Manager** | ❌ Pendente | Firewall central | MÉDIO |

### IoT (Baixa Prioridade)

| Serviço | Status | Descrição | Potencial de Economia |
|---------|--------|-----------|----------------------|
| **AWS IoT Core** | ❌ Pendente | IoT platform | MÉDIO |
| **AWS IoT Analytics** | ❌ Pendente | IoT analytics | MÉDIO |
| **AWS IoT Greengrass** | ❌ Pendente | Edge computing | MÉDIO |
| **AWS IoT Device Management** | ❌ Pendente | Device management | BAIXO |
| **AWS IoT Events** | ❌ Pendente | Event detection | BAIXO |
| **AWS IoT FleetWise** | ❌ Pendente | Vehicle data | MÉDIO |

---

## Serviços SERVERLESS (Pay-per-Use)

Estes serviços cobram apenas pelo uso real. Menor potencial de otimização por ociosidade, mas ainda importantes.

### Compute Serverless

| Serviço | Status | Descrição |
|---------|--------|-----------|
| **AWS Lambda** | ✅ Implementado | Functions as a Service |
| **AWS Fargate** | ✅ (via ECS) | Serverless containers |
| **AWS App Runner** | ❌ Pendente | Serverless web apps |
| **AWS EMR Serverless** | ❌ Pendente | Serverless Spark |

### Storage Serverless

| Serviço | Status | Descrição |
|---------|--------|-----------|
| **AWS S3** | ✅ Implementado | Object storage |
| **AWS S3 Glacier** | ❌ Pendente | Archive storage |
| **AWS S3 Express One Zone** | ❌ Pendente | Low-latency S3 |

### Database Serverless

| Serviço | Status | Descrição |
|---------|--------|-----------|
| **AWS DynamoDB** | ✅ Implementado | NoSQL (on-demand) |
| **AWS DynamoDB Accelerator (DAX)** | ❌ Pendente | DynamoDB cache |
| **Aurora Serverless** | ❌ Pendente | Aurora on-demand |

### Integration Serverless

| Serviço | Status | Descrição |
|---------|--------|-----------|
| **AWS SNS** | ✅ Implementado | Pub/Sub messaging |
| **AWS SQS** | ✅ Implementado | Message queues |
| **AWS EventBridge** | ❌ Pendente | Event bus |
| **AWS Step Functions** | ❌ Pendente | Workflow orchestration |
| **AWS AppSync** | ❌ Pendente | GraphQL API |
| **AWS API Gateway** | ❌ Pendente | REST/HTTP APIs |

### CDN/Edge

| Serviço | Status | Descrição |
|---------|--------|-----------|
| **Amazon CloudFront** | ✅ Implementado | CDN |
| **AWS Lambda@Edge** | ❌ Pendente | Edge functions |

---

## Serviços de Gerenciamento (Custo Indireto)

Estes serviços geralmente são gratuitos ou têm custo indireto via outros serviços.

| Categoria | Exemplos |
|-----------|----------|
| **Monitoramento** | CloudWatch, CloudTrail, Config |
| **Segurança** | IAM, KMS, Secrets Manager, ACM |
| **Gerenciamento** | Systems Manager, Organizations, Control Tower |
| **DevOps** | CodeBuild, CodePipeline, CodeDeploy |
| **Otimização** | Compute Optimizer, Trusted Advisor, Budgets |

---

## Próximos Serviços a Implementar (Por Prioridade)

### Prioridade 1 - Muito Alto Impacto de Custo

1. **AWS EKS** - Kubernetes é muito utilizado e caro
2. **Amazon Aurora** - Principal banco de dados gerenciado
3. **AWS Direct Connect** - Conexões dedicadas são caras
4. **Amazon WorkSpaces** - Desktops virtuais corporativos
5. **AWS Transit Gateway** - Hub de rede multi-VPC
6. **AWS OpenSearch** - Elasticsearch gerenciado
7. **Amazon Bedrock** - LLMs e IA Generativa
8. **AWS Global Accelerator** - Aceleração de rede

### Prioridade 2 - Alto Impacto de Custo

1. **Amazon DocumentDB** - MongoDB gerenciado
2. **Amazon Neptune** - Graph database
3. **AWS FSx** (todas as variantes) - File systems enterprise
4. **AWS Elemental** (MediaLive, etc) - Streaming de vídeo
5. **Amazon Connect** - Contact center
6. **AWS CloudHSM** - Hardware security modules
7. **AWS Directory Service** - Active Directory
8. **Amazon Kendra** - Enterprise search

### Prioridade 3 - Médio Impacto

1. **AWS API Gateway** - APIs REST/HTTP
2. **AWS Step Functions** - Workflows
3. **AWS EventBridge** - Event bus
4. **AWS Batch** - Processamento em lote
5. **Amazon MQ** - Message broker
6. **AWS App Runner** - Serverless web apps

---

## Status Atual

| Métrica | Valor |
|---------|-------|
| Total de Serviços AWS | 253 |
| Serviços Implementados | 21 (8.3%) |
| Serviços Não-Serverless Pendentes | ~64 |
| Serviços Serverless Pendentes | ~50 |
| Serviços de Gerenciamento | ~93 |

---

*Documento gerado em: Novembro 2025*
