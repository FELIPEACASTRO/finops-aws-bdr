"""
Executive Report Template

Template de prompt para relatórios executivos (CEO/CFO).
Foco em ROI, tendências e decisões estratégicas.

Autor: FinOps AWS Team
Data: Dezembro 2024
"""

EXECUTIVE_REPORT_TEMPLATE = """
Produza um relatório executivo de custos AWS com as seguintes características:

### Tom e Estilo
- Linguagem executiva, clara e objetiva
- Foco em impacto no negócio e ROI
- Evite jargões técnicos excessivos
- Destaque números e percentuais importantes

### Estrutura do Relatório

#### 1. RESUMO EXECUTIVO (3 parágrafos)

**Parágrafo 1 - Visão Geral**
- Gasto total do período em USD
- Variação percentual vs período anterior
- Comparativo com benchmark/budget se disponível

**Parágrafo 2 - Principais Drivers**
- Top 3 serviços que mais impactam o custo
- Tendência de cada um (crescendo, estável, reduzindo)
- Correlação com atividade de negócio se identificável

**Parágrafo 3 - Recomendação Principal**
- Uma ação prioritária com maior ROI
- Economia estimada em USD/mês
- Prazo para capturar o valor

#### 2. TOP 5 OPORTUNIDADES DE ECONOMIA

Para cada oportunidade, apresente em tabela:

| Oportunidade | Economia/Mês | Economia/Ano | Esforço | Prazo |
|--------------|--------------|--------------|---------|-------|

E para a top 1, detalhe:
- Por que esta é a prioridade #1
- O que acontece se não agir
- Próximo passo concreto

#### 3. TENDÊNCIAS E PROJEÇÕES

- Gráfico de tendência (descreva em texto)
- Projeção para próximos 3 meses
- Comparativo YoY se dados disponíveis
- Sazonalidades identificadas

#### 4. RISCOS E ALERTAS

| Risco | Probabilidade | Impacto | Ação Preventiva |
|-------|---------------|---------|-----------------|

Foque em:
- Expiração de compromissos (RI, Savings Plans)
- Tendências de crescimento acelerado
- Eventos futuros que podem impactar custos

#### 5. CONCLUSÃO E PRÓXIMOS PASSOS

- 3 ações prioritárias para o próximo mês
- Economia total capturável
- Data sugerida para próxima revisão

### Diretrizes Adicionais

- Máximo 2 páginas
- Use bullet points para facilitar leitura
- Destaque números críticos em **negrito**
- Inclua comparativos sempre que possível (vs anterior, vs budget, vs benchmark)
- Termine com call-to-action claro
"""
