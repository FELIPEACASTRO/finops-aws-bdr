import { useState, useEffect } from 'react';
import {
  Bot,
  Send,
  User,
  Sparkles,
  Loader2,
  Copy,
  Download,
  RefreshCw,
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Select,
  Textarea,
  Badge,
} from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import styles from './AIConsultant.module.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  persona?: string;
}

const personas = [
  { value: 'EXECUTIVE', label: 'Executivo', description: 'Resumo estratégico para C-Level' },
  { value: 'CTO', label: 'CTO', description: 'Visão técnica e arquitetural' },
  { value: 'DEVOPS', label: 'DevOps', description: 'Foco em automação e infraestrutura' },
  { value: 'ANALYST', label: 'Analista', description: 'Detalhes completos e métricas' },
];

const suggestedQuestionsByPersona: Record<string, string[]> = {
  EXECUTIVE: [
    'Qual é o resumo executivo dos nossos gastos AWS este mês?',
    'Qual o ROI das otimizações implementadas?',
    'Como estamos comparados ao orçamento anual?',
    'Quais são os riscos financeiros na nossa infraestrutura?',
    'Qual a tendência de custos para o próximo trimestre?',
  ],
  CTO: [
    'Qual arquitetura seria mais custo-efetiva para nossos workloads?',
    'Devemos migrar para containers ou serverless?',
    'Como otimizar custos sem impactar performance?',
    'Quais serviços AWS deveríamos considerar adotar?',
    'Qual estratégia de multi-region é mais econômica?',
  ],
  DEVOPS: [
    'Quais instâncias EC2 podem ser automatizadas para desligar?',
    'Como implementar rightsizing automatizado?',
    'Quais recursos órfãos devo remover?',
    'Como otimizar custos de CI/CD pipelines?',
    'Quais políticas de lifecycle devo aplicar no S3?',
  ],
  ANALYST: [
    'Quais são os principais drivers de custo por serviço?',
    'Qual a taxa de utilização de Reserved Instances?',
    'Como está a cobertura de Savings Plans?',
    'Quais recursos estão subutilizados (< 10%)?',
    'Qual o breakdown de custos por tag de projeto?',
  ],
};

export function AIConsultant() {
  const { get, post, loading } = useFetch();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [persona, setPersona] = useState('ANALYST');
  const [provider, setProvider] = useState('perplexity');

  useEffect(() => {
    // Carregar provedor das configurações
    const loadProvider = async () => {
      try {
        const response = await get<any>('/api/v1/settings');
        if (response?.status === 'success' && response?.settings?.ai_provider) {
          console.log('Provedor de IA carregado:', response.settings.ai_provider);
          setProvider(response.settings.ai_provider);
        }
      } catch (error) {
        console.error('Erro ao carregar provedor:', error);
      }
    };
    loadProvider();
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    const response = await post<any>('/api/v1/ai-report', {
      question: input.trim(),
      persona: persona,
      provider: provider,
    });

    const assistantMessage: Message = {
      id: `msg-${Date.now()}-response`,
      role: 'assistant',
      content: response?.report?.content || response?.report || response?.error || 'Desculpe, não consegui processar sua solicitação.',
      timestamp: new Date(),
      persona: persona,
    };

    setMessages((prev) => [...prev, assistantMessage]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const clearChat = () => {
    setMessages([]);
  };

  const useSuggestion = (question: string) => {
    setInput(question);
  };

  return (
    <div className={styles.page}>
      <Header
        title="Consultor IA"
        subtitle="Assistente inteligente para análise de custos AWS"
      />

      <div className={styles.container}>
        <aside className={styles.sidebar}>
          <Card>
            <CardHeader title="Configurações" />
            <CardContent>
              <Select
                label="Persona"
                value={persona}
                onChange={setPersona}
                options={personas.map((p) => ({ value: p.value, label: p.label }))}
              />
              <p className={styles.personaDescription}>
                {personas.find((p) => p.value === persona)?.description}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader title="Perguntas Sugeridas" />
            <CardContent>
              <div className={styles.suggestions}>
                {(suggestedQuestionsByPersona[persona] || suggestedQuestionsByPersona.ANALYST).map((question, i) => (
                  <button
                    key={`${persona}-${i}`}
                    className={styles.suggestionBtn}
                    onClick={() => useSuggestion(question)}
                  >
                    <Sparkles size={14} />
                    {question}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Button
            variant="ghost"
            icon={<RefreshCw size={16} />}
            onClick={clearChat}
            className={styles.clearBtn}
          >
            Limpar Conversa
          </Button>
        </aside>

        <main className={styles.chatArea}>
          <Card className={styles.chatCard}>
            <div className={styles.messages}>
              {messages.length === 0 ? (
                <div className={styles.welcome}>
                  <Bot size={64} />
                  <h2>Bem-vindo ao Consultor FinOps IA</h2>
                  <p>
                    Faça perguntas sobre seus custos AWS, otimizações recomendadas,
                    ou peça análises específicas. Selecione uma persona para
                    personalizar o estilo das respostas.
                  </p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`${styles.message} ${styles[msg.role]}`}
                  >
                    <div className={styles.messageAvatar}>
                      {msg.role === 'user' ? (
                        <User size={20} />
                      ) : (
                        <Bot size={20} />
                      )}
                    </div>
                    <div className={styles.messageContent}>
                      <div className={styles.messageHeader}>
                        <span className={styles.messageSender}>
                          {msg.role === 'user' ? 'Você' : 'FinOps AI'}
                        </span>
                        {msg.persona && (
                          <Badge variant="info" size="sm">
                            {msg.persona}
                          </Badge>
                        )}
                        <span className={styles.messageTime}>
                          {msg.timestamp.toLocaleTimeString('pt-BR', {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                      <div className={styles.messageText}>
                        {msg.content}
                      </div>
                      {msg.role === 'assistant' && (
                        <div className={styles.messageActions}>
                          <button
                            onClick={() => copyMessage(msg.content)}
                            title="Copiar"
                          >
                            <Copy size={14} />
                          </button>
                          <button title="Baixar">
                            <Download size={14} />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              {loading && (
                <div className={`${styles.message} ${styles.assistant}`}>
                  <div className={styles.messageAvatar}>
                    <Bot size={20} />
                  </div>
                  <div className={styles.messageContent}>
                    <div className={styles.typing}>
                      <Loader2 size={16} className={styles.spinner} />
                      <span>Analisando...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className={styles.inputArea}>
              <Textarea
                placeholder="Digite sua pergunta sobre custos AWS..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                className={styles.textarea}
              />
              <Button
                variant="primary"
                icon={loading ? <Loader2 size={18} className={styles.spinner} /> : <Send size={18} />}
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className={styles.sendBtn}
              >
                Enviar
              </Button>
            </div>
          </Card>
        </main>
      </div>
    </div>
  );
}

export default AIConsultant;
