# FinOps AWS - Manual do Usuário

## Versão 2.0 - Dezembro 2024

---

## 1. Introdução

O **FinOps AWS Dashboard** é uma ferramenta visual para análise de custos da sua infraestrutura AWS. Ele mostra automaticamente onde você está gastando dinheiro e sugere formas de economizar.

---

## 2. Acessando o Dashboard

1. Abra o navegador e acesse a URL do dashboard
2. O sistema carregará automaticamente os dados da sua conta AWS
3. Aguarde enquanto "Buscando dados da AWS..." é exibido

---

## 3. Entendendo o Dashboard

### 3.1 Painel Superior

| Card | O que mostra |
|------|--------------|
| **Custo Total (30D)** | Quanto você gastou nos últimos 30 dias |
| **Economia Potencial** | Quanto você pode economizar seguindo as recomendações |
| **Serviços Analisados** | Quantos serviços AWS foram verificados |
| **Recomendações** | Número de sugestões de otimização |

### 3.2 Botões de Ação

| Botão | Função |
|-------|--------|
| **Análise Completa** | Executa análise de custos + recomendações |
| **Apenas Custos** | Mostra apenas dados de custo |
| **Apenas Recomendações** | Mostra apenas sugestões de economia |
| **Multi-Region** | Analisa todas as regiões AWS |

### 3.3 Exportação

| Formato | Uso |
|---------|-----|
| **Exportar CSV** | Abrir no Excel/Google Sheets |
| **Exportar JSON** | Integração com outros sistemas |
| **Versão Impressão** | Relatório para reuniões |

---

## 4. Tipos de Recomendações

### Prioridade ALTA (vermelho)
- **Ação imediata necessária**
- Exemplos: volumes órfãos custando dinheiro, IPs não utilizados

### Prioridade MÉDIA (amarelo)
- **Revisar em breve**
- Exemplos: habilitar versionamento S3, lifecycle policies

### Prioridade BAIXA (verde)
- **Otimização opcional**
- Exemplos: migrar para tipos de instância mais novos

### Informativo (azul)
- **Apenas informação**
- Exemplos: alertas de custo de NAT Gateway

---

## 5. Top 10 Serviços por Custo

A tabela mostra seus 10 serviços AWS mais caros:

| Coluna | Significado |
|--------|-------------|
| **Serviço** | Nome do serviço AWS |
| **Custo Mensal** | Valor gasto no mês |
| **% do Total** | Percentual do custo total |
| **Tendência** | Subindo, estável ou descendo |
| **Status** | OK, Alerta ou Crítico |

---

## 6. Integrações

### AWS Compute Optimizer
- Sugere o tamanho correto para suas instâncias EC2
- Precisa estar habilitado na sua conta AWS

### Cost Explorer
- Recomenda Reserved Instances e Savings Plans
- Mostra onde você pode economizar com compromissos

### Trusted Advisor
- Verificações de boas práticas AWS
- Requer plano Business ou Enterprise

### Amazon Q (IA)
- Gera relatórios inteligentes personalizados
- Precisa de configuração adicional

---

## 7. Recomendações Comuns

| Recomendação | O que fazer | Economia esperada |
|--------------|-------------|-------------------|
| **EBS Órfão** | Deletar volumes não anexados | $0.10/GB/mês |
| **EIP Não Associado** | Liberar IPs não utilizados | $3.60/mês cada |
| **S3 sem Lifecycle** | Configurar transição automática | 20-40% |
| **EC2 Parado** | Terminar instâncias paradas | Variável |

---

## 8. Perguntas Frequentes

### Por que meu custo mostra $0?
- Conta nova ou com poucos recursos
- Dados do Cost Explorer demoram 24h para aparecer

### Por que algumas integrações estão inativas?
- Compute Optimizer precisa ser habilitado manualmente
- Trusted Advisor requer plano de suporte Business/Enterprise
- Amazon Q precisa de configuração do Application ID

### Com que frequência os dados são atualizados?
- A cada vez que você clica em "Análise Completa"
- Dados de custo são atualizados pela AWS a cada 24h

---

## 9. Contato e Suporte

Para dúvidas ou problemas, verifique:
1. Se as credenciais AWS estão configuradas
2. Se você tem permissões IAM suficientes
3. Os logs do sistema para erros específicos

---

*Manual do Usuário - Versão 2.0 - Dezembro 2024*
