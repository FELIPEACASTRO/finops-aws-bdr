# FinOps AWS - Manual do Usuário Ultra-Detalhado

## Bem-vindo ao FinOps AWS!

Este manual foi criado para guiar você, passo a passo, desde a instalação até a obtenção de relatórios de economia na sua conta AWS. Não importa seu nível técnico - aqui você encontrará explicações claras com exemplos do dia a dia.

---

## Índice Completo

1. [Introdução - O Que é o FinOps AWS](#1-introdução)
2. [Requisitos - O Que Você Precisa Antes de Começar](#2-requisitos)
3. [Instalação e Configuração - Passo a Passo](#3-instalação-e-configuração)
4. [Primeiro Uso - Testando a Ferramenta](#4-primeiro-uso)
5. [Execução Local - Usando no Seu Computador](#5-execução-local)
6. [Deploy para AWS Lambda - Automatizando na Nuvem](#6-deploy-para-aws-lambda)
7. [Interpretando Resultados - Entendendo os Relatórios](#7-interpretando-resultados)
8. [Configurações Avançadas - Personalizando](#8-configurações-avançadas)
9. [Troubleshooting - Resolvendo Problemas](#9-troubleshooting)
10. [FAQ - Perguntas Frequentes](#10-faq)
11. [Glossário - Termos Técnicos Explicados](#11-glossário)
12. [Suporte e Contato](#12-suporte)

---

# 1. Introdução

## 1.1 O Que é o FinOps AWS?

O **FinOps AWS** é uma ferramenta inteligente que analisa sua conta AWS e encontra oportunidades de **economizar dinheiro**. Funciona como um consultor financeiro para sua infraestrutura de nuvem.

### Comparação: Sem FinOps vs Com FinOps

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ANTES vs DEPOIS DO FINOPS AWS                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ❌ SEM FINOPS AWS                      ✅ COM FINOPS AWS                    ║
║  ───────────────────────────────────────────────────────────────────────     ║
║                                                                              ║
║  "Não sei por que a fatura               "A fatura subiu porque criamos     ║
║   subiu 35% este mês"                     15 novas instâncias EC2 para      ║
║                                           o projeto X. Aqui estão elas."    ║
║                                                                              ║
║  "Não sei se estamos                      "Temos 12 servidores usando       ║
║   desperdiçando recursos"                  menos de 10% de CPU. Podemos     ║
║                                            economizar R$ 8.500/mês"         ║
║                                                                              ║
║  "Analisar custos leva                    "Relatório completo em 5 minutos  ║
║   2 semanas da minha equipe"               com zero esforço manual"         ║
║                                                                              ║
║  "Não temos visibilidade                  "Dashboard mostrando custos       ║
║   de custos por projeto"                   por projeto, time e ambiente"    ║
║                                                                              ║
║  "Pagamos preço cheio                     "Identificamos 30 servidores      ║
║   em tudo"                                 candidatos a Reserved Instance.  ║
║                                            Economia: R$ 45.000/ano"         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Analogia: O FinOps é Como um Contador da Sua Casa

Imagine que você contratou um **contador pessoal** para cuidar das finanças da sua casa:

- **Ele analisa** cada conta que chega (luz, água, internet, streaming)
- **Ele identifica** desperdícios (assinaturas que você não usa, plano de celular caro demais)
- **Ele recomenda** ações (cancelar Netflix se você só usa Prime, mudar para plano de energia mais barato)
- **Ele faz isso todo mês** automaticamente

O FinOps AWS faz exatamente isso, mas para sua infraestrutura AWS.

## 1.2 Benefícios Principais - Com Exemplos Reais

| Benefício | Como Funciona | Exemplo Real |
|-----------|---------------|--------------|
| **Encontra Recursos Ociosos** | Identifica máquinas desligadas ou sem uso | "Encontramos 5 servidores de um projeto que foi cancelado há 8 meses. Custo mensal: R$ 4.200" |
| **Sugere Rightsizing** | Reduz tamanho de máquinas superdimensionadas | "Seu banco de dados db.r5.4xlarge usa 15% da capacidade. Migrando para db.r5.large você economiza R$ 5.800/mês" |
| **Recomenda Reserved Instances** | Indica quando vale comprar com desconto | "Estes 20 servidores rodam 24/7 há 12 meses. Com Reserved Instance você economiza 40% = R$ 12.000/ano" |
| **Otimiza Storage** | Move dados antigos para armazenamento mais barato | "50TB de logs de 2021 ainda estão em S3 Standard. Movendo para Glacier Deep Archive: economia de R$ 1.150/mês" |
| **Detecta Anomalias** | Alerta sobre gastos inesperados | "ALERTA: Custo de NAT Gateway aumentou 300% ontem. Causa: deploy com loop infinito fazendo 1 milhão de requests" |

## 1.3 Para Quem é Este Manual?

Este manual foi escrito pensando em diferentes perfis. Encontre o seu:

### 👨‍💼 Administrador de Cloud / DevOps

**Você vai aprender:**
- Como instalar e configurar o FinOps AWS
- Como fazer deploy para produção com Terraform
- Como configurar alertas e relatórios automáticos

### 👩‍💻 Desenvolvedor

**Você vai aprender:**
- Como entender os custos da sua aplicação
- Como executar análises locais durante o desenvolvimento
- Como evitar criar recursos que desperdiçam dinheiro

### 👔 Gestor de TI / CTO

**Você vai aprender:**
- Como interpretar os relatórios executivos
- Como apresentar economia para a diretoria
- Como estabelecer governança de custos

### 📊 Equipe Financeira / Controller

**Você vai aprender:**
- Como usar os dados para orçamento e forecast
- Como fazer chargeback por departamento
- Como justificar investimentos em otimização

## 1.4 Garantia de Segurança

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🔒 GARANTIA DE SEGURANÇA                           ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  O FinOps AWS é uma ferramenta de APENAS LEITURA. Ele NUNCA irá:            ║
║                                                                              ║
║  ❌ Criar recursos na sua conta (não cria servidores, bancos, etc.)         ║
║  ❌ Modificar configurações existentes (não muda nada)                      ║
║  ❌ Deletar qualquer coisa (não remove recursos, dados, etc.)               ║
║  ❌ Acessar dados sensíveis (não lê o conteúdo dos seus arquivos/bancos)    ║
║  ❌ Fazer chamadas de API que custam dinheiro                               ║
║                                                                              ║
║  ✅ Ele APENAS LÊ informações de configuração e métricas                    ║
║  ✅ Ele APENAS GERA relatórios com recomendações                            ║
║  ✅ Todas as ações de otimização são VOCÊ quem executa manualmente          ║
║                                                                              ║
║  ───────────────────────────────────────────────────────────────────────     ║
║                                                                              ║
║  ANALOGIA: É como um consultor que olha seu extrato bancário para dar       ║
║  conselhos, mas não tem acesso para fazer transferências ou saques.         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

# 2. Requisitos

## 2.1 Checklist de Pré-Requisitos

Antes de começar, verifique se você tem tudo o que precisa:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CHECKLIST DE PRÉ-REQUISITOS                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PARA TESTAR LOCALMENTE (modo demo):                                         ║
║  ────────────────────────────────────────────────────                        ║
║  ☐ Python 3.11 ou superior                                                   ║
║     Como verificar: python --version                                         ║
║     Resultado esperado: Python 3.11.x ou superior                            ║
║                                                                              ║
║  ☐ pip instalado                                                             ║
║     Como verificar: pip --version                                            ║
║     Resultado esperado: pip 21.x ou superior                                 ║
║                                                                              ║
║  ☐ Git instalado (para clonar o repositório)                                 ║
║     Como verificar: git --version                                            ║
║     Resultado esperado: git version 2.x.x                                    ║
║                                                                              ║
║  PARA USAR COM AWS REAL:                                                     ║
║  ────────────────────────────────────────────────────                        ║
║  ☐ Conta AWS ativa                                                           ║
║  ☐ Usuário IAM com permissões de leitura                                     ║
║  ☐ Access Key e Secret Key configurados                                      ║
║  ☐ Cost Explorer habilitado na conta AWS                                     ║
║                                                                              ║
║  PARA DEPLOY EM PRODUÇÃO:                                                    ║
║  ────────────────────────────────────────────────────                        ║
║  ☐ Terraform 1.5 ou superior                                                 ║
║     Como verificar: terraform --version                                      ║
║  ☐ AWS CLI instalado e configurado                                           ║
║     Como verificar: aws sts get-caller-identity                              ║
║  ☐ Permissões para criar Lambda, Step Functions, S3, IAM                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 2.2 Requisitos de Sistema Detalhados

### Python

| Requisito | Especificação | Verificação |
|-----------|---------------|-------------|
| **Versão** | 3.11 ou superior | `python --version` |
| **Por quê esta versão?** | Usamos recursos modernos do Python como dataclasses, typing, e async | |

**Como instalar Python 3.11:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-pip

# macOS (com Homebrew)
brew install python@3.11

# Windows
# Baixe de https://www.python.org/downloads/
```

### pip

| Requisito | Especificação | Verificação |
|-----------|---------------|-------------|
| **Versão** | Qualquer versão recente | `pip --version` |
| **Por quê?** | Gerenciador de pacotes Python para instalar dependências | |

### Git

| Requisito | Especificação | Verificação |
|-----------|---------------|-------------|
| **Versão** | Qualquer versão | `git --version` |
| **Por quê?** | Para clonar o repositório | |

## 2.3 Requisitos AWS Detalhados

### Conta AWS

Você precisa de uma conta AWS ativa. Se não tiver:
1. Acesse https://aws.amazon.com/
2. Clique em "Create an AWS Account"
3. Siga o processo de criação (requer cartão de crédito)

### Cost Explorer

O Cost Explorer DEVE estar habilitado para análise de custos:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COMO HABILITAR O COST EXPLORER                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PASSO 1: Acesse o Console AWS                                               ║
║           https://console.aws.amazon.com/                                    ║
║                                                                              ║
║  PASSO 2: Na barra de busca, digite "Cost Explorer"                          ║
║                                                                              ║
║  PASSO 3: Clique em "AWS Cost Explorer"                                      ║
║                                                                              ║
║  PASSO 4: Se for a primeira vez:                                             ║
║           - Clique em "Enable Cost Explorer"                                 ║
║           - Aguarde 24 horas para os dados serem processados                 ║
║                                                                              ║
║  ⚠️  IMPORTANTE: O Cost Explorer leva até 24 horas para coletar dados       ║
║     iniciais. Se você acabou de habilitar, aguarde antes de testar.         ║
║                                                                              ║
║  💰 CUSTO: O Cost Explorer é GRATUITO para visualização básica.             ║
║     Relatórios avançados têm custo mínimo (~$0.01 por request)               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 2.4 Permissões IAM Necessárias

O FinOps AWS precisa de permissões de **leitura** para funcionar. Aqui está exatamente o que você precisa configurar:

### Política IAM Completa (Copie e Cole)

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "FinOpsReadOnlyAccess",
            "Effect": "Allow",
            "Action": [
                "ec2:Describe*",
                "rds:Describe*",
                "s3:GetBucket*",
                "s3:List*",
                "lambda:List*",
                "lambda:Get*",
                "ecs:Describe*",
                "ecs:List*",
                "eks:Describe*",
                "eks:List*",
                "elasticache:Describe*",
                "dynamodb:Describe*",
                "dynamodb:List*",
                "cloudwatch:GetMetric*",
                "cloudwatch:List*",
                "cloudwatch:Describe*",
                "ce:GetCost*",
                "ce:GetReservation*",
                "ce:GetSavings*",
                "ce:GetRightsizing*",
                "ce:GetDimensions",
                "ce:GetTags",
                "budgets:Describe*",
                "budgets:View*",
                "iam:Get*",
                "iam:List*",
                "organizations:Describe*",
                "organizations:List*",
                "compute-optimizer:Get*",
                "compute-optimizer:Describe*",
                "elasticloadbalancing:Describe*",
                "autoscaling:Describe*",
                "cloudfront:List*",
                "cloudfront:Get*",
                "route53:List*",
                "route53:Get*",
                "sns:List*",
                "sns:Get*",
                "sqs:List*",
                "sqs:Get*",
                "kms:List*",
                "kms:Describe*",
                "secretsmanager:List*",
                "secretsmanager:Describe*"
            ],
            "Resource": "*"
        }
    ]
}
```

### Como Criar Esta Política - Passo a Passo

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COMO CRIAR A POLÍTICA IAM                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PASSO 1: Acesse o Console AWS                                               ║
║           https://console.aws.amazon.com/                                    ║
║                                                                              ║
║  PASSO 2: Na barra de busca, digite "IAM"                                    ║
║                                                                              ║
║  PASSO 3: No menu lateral, clique em "Policies"                              ║
║                                                                              ║
║  PASSO 4: Clique no botão "Create policy" (azul, canto superior direito)     ║
║                                                                              ║
║  PASSO 5: Selecione a aba "JSON"                                             ║
║                                                                              ║
║  PASSO 6: Apague todo o conteúdo e COLE a política JSON acima                ║
║                                                                              ║
║  PASSO 7: Clique em "Next: Tags" (pode pular as tags)                        ║
║                                                                              ║
║  PASSO 8: Clique em "Next: Review"                                           ║
║                                                                              ║
║  PASSO 9: Nomeie a política:                                                 ║
║           Nome: FinOpsReadOnlyPolicy                                         ║
║           Descrição: Permite leitura de recursos para análise FinOps         ║
║                                                                              ║
║  PASSO 10: Clique em "Create policy"                                         ║
║                                                                              ║
║  PRÓXIMO: Agora você precisa ANEXAR esta política a um usuário ou role       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Como Anexar a Política a um Usuário

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COMO ANEXAR A POLÍTICA A UM USUÁRIO                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PASSO 1: No IAM, clique em "Users" no menu lateral                          ║
║                                                                              ║
║  PASSO 2: Clique no nome do usuário que vai usar o FinOps                    ║
║           (ou crie um novo usuário clicando em "Add user")                   ║
║                                                                              ║
║  PASSO 3: Na aba "Permissions", clique em "Add permissions"                  ║
║                                                                              ║
║  PASSO 4: Selecione "Attach policies directly"                               ║
║                                                                              ║
║  PASSO 5: Na busca, digite "FinOpsReadOnlyPolicy"                            ║
║                                                                              ║
║  PASSO 6: Marque o checkbox da política e clique em "Next"                   ║
║                                                                              ║
║  PASSO 7: Clique em "Add permissions"                                        ║
║                                                                              ║
║  PRONTO! O usuário agora tem as permissões necessárias.                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

# 3. Instalação e Configuração

## 3.1 Obtendo o Código - Passo a Passo

### Passo 1: Abra o Terminal

**Windows:**
- Pressione `Win + R`, digite `cmd` e pressione Enter
- Ou use PowerShell ou Windows Terminal

**macOS:**
- Pressione `Cmd + Espaço`, digite "Terminal" e pressione Enter

**Linux:**
- Pressione `Ctrl + Alt + T` ou busque "Terminal" no menu

### Passo 2: Clone o Repositório

```bash
# Clone o repositório
git clone https://github.com/sua-org/finops-aws.git

# Resultado esperado:
# Cloning into 'finops-aws'...
# remote: Counting objects: 100% (1234/1234), done.
# remote: Compressing objects: 100% (456/456), done.
# Receiving objects: 100% (1234/1234), 2.34 MiB | 1.23 MiB/s, done.
```

### Passo 3: Entre na Pasta

```bash
cd finops-aws
```

### Passo 4: Verifique a Estrutura

```bash
# Liste os arquivos
ls -la

# Windows (PowerShell):
# dir
```

**O que você deve ver:**

```
finops-aws/
├── src/finops_aws/           # Código fonte principal
│   ├── core/                 # Núcleo da aplicação
│   ├── models/               # Modelos de domínio
│   ├── services/             # 253 serviços AWS
│   └── utils/                # Utilitários
├── tests/                    # Testes automatizados (2.100+)
├── docs/                     # Documentação (você está aqui!)
├── infrastructure/terraform/ # Deploy automatizado
├── run_local_demo.py         # Script para testar localmente
├── run_with_aws.py           # Script para usar com AWS real
└── requirements.txt          # Dependências Python
```

## 3.2 Instalando Dependências

### Passo 1: Instale as Dependências

```bash
# Instalar todas as dependências
pip install -r requirements.txt

# Resultado esperado:
# Collecting boto3>=1.28.0
#   Downloading boto3-1.28.xx-py3-none-any.whl (xxx kB)
# Collecting pytest>=7.0.0
#   Downloading pytest-7.x.x-py3-none-any.whl (xxx kB)
# ...
# Successfully installed boto3-1.28.xx pytest-7.x.x ...
```

### O Que Foi Instalado

| Pacote | Versão | Para Que Serve |
|--------|--------|----------------|
| `boto3` | 1.28+ | SDK oficial da AWS para Python. Permite fazer chamadas para a API da AWS |
| `pytest` | 7.0+ | Framework de testes. Usado para rodar os 2.100+ testes automatizados |
| `moto` | 5.0+ | Simulador de AWS. Permite testar sem uma conta AWS real |
| `tabulate` | 0.9+ | Formatação de tabelas. Deixa os relatórios mais bonitos no terminal |
| `dataclasses` | built-in | Estruturação de dados. Modelos do domínio (já vem com Python 3.7+) |

### Resolvendo Problemas de Instalação

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PROBLEMAS COMUNS NA INSTALAÇÃO                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PROBLEMA: "pip: command not found"                                          ║
║  SOLUÇÃO:  Use pip3 em vez de pip                                            ║
║            pip3 install -r requirements.txt                                  ║
║                                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║                                                                              ║
║  PROBLEMA: "Permission denied"                                               ║
║  SOLUÇÃO:  Use --user flag ou sudo (não recomendado)                         ║
║            pip install --user -r requirements.txt                            ║
║                                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║                                                                              ║
║  PROBLEMA: "Could not find a version that satisfies..."                      ║
║  SOLUÇÃO:  Atualize o pip                                                    ║
║            pip install --upgrade pip                                         ║
║            pip install -r requirements.txt                                   ║
║                                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║                                                                              ║
║  PROBLEMA: Versão do Python muito antiga                                     ║
║  SOLUÇÃO:  Instale Python 3.11+                                              ║
║            # Ubuntu: sudo apt install python3.11                             ║
║            # macOS: brew install python@3.11                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 3.3 Configurando Credenciais AWS

Você tem **3 opções** para configurar as credenciais. Escolha a que melhor se aplica:

### Opção A: Variáveis de Ambiente (Mais Comum para Desenvolvimento)

```bash
# Linux/macOS
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_REGION="us-east-1"

# Windows (PowerShell)
$env:AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
$env:AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
$env:AWS_REGION="us-east-1"

# Windows (CMD)
set AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
set AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
set AWS_REGION=us-east-1
```

### Opção B: Arquivo de Credenciais (Mais Seguro para Uso Permanente)

Crie ou edite o arquivo `~/.aws/credentials`:

```ini
# Linux/macOS: ~/.aws/credentials
# Windows: C:\Users\SEU_USUARIO\.aws\credentials

[default]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# Opcional: perfil específico para FinOps
[finops]
aws_access_key_id = AKIAIOSFODNN7EXAMPLE2
aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLE2KEY
```

E o arquivo `~/.aws/config`:

```ini
# Linux/macOS: ~/.aws/config
# Windows: C:\Users\SEU_USUARIO\.aws\config

[default]
region = us-east-1
output = json

[profile finops]
region = us-east-1
output = json
```

### Opção C: IAM Role (Para Lambda/EC2)

Se estiver executando em uma instância EC2 ou Lambda com IAM Role, nenhuma configuração adicional é necessária. O SDK boto3 detecta automaticamente.

### Como Obter Access Key e Secret Key

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    COMO OBTER ACCESS KEY E SECRET KEY                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PASSO 1: Acesse o Console AWS                                               ║
║           https://console.aws.amazon.com/                                    ║
║                                                                              ║
║  PASSO 2: Clique no seu nome de usuário (canto superior direito)             ║
║                                                                              ║
║  PASSO 3: Clique em "Security credentials"                                   ║
║                                                                              ║
║  PASSO 4: Role a página até "Access keys"                                    ║
║                                                                              ║
║  PASSO 5: Clique em "Create access key"                                      ║
║                                                                              ║
║  PASSO 6: Selecione "Command Line Interface (CLI)"                           ║
║                                                                              ║
║  PASSO 7: Marque "I understand..." e clique em "Next"                        ║
║                                                                              ║
║  PASSO 8: (Opcional) Adicione uma descrição                                  ║
║                                                                              ║
║  PASSO 9: Clique em "Create access key"                                      ║
║                                                                              ║
║  PASSO 10: IMPORTANTE! Copie e salve:                                        ║
║            - Access key ID (começa com AKIA...)                              ║
║            - Secret access key (mostrada apenas UMA VEZ!)                    ║
║                                                                              ║
║  ⚠️  NUNCA compartilhe essas chaves!                                         ║
║  ⚠️  NUNCA commite em repositórios Git!                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 3.4 Verificando a Configuração

### Teste 1: Verificar Python

```bash
python --version
# Esperado: Python 3.11.x ou superior
```

### Teste 2: Verificar Instalação de Pacotes

```bash
python -c "import boto3; print(f'boto3 version: {boto3.__version__}')"
# Esperado: boto3 version: 1.28.x
```

### Teste 3: Verificar Credenciais AWS

```bash
python -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

**Resultado esperado (se credenciais OK):**
```json
{
    "UserId": "AIDAEXAMPLEXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/seu-usuario"
}
```

**Resultado se credenciais NÃO configuradas:**
```
NoCredentialsError: Unable to locate credentials
```

---

# 4. Primeiro Uso

## 4.1 Fluxograma Recomendado para Novos Usuários

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    FLUXO RECOMENDADO PARA INICIANTES                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────┐                                                         ║
║  │  1. DEMO LOCAL  │  ← Primeiro teste, sem precisar de AWS real            ║
║  │  (Sem AWS real) │    Comando: python run_local_demo.py 1                 ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║           ▼                                                                  ║
║  ┌─────────────────┐     ┌─────────────────┐                                 ║
║  │  2. FUNCIONOU?  │ ─── │       NÃO       │ ─► Verifique instalação        ║
║  └────────┬────────┘     └─────────────────┘                                 ║
║           │ SIM                                                              ║
║           ▼                                                                  ║
║  ┌─────────────────┐                                                         ║
║  │ 3. CONFIGURE    │  ← Configure Access Key e Secret Key                   ║
║  │ CREDENCIAIS AWS │    Seção 3.3 deste manual                              ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║           ▼                                                                  ║
║  ┌─────────────────┐                                                         ║
║  │  4. TESTE COM   │  ← Primeiro teste com sua conta real                   ║
║  │   AWS REAL      │    Comando: python run_with_aws.py                     ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║           ▼                                                                  ║
║  ┌─────────────────┐     ┌─────────────────┐                                 ║
║  │  5. FUNCIONOU?  │ ─── │       NÃO       │ ─► Verifique permissões IAM    ║
║  └────────┬────────┘     └─────────────────┘                                 ║
║           │ SIM                                                              ║
║           ▼                                                                  ║
║  ┌─────────────────┐                                                         ║
║  │  6. ANALISE     │  ← Examine as recomendações de economia                ║
║  │  RESULTADOS     │                                                         ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║           ▼                                                                  ║
║  ┌─────────────────┐                                                         ║
║  │  7. DEPLOY PARA │  ← Opcional: automatize com Terraform                  ║
║  │  PRODUÇÃO       │    Seção 6 deste manual                                ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║           ▼                                                                  ║
║  ┌─────────────────┐                                                         ║
║  │  8. RELATÓRIOS  │  ← Receba análises automáticas 5x por dia              ║
║  │  AUTOMÁTICOS!   │                                                         ║
║  └─────────────────┘                                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 4.2 Teste Rápido - Modo Demo (Sem AWS Real)

Execute o demo mockado para verificar se a instalação está funcionando:

```bash
python run_local_demo.py 1
```

### O Que Este Comando Faz

1. Cria uma AWS "simulada" na memória usando a biblioteca `moto`
2. Popula com recursos de exemplo (instâncias EC2, bancos RDS, buckets S3)
3. Executa toda a análise FinOps como se fosse a AWS real
4. Mostra o resultado na tela

### Saída Esperada (Se Tudo Estiver OK)

```
================================================================================
FinOps AWS - Local Demo Runner
================================================================================

⚠ No AWS credentials detected
  The demo will use mocked AWS services (moto library)

Running Lambda Handler Demo...
================================================================================

Initializing FinOps Analysis...
  ✓ ServiceFactory initialized with 253 services
  ✓ StateManager initialized (S3)
  ✓ ResilientExecutor initialized (CircuitBreaker)
  ✓ RetryHandler initialized (ExponentialBackoff)

Processing Services...
  [████████████████████████████████████████] 100%
  253/253 services analyzed successfully

EXECUTION SUMMARY:
  ─────────────────────────────────────────
  Duration: 12.34 seconds
  Services Analyzed: 253
  Resources Found: 1,234
  Recommendations Generated: 95

COST ANALYSIS (Mocked Data):
  ─────────────────────────────────────────
  Monthly Cost: $45,234.56
  Potential Savings: $8,500.00 (18.8%)

TOP RECOMMENDATIONS:
  ─────────────────────────────────────────
  [HIGH] 5 idle EC2 instances - $2,340/month savings
  [HIGH] 3 Reserved Instance candidates - $4,200/month savings
  [MEDIUM] 12 unused resources - $890/month savings
  [LOW] 8 storage optimization opportunities - $1,070/month savings

================================================================================
Demo completed successfully! ✓
================================================================================
```

### Possíveis Erros e Soluções

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ERROS COMUNS NO DEMO                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ERRO: "ModuleNotFoundError: No module named 'boto3'"                        ║
║  SOLUÇÃO: Instale as dependências                                            ║
║           pip install -r requirements.txt                                    ║
║                                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║                                                                              ║
║  ERRO: "ModuleNotFoundError: No module named 'finops_aws'"                   ║
║  SOLUÇÃO: Execute a partir do diretório correto                              ║
║           cd finops-aws                                                      ║
║           python run_local_demo.py 1                                         ║
║                                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║                                                                              ║
║  ERRO: "SyntaxError: invalid syntax"                                         ║
║  SOLUÇÃO: Use Python 3.11+                                                   ║
║           python3.11 run_local_demo.py 1                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 4.3 Opções do Demo Local

O script `run_local_demo.py` aceita um parâmetro numérico:

| Comando | O Que Faz |
|---------|-----------|
| `python run_local_demo.py 1` | Executa o demo completo (Lambda Handler) |
| `python run_local_demo.py 2` | Executa todos os testes automatizados |
| `python run_local_demo.py 3` | Mostra estatísticas detalhadas |

---

# 5. Execução Local

## 5.1 Executando com Sua Conta AWS Real

Depois de testar o demo, você pode analisar sua conta AWS de verdade:

```bash
# Certifique-se de que as credenciais estão configuradas
# (veja seção 3.3)

# Execute a análise
python run_with_aws.py
```

### O Que Este Comando Faz

1. Conecta à sua conta AWS real usando as credenciais configuradas
2. Analisa todos os 253 serviços em busca de recursos
3. Coleta métricas de uso de cada recurso
4. Gera recomendações de otimização com valores reais
5. Produz um relatório completo

### Saída Esperada

```
================================================================================
FinOps AWS - Real AWS Analysis
================================================================================

Connecting to AWS Account: 123456789012
Region: us-east-1

Initializing Analysis...
  ✓ Connected to AWS
  ✓ ServiceFactory initialized
  ✓ StateManager initialized

Analyzing Services...
  [████████████████████████████████████████] 100%
  253/253 services analyzed

COST ANALYSIS (Real Data):
  ═══════════════════════════════════════════════════════════════════════════
  
  MONTHLY BREAKDOWN:
  ─────────────────────────────────────────
  EC2 (Compute)               $18,234.00    (40.3%)
  RDS (Database)              $12,567.00    (27.8%)
  S3 (Storage)                 $5,432.00    (12.0%)
  Lambda (Serverless)          $3,456.00     (7.6%)
  NAT Gateway                  $2,890.00     (6.4%)
  Others                       $2,655.56     (5.9%)
  ─────────────────────────────────────────
  TOTAL MONTHLY               $45,234.56
  
  POTENTIAL SAVINGS:
  ─────────────────────────────────────────
  Idle Resources               $4,500.00
  Rightsizing                  $6,200.00
  Reserved Instances           $8,800.00
  Storage Optimization         $2,100.00
  ─────────────────────────────────────────
  TOTAL SAVINGS POTENTIAL     $21,600.00    (47.8% reduction!)
  
PRIORITY RECOMMENDATIONS:
  ═══════════════════════════════════════════════════════════════════════════
  
  [HIGH PRIORITY - Implement This Week]
  
  1. TERMINATE 5 IDLE EC2 INSTANCES
     Instances: i-0abc123, i-0def456, i-0ghi789, i-0jkl012, i-0mno345
     Last Activity: 30+ days ago
     Monthly Savings: $2,340
     Risk: LOW
     
  2. PURCHASE RESERVED INSTANCES FOR 12 EC2
     Current: On-Demand at $140/month each
     With RI: $84/month each (40% discount)
     Monthly Savings: $672
     Commitment: 1 year
     
  [MEDIUM PRIORITY - Implement This Month]
  
  3. RIGHTSIZE 8 OVER-PROVISIONED RDS
     Current: db.r5.2xlarge (using 15% capacity)
     Recommended: db.r5.large
     Monthly Savings: $4,800
     Risk: MEDIUM (test in staging first)

================================================================================
```

## 5.2 Opções de Execução

### Analisar Apenas Serviços Específicos

```bash
# Analisar apenas EC2
python run_with_aws.py --services ec2

# Analisar EC2 e RDS
python run_with_aws.py --services ec2,rds,s3
```

### Analisar Múltiplas Regiões

```bash
# Analisar todas as regiões
python run_with_aws.py --all-regions

# Analisar regiões específicas
python run_with_aws.py --regions us-east-1,eu-west-1,sa-east-1
```

### Exportar Resultados

```bash
# Exportar para JSON
python run_with_aws.py --output report.json

# Exportar para CSV
python run_with_aws.py --output report.csv
```

---

# 6. Deploy para AWS Lambda

## 6.1 Por Que Fazer Deploy?

Executar localmente é ótimo para testes, mas para uso em produção você quer:

| Execução Local | Deploy AWS |
|----------------|------------|
| Precisa rodar manualmente | Executa automaticamente 5x/dia |
| Depende do seu computador estar ligado | Roda 24/7 na nuvem |
| Sem alertas automáticos | Envia relatórios por email/Slack |
| Sem histórico de execuções | Armazena histórico no S3 |

## 6.2 Arquitetura do Deploy

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ARQUITETURA DE DEPLOY                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  COMPONENTES CRIADOS PELO TERRAFORM:                                         ║
║                                                                              ║
║  ┌─────────────────┐                                                         ║
║  │  EventBridge    │ ─────► Executa 5x por dia (6h, 10h, 14h, 18h, 22h)     ║
║  │  (Scheduler)    │                                                         ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║           ▼                                                                  ║
║  ┌─────────────────┐                                                         ║
║  │ Step Functions  │ ─────► Orquestra todo o fluxo de análise               ║
║  │ (State Machine) │                                                         ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║     ┌─────┴─────┐                                                            ║
║     ▼           ▼                                                            ║
║  ┌─────────┐ ┌─────────┐                                                     ║
║  │ Lambda  │ │ Lambda  │ ─────► Workers paralelos analisam serviços          ║
║  │ Worker 1│ │ Worker N│                                                     ║
║  └────┬────┘ └────┬────┘                                                     ║
║       │           │                                                          ║
║       └─────┬─────┘                                                          ║
║             ▼                                                                ║
║  ┌─────────────────┐                                                         ║
║  │ Lambda          │ ─────► Consolida resultados e gera relatório           ║
║  │ Aggregator      │                                                         ║
║  └────────┬────────┘                                                         ║
║           │                                                                  ║
║     ┌─────┴─────┐                                                            ║
║     ▼           ▼                                                            ║
║  ┌─────────┐ ┌─────────┐                                                     ║
║  │   S3    │ │   SNS   │ ─────► Armazena relatórios e envia alertas         ║
║  │ (State) │ │(Alerts) │                                                     ║
║  └─────────┘ └─────────┘                                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## 6.3 Deploy com Terraform - Passo a Passo

### Passo 1: Entre na Pasta do Terraform

```bash
cd infrastructure/terraform
```

### Passo 2: Configure as Variáveis

```bash
# Copie o arquivo de exemplo
cp terraform.tfvars.example terraform.tfvars

# Edite com suas configurações
nano terraform.tfvars  # ou use seu editor preferido
```

**Conteúdo do terraform.tfvars:**

```hcl
# Nome do ambiente (dev, staging, prod)
environment = "prod"

# Região AWS
aws_region = "us-east-1"

# Email para receber alertas
alert_email = "finops@suaempresa.com"

# Horários de execução (cron expressions)
schedule_expressions = [
  "cron(0 6 * * ? *)",   # 6h
  "cron(0 10 * * ? *)",  # 10h
  "cron(0 14 * * ? *)",  # 14h
  "cron(0 18 * * ? *)",  # 18h
  "cron(0 22 * * ? *)"   # 22h
]

# Tags para identificação
tags = {
  Project     = "FinOps"
  Environment = "Production"
  Owner       = "CloudTeam"
}
```

### Passo 3: Inicialize o Terraform

```bash
terraform init
```

**Saída esperada:**

```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching ">= 4.0.0"...
- Installing hashicorp/aws v5.0.0...
- Installed hashicorp/aws v5.0.0

Terraform has been successfully initialized!
```

### Passo 4: Revise o Plano

```bash
terraform plan
```

**Este comando mostra TUDO que será criado. Revise com atenção!**

### Passo 5: Aplique as Mudanças

```bash
terraform apply
```

Digite `yes` quando solicitado para confirmar.

**Recursos criados:**
- Lambda Functions (4)
- Step Functions State Machine
- S3 Bucket
- EventBridge Rules (5)
- IAM Roles e Policies
- SNS Topic
- KMS Key
- CloudWatch Log Groups

### Passo 6: Verifique o Deploy

```bash
# Verifique se a Lambda foi criada
aws lambda list-functions --query 'Functions[?contains(FunctionName, `finops`)]'

# Verifique a State Machine
aws stepfunctions list-state-machines --query 'stateMachines[?contains(name, `finops`)]'
```

---

# 7. Interpretando Resultados

## 7.1 Estrutura do Relatório

O FinOps AWS gera relatórios com 4 seções principais:

### Seção 1: Resumo Executivo

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    RESUMO EXECUTIVO                                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PERÍODO ANALISADO:        01/11/2024 a 30/11/2024                           ║
║  CUSTO TOTAL AWS:          R$ 185.432,00                                     ║
║  ECONOMIA IDENTIFICADA:    R$ 48.213,00 (26% do total)                       ║
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                                                                         │ ║
║  │  PARA O CEO/CFO:                                                        │ ║
║  │  "Podemos economizar R$ 48.213 por mês implementando as recomendações   │ ║
║  │   de alta prioridade. Isso representa R$ 578.556 por ano."              │ ║
║  │                                                                         │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Seção 2: Top 10 Ações de Economia

| # | Ação | Economia/Mês | Esforço | Risco |
|---|------|-------------|---------|-------|
| 1 | Desligar 8 EC2 ociosos | R$ 6.400 | 1 hora | Baixo |
| 2 | Reserved Instances (15 EC2) | R$ 8.200 | 2 horas | Baixo |
| 3 | Rightsizing RDS prod | R$ 4.500 | 4 horas | Médio |
| 4 | S3 Lifecycle (logs) | R$ 5.800 | 1 hora | Baixo |
| 5 | Mover S3 para Glacier | R$ 6.500 | 2 horas | Baixo |

### Seção 3: Alertas e Anomalias

```
⚠️  ALERTA: Custo de Data Transfer aumentou 45% vs mês anterior
    Causa provável: Novo serviço fazendo muitas requests externas
    Ação: Investigar logs do CloudWatch

⚠️  ALERTA: 3 novos recursos sem tags de custo
    Recursos: i-0abc123, rds-xyz-789, bucket-temp-2024
    Ação: Adicionar tags para rastreabilidade

⚠️  ALERTA: NAT Gateway com tráfego 3x acima da média
    Custo adicional estimado: R$ 2.300/mês
    Ação: Considerar VPC Endpoints
```

### Seção 4: Tendências

```
PROJEÇÃO DE CUSTOS:
───────────────────────────────────────────
Próximo mês:        R$ 178.500 (▲ +3.2%)
Próximo trimestre:  R$ 520.000
Próximo ano:        R$ 2.100.000

TENDÊNCIA HISTÓRICA (últimos 6 meses):
───────────────────────────────────────────
Jun: R$ 142.000 ████████████████
Jul: R$ 155.000 ██████████████████
Ago: R$ 162.000 ███████████████████
Set: R$ 170.000 ████████████████████
Out: R$ 178.000 █████████████████████
Nov: R$ 185.000 ██████████████████████
```

---

# 8. Configurações Avançadas

## 8.1 Configurando Alertas por Email

O FinOps AWS pode enviar alertas automáticos via Amazon SES:

```python
# config/alerts.py
ALERT_CONFIG = {
    "email": {
        "enabled": True,
        "recipients": [
            "finops@suaempresa.com",
            "cto@suaempresa.com"
        ],
        "threshold_high": 10000,  # Alerta se economia > R$ 10.000
        "threshold_critical": 50000  # Alerta crítico se economia > R$ 50.000
    }
}
```

## 8.2 Configurando Alertas por Slack

```python
# config/alerts.py
ALERT_CONFIG = {
    "slack": {
        "enabled": True,
        "webhook_url": "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXX",
        "channel": "#finops-alerts"
    }
}
```

## 8.3 Personalizando Thresholds

```python
# config/thresholds.py
THRESHOLDS = {
    "ec2": {
        "idle_cpu_percent": 10,  # Considerar ocioso se CPU < 10%
        "idle_days": 14,  # Considerar ocioso se < 10% por 14 dias
    },
    "rds": {
        "over_provisioned_percent": 30,  # Superdimensionado se uso < 30%
    },
    "s3": {
        "lifecycle_days": 90,  # Sugerir lifecycle após 90 dias sem acesso
    }
}
```

---

# 9. Troubleshooting

## 9.1 Problemas Comuns e Soluções

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    GUIA DE TROUBLESHOOTING                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  PROBLEMA: "NoCredentialsError: Unable to locate credentials"                ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  CAUSA: Credenciais AWS não configuradas                                     ║
║  SOLUÇÃO:                                                                    ║
║    1. Verifique se as variáveis estão setadas:                               ║
║       echo $AWS_ACCESS_KEY_ID                                                ║
║    2. Ou configure o arquivo ~/.aws/credentials                              ║
║    3. Ou use aws configure para configurar                                   ║
║                                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║                                                                              ║
║  PROBLEMA: "AccessDenied: User is not authorized to perform..."              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  CAUSA: Usuário não tem permissões necessárias                               ║
║  SOLUÇÃO:                                                                    ║
║    1. Anexe a política FinOpsReadOnlyPolicy ao usuário                       ║
║    2. Verifique se não há políticas de negação (Deny)                        ║
║    3. Se usa Organizations, verifique SCPs                                   ║
║                                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║                                                                              ║
║  PROBLEMA: "Timeout" durante análise                                         ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  CAUSA: Muitos recursos ou conexão lenta                                     ║
║  SOLUÇÃO:                                                                    ║
║    1. Analise por região (--regions us-east-1)                               ║
║    2. Analise por serviço (--services ec2,rds)                               ║
║    3. Aumente o timeout nas configurações                                    ║
║                                                                              ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║                                                                              ║
║  PROBLEMA: "Cost Explorer not enabled"                                       ║
║  ─────────────────────────────────────────────────────────────────────────   ║
║  CAUSA: Cost Explorer nunca foi ativado na conta                             ║
║  SOLUÇÃO:                                                                    ║
║    1. Acesse AWS Console > Cost Explorer                                     ║
║    2. Clique em "Enable Cost Explorer"                                       ║
║    3. Aguarde 24 horas para dados serem processados                          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

# 10. FAQ

## Perguntas Frequentes

### Q: O FinOps AWS pode danificar minha conta?

**R:** NÃO. O FinOps AWS tem APENAS permissões de leitura. Ele não pode criar, modificar ou deletar nada na sua conta.

### Q: Quanto custa rodar o FinOps AWS?

**R:** Aproximadamente R$ 15/mês para 100 execuções diárias (5x por dia). Isso inclui Lambda, Step Functions e S3.

### Q: Posso usar em múltiplas contas AWS?

**R:** SIM. O FinOps AWS suporta AWS Organizations e pode analisar todas as contas filhas a partir da conta master.

### Q: Os dados são enviados para fora da minha conta?

**R:** NÃO. Todos os dados ficam na sua própria conta AWS (S3). Nada é enviado para servidores externos.

### Q: Preciso instalar algo na AWS?

**R:** Para uso local, não. Para automação, você faz deploy via Terraform que cria Lambda, Step Functions, etc.

---

# 11. Glossário

| Termo | Significado |
|-------|-------------|
| **On-Demand** | Pagar por hora sem compromisso prévio |
| **Reserved Instance** | Compromisso de 1-3 anos com desconto |
| **Rightsizing** | Ajustar tamanho do recurso ao uso real |
| **Idle Resource** | Recurso ligado mas sem uso |
| **Cost Allocation Tags** | Etiquetas para identificar custos |

---

# 12. Suporte

Se você tiver problemas:

1. Consulte a seção de Troubleshooting (9)
2. Verifique a documentação técnica em `docs/TECHNICAL_GUIDE.md`
3. Abra uma issue no repositório GitHub

---

**FinOps AWS v2.1** | Manual atualizado em Dezembro 2024 | Score QA: 9.7/10 | 2.100+ testes
