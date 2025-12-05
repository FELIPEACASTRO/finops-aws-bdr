# Guia de Provedores de IA - FinOps AWS

## Visão Geral

O FinOps AWS suporta múltiplos provedores de IA para geração de relatórios e insights de otimização de custos. Isso permite flexibilidade na escolha do provedor mais adequado para cada cenário.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ARQUITETURA MULTI-IA                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────────┐      ┌──────────────────────────────────┐   │
│   │   Dashboard      │      │        AI Provider Factory       │   │
│   │   Web/API        │─────▶│        (Strategy Pattern)        │   │
│   └──────────────────┘      └────────────────┬─────────────────┘   │
│                                              │                      │
│                      ┌───────────────────────┼───────────────────┐  │
│                      │                       │                   │  │
│                      ▼                       ▼                   ▼  │
│            ┌─────────────────┐    ┌─────────────────┐   ┌────────────┐
│            │   Amazon Q      │    │    OpenAI       │   │  Gemini   ││
│            │   Business      │    │    ChatGPT      │   │  Google   ││
│            └─────────────────┘    └─────────────────┘   └────────────┘
│                      │                       │                   │  │
│                      │                       ▼                   │  │
│                      │            ┌─────────────────┐            │  │
│                      │            │   Perplexity    │            │  │
│                      │            │   (c/ busca)    │            │  │
│                      │            └─────────────────┘            │  │
│                      │                       │                   │  │
│                      └───────────────────────┴───────────────────┘  │
│                                              │                      │
│                                              ▼                      │
│                              ┌───────────────────────────┐          │
│                              │   AIResponse Padronizado  │          │
│                              │   (content, tokens, etc)  │          │
│                              └───────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Provedores Suportados

### 1. Amazon Q Business (AWS Nativo)

**Características:**
- Integração nativa com AWS
- Base de conhecimento customizada (RAG)
- Segurança IAM integrada
- Sem custo adicional de API

**Configuração:**
```bash
# Variáveis de ambiente
Q_BUSINESS_APPLICATION_ID=seu-app-id
AWS_REGION=us-east-1
```

**Caso de Uso Ideal:**
- Ambientes enterprise AWS
- Necessidade de RAG com documentos internos
- Compliance e segurança rigorosos

---

### 2. OpenAI ChatGPT

**Características:**
- Modelos GPT-4o de última geração
- Excelente raciocínio e análise
- Function calling avançado
- Grande contexto (128K tokens)

**Modelos Disponíveis:**
| Modelo | Contexto | Melhor Para |
|--------|----------|-------------|
| gpt-4o | 128K | Análises complexas |
| gpt-4o-mini | 128K | Custo-benefício |
| gpt-4-turbo | 128K | Alta precisão |
| gpt-3.5-turbo | 16K | Tarefas simples |

**Configuração:**
```bash
# Variáveis de ambiente
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o  # opcional
```

**Caso de Uso Ideal:**
- Análises detalhadas e complexas
- Geração de relatórios extensos
- Quando precisão é crítica

---

### 3. Google Gemini

**Características:**
- Modelos Gemini 2.5 de última geração
- Contexto ultra-longo (até 2M tokens)
- Multimodal (texto, imagens, código)
- Custo competitivo

**Modelos Disponíveis:**
| Modelo | Contexto | Melhor Para |
|--------|----------|-------------|
| gemini-2.5-pro | 2M | Análises profundas |
| gemini-2.5-flash | 1M | Velocidade |
| gemini-1.5-pro | 2M | Estabilidade |

**Configuração:**
```bash
# Variáveis de ambiente
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.5-flash  # opcional
```

**Caso de Uso Ideal:**
- Análise de grandes volumes de dados
- Contexto muito longo necessário
- Custo é fator importante

---

### 4. Perplexity AI

**Características:**
- Busca online em tempo real
- Citações de fontes
- Informações atualizadas
- Ideal para preços AWS atuais

**Modelos Disponíveis:**
| Modelo | Características |
|--------|-----------------|
| llama-3.1-sonar-large-128k-online | Alta qualidade + busca |
| llama-3.1-sonar-small-128k-online | Rápido + busca |
| llama-3.1-sonar-huge-128k-online | Máxima qualidade |

**Configuração:**
```bash
# Variáveis de ambiente
PERPLEXITY_API_KEY=pplx-...
PERPLEXITY_MODEL=llama-3.1-sonar-large-128k-online  # opcional
```

**Caso de Uso Ideal:**
- Preços AWS atualizados em tempo real
- Comparativo com mercado
- Best practices recentes

---

## Uso Programático

### Exemplo Básico

```python
from finops_aws.ai_consultant.providers import (
    AIProviderFactory,
    PersonaType
)

# Criar provedor específico
provider = AIProviderFactory.create("openai")

# Verificar saúde
health = provider.health_check()
print(f"Status: {health['healthy']}")

# Gerar relatório
costs = {"total": 1500.00, "by_service": {"EC2": 800, "RDS": 500}}
resources = {"ec2_instances": 10, "rds_instances": 2}

response = provider.generate_report(
    costs=costs,
    resources=resources,
    persona=PersonaType.EXECUTIVE
)

print(response.content)
print(f"Tokens: {response.tokens_used}")
print(f"Latência: {response.latency_ms}ms")
```

### Seleção Automática

```python
from finops_aws.ai_consultant.providers import AIProviderFactory

# Cria todos os provedores disponíveis
available = AIProviderFactory.create_all_available()

# Usa o primeiro disponível
if available:
    provider = list(available.values())[0]
    response = provider.generate_report(costs, resources, PersonaType.CTO)
```

### Via Dashboard API

```python
from finops_aws.dashboard.integrations import get_ai_insights

# Auto-seleciona provedor
insights = get_ai_insights(
    costs=costs,
    resources=resources,
    persona='EXECUTIVE',
    provider='auto'  # ou 'openai', 'gemini', 'perplexity', 'amazon_q'
)

for insight in insights:
    print(insight['title'])
    print(insight['description'])
```

---

## Comparativo de Provedores

```
┌────────────────┬────────────────┬────────────────┬────────────────┬────────────────┐
│ Característica │ Amazon Q       │ OpenAI         │ Gemini         │ Perplexity     │
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┤
│ API Key        │ Não (IAM)      │ Sim            │ Sim            │ Sim            │
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┤
│ RAG/Knowledge  │ ✅ Nativo      │ ❌             │ ❌             │ ✅ Web Search  │
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┤
│ Contexto Max   │ Variável       │ 128K tokens    │ 2M tokens      │ 128K tokens    │
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┤
│ Busca Online   │ ❌             │ ❌             │ ❌             │ ✅             │
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┤
│ Citações       │ ✅ Docs        │ ❌             │ ❌             │ ✅ Web         │
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┤
│ Preços AWS     │ Estático       │ Estático       │ Estático       │ Tempo Real     │
├────────────────┼────────────────┼────────────────┼────────────────┼────────────────┤
│ Melhor Para    │ Enterprise     │ Precisão       │ Custo-Benefício│ Atualização    │
└────────────────┴────────────────┴────────────────┴────────────────┴────────────────┘
```

---

## Fluxo de Seleção de Provedor

```
                    ┌─────────────────────┐
                    │   Início Análise    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Provider = 'auto'? │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │ Sim            │                │ Não
              ▼                │                ▼
   ┌─────────────────────┐     │     ┌─────────────────────┐
   │  Verificar Health   │     │     │  Criar Provider     │
   │  de todos           │     │     │  Específico         │
   └──────────┬──────────┘     │     └──────────┬──────────┘
              │                │                │
              ▼                │                │
   ┌─────────────────────┐     │                │
   │  Selecionar 1º      │     │                │
   │  Healthy            │     │                │
   └──────────┬──────────┘     │                │
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  generate_report()  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  AIResponse         │
                    │  Padronizado        │
                    └─────────────────────┘
```

---

## Personas Disponíveis

Todas os provedores suportam as mesmas 4 personas:

### EXECUTIVE (CEO/CFO)
- Foco: ROI, impacto no negócio
- Formato: 2 páginas, bullet points
- Tom: Executivo

### CTO (CTO/VP Eng)
- Foco: Arquitetura, trade-offs técnicos
- Formato: Roadmap, diagramas
- Tom: Técnico-estratégico

### DEVOPS (DevOps/SRE)
- Foco: Implementação, scripts
- Formato: Comandos AWS CLI
- Tom: Prático

### ANALYST (FinOps Analyst)
- Foco: KPIs, métricas, benchmarks
- Formato: Tabelas, dados
- Tom: Analítico

---

## Tratamento de Erros

```python
from finops_aws.ai_consultant.providers import AIProviderFactory

provider = AIProviderFactory.create("openai")

# Verificar disponibilidade antes de usar
health = provider.health_check()
if not health['healthy']:
    error = health['details'].get('error')
    print(f"Provedor indisponível: {error}")
    
    # Fallback para outro provedor
    provider = AIProviderFactory.create("gemini")

# Tratar erros de geração
try:
    response = provider.generate_report(costs, resources, PersonaType.EXECUTIVE)
except RuntimeError as e:
    print(f"Erro na geração: {e}")
except ValueError as e:
    print(f"Configuração inválida: {e}")
```

---

## Custos Estimados

| Provedor | Modelo | Custo por 1M tokens (input) | Custo por 1M tokens (output) |
|----------|--------|-------------------------------|-------------------------------|
| Amazon Q | Q Business | Por uso AWS | Por uso AWS |
| OpenAI | gpt-4o | $2.50 | $10.00 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| Gemini | gemini-2.5-flash | $0.075 | $0.30 |
| Gemini | gemini-2.5-pro | $1.25 | $5.00 |
| Perplexity | sonar-large | $1.00 | $1.00 |

*Preços aproximados, consulte documentação oficial para valores atuais.*

---

## Próximos Passos

1. **Configurar API Keys**: Configure as variáveis de ambiente para os provedores desejados
2. **Testar Health Check**: Verifique se os provedores estão funcionando
3. **Escolher Provedor**: Selecione o provedor mais adequado para seu caso de uso
4. **Monitorar Custos**: Acompanhe o consumo de tokens para otimizar custos

---

## Changelog

- **v2.0.0** (Dezembro 2024): Adicionado suporte multi-IA
  - OpenAI ChatGPT (GPT-4o)
  - Google Gemini (2.5)
  - Perplexity AI (com busca online)
  - Strategy Pattern para seleção dinâmica
  - Factory + Registry para gerenciamento
