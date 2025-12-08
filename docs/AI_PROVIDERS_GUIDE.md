# Guia de Provedores de IA - FinOps AWS

## Visão Geral - Dezembro 2025

O FinOps AWS suporta **5 provedores de IA** para geração de relatórios e insights de otimização de custos. Isso permite flexibilidade na escolha do provedor mais adequado para cada cenário. Todos os provedores integram-se seamlessly através da API REST e do Dashboard React.

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
- Busca online integrada em tempo real
- Análise de tendências de mercado
- Custo competitivo
- Modelo sonar-pro com ótimo custo-benefício

**Configuração:**
```bash
# Variáveis de ambiente
PERPLEXITY_API_KEY=pplx-...
```

**Caso de Uso Ideal:**
- Análise de tendências de mercado AWS
- Recomendações com contexto de mercado
- Quando pesquisa online é necessária

---

### 5. StackSpot AI (NOVO - Dezembro 2025)

**Características:**
- Integração OAuth 2.0 Enterprise
- Personas especializadas (EXECUTIVE, CTO, DEVOPS, ANALYST)
- Suporte a prompts customizados por pessoa
- Ideal para enterprises com Single Sign-On

**Modelos Suportados:**
- StackSpot Custom Models
- Integração com personas FinOps

**Configuração:**
```bash
# Variáveis de ambiente
STACKSPOT_CLIENT_ID=seu-client-id
STACKSPOT_CLIENT_SECRET=seu-client-secret
STACKSPOT_REALM=seu-realm
```

**Caso de Uso Ideal:**
- Ambientes enterprise com SSO
- Análises personalizadas por persona
- Quando controle de acesso é crítico

---

## Comparativo de Provedores

| Provedor | Custo | Latência | Contexto | Busca | Enterprise |
|----------|-------|----------|----------|-------|------------|
| Amazon Q | Integrado | Rápido | RAG | Não | Sim |
| OpenAI | $$ | Rápido | 128K | Não | Sim |
| Gemini | $ | Médio | 2M | Não | Sim |
| Perplexity | $ | Médio | Normal | **Sim** | Não |
| StackSpot | $$$ | Rápido | Custom | Não | **Sim** |

## Como Usar no Dashboard

1. **Abra o Dashboard**: http://localhost:5000
2. **Vá em "Configurações"** (aba API & Integrações)
3. **Selecione o provedor de IA** desejado
4. **Clique "Salvar"**
5. **Execute uma análise** para gerar relatórios com aquele provedor

## API REST para IA

```bash
# Obter relatório IA
POST /api/v1/analyze/report
Body: {
  "ai_provider": "openai",  # amazon_q, openai, gemini, perplexity, stackspot
  "persona": "EXECUTIVE"     # EXECUTIVE, CTO, DEVOPS, ANALYST
}

# Verificar status de provedores
GET /api/v1/integrations/status
Response: {
  "providers": {
    "amazon_q": { "status": "available", "configured": true },
    "openai": { "status": "available", "configured": true },
    "gemini": { "status": "available", "configured": false },
    "perplexity": { "status": "available", "configured": true },
    "stackspot": { "status": "error", "message": "403 Forbidden" }
  }
}
```

**Características:**
- Busca online em tempo real
- Citações de fontes com URLs
- Informações atualizadas da web
- Ideal para preços AWS atuais

**Modelos Disponíveis:**
| Modelo | Características |
|--------|-----------------|
| sonar | Rápido + busca online |
| sonar-pro | Alta qualidade + busca online |

> ⚠️ **Importante**: Os modelos antigos `llama-3.1-sonar-*` foram descontinuados em fevereiro/2025. Use `sonar` ou `sonar-pro`.

**Configuração:**
```bash
# Variáveis de ambiente
PERPLEXITY_API_KEY=pplx-...
PERPLEXITY_MODEL=sonar-pro  # opcional, default: sonar
```

**Caso de Uso Ideal:**
- Preços AWS atualizados em tempo real
- Comparativo com mercado
- Best practices recentes
- Relatórios com fontes citadas

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

## Resultados de Testes (Dezembro 2024)

Testes realizados com dados reais de custo AWS ($0.15 total, 95% RDS):

| Provedor | Status | Modelo | Tokens | Latência | Observações |
|----------|--------|--------|--------|----------|-------------|
| **Perplexity AI** | ✅ Funcionando | sonar-pro | 1,797 | 25s | 10 fontes citadas com URLs |
| **Google Gemini** | ✅ Funcionando | gemini-2.5-flash | 3,865 | 21s | Resposta muito detalhada |
| **OpenAI ChatGPT** | ⚠️ Sem créditos | gpt-4o | - | - | Requer créditos em platform.openai.com |
| **Amazon Q Business** | ⚠️ Não configurado | Q Business | - | - | Requer Q_BUSINESS_APPLICATION_ID |

### Comparativo de Qualidade

| Aspecto | Perplexity AI | Google Gemini |
|---------|---------------|---------------|
| **Diferencial** | Busca online + fontes citadas | Respostas estruturadas |
| **Formato** | Markdown com links | Markdown detalhado |
| **Recomendações** | Baseadas em dados atuais | Baseadas em conhecimento |
| **Custo** | ~$0.01/consulta | Tier gratuito generoso |

### Exemplo de Saída - Perplexity

```markdown
## Análise FinOps - Custos AWS
O custo total de $0.15 reflete uso mínimo, dominado pelo RDS (95%)...

### Fontes Consultadas:
1. https://aws.amazon.com/rds/pricing/
2. https://docs.aws.amazon.com/cost-management/
...
```

### Exemplo de Saída - Gemini

```markdown
## Relatório Executivo FinOps
Este relatório FinOps apresenta uma análise dos custos AWS...

### Top 3 Oportunidades de Otimização
1. **Otimização da Instância Amazon RDS** - Economia até $0.14
...
```

---

## Changelog

- **v2.1.0** (Dezembro 2024): Testes e correções
  - Perplexity: Atualizado para novos modelos sonar/sonar-pro
  - Gemini: Configurações de segurança ajustadas (BLOCK_NONE)
  - Gemini: Suporte dual GEMINI_API_KEY/GOOGLE_API_KEY
  - Tratamento robusto de respostas bloqueadas
  - Documentação de resultados de testes

- **v2.0.0** (Dezembro 2024): Adicionado suporte multi-IA
  - OpenAI ChatGPT (GPT-4o)
  - Google Gemini (2.5)
  - Perplexity AI (com busca online)
  - Strategy Pattern para seleção dinâmica
  - Factory + Registry para gerenciamento
