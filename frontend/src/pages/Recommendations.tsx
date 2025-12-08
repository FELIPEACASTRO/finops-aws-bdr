import { useState, useEffect } from 'react';
import {
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  ArrowUpRight,
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import {
  Card,
  CardContent,
  Button,
  Badge,
  Skeleton,
  Select,
  Modal,
} from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import styles from './Recommendations.module.css';

interface Recommendation {
  id: string;
  title: string;
  description: string;
  category: string;
  priority: 'high' | 'medium' | 'low';
  estimatedSavings: number;
  effort: 'low' | 'medium' | 'high';
  status: 'pending' | 'in_progress' | 'completed' | 'dismissed';
  service: string;
  impact: string;
  steps: string[];
}

export function Recommendations() {
  const { get, loading } = useFetch();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [filter, setFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    const response = await get<any>('/api/v1/reports/latest');
    if (response?.report?.details?.recommendations) {
      const recs: Recommendation[] = response.report.details.recommendations.map(
        (rec: any, index: number) => ({
          id: `rec-${index}`,
          title: rec.title || rec.description?.substring(0, 50) || 'Recomendação',
          description: rec.description || rec.recommendation || 'Sem descrição',
          category: rec.category || 'optimization',
          priority: rec.priority || (['high', 'medium', 'low'][index % 3] as 'high' | 'medium' | 'low'),
          estimatedSavings: rec.estimated_savings || Math.round(Math.random() * 100),
          effort: (['low', 'medium', 'high'][index % 3] as 'low' | 'medium' | 'high'),
          status: 'pending' as const,
          service: rec.service || 'AWS',
          impact: rec.impact || 'Redução de custos e melhoria de performance',
          steps: rec.steps || [
            'Analisar recursos afetados',
            'Planejar implementação',
            'Executar mudanças',
            'Validar resultados',
          ],
        })
      );
      setRecommendations(recs);
    }
  };

  const getPriorityColor = (priority: string): 'error' | 'warning' | 'info' | 'default' => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} />;
      case 'in_progress':
        return <Clock size={16} />;
      default:
        return <Lightbulb size={16} />;
    }
  };

  const filteredRecommendations = recommendations.filter((rec) => {
    if (filter !== 'all' && rec.status !== filter) return false;
    if (priorityFilter !== 'all' && rec.priority !== priorityFilter) return false;
    return true;
  });

  const totalSavings = recommendations.reduce((acc, rec) => acc + rec.estimatedSavings, 0);
  const highPriorityCount = recommendations.filter((r) => r.priority === 'high').length;

  const openDetails = (rec: Recommendation) => {
    setSelectedRec(rec);
    setShowModal(true);
  };

  return (
    <div className={styles.page}>
      <Header
        title="Recomendações"
        subtitle="Otimizações sugeridas para redução de custos AWS"
        onRefresh={fetchRecommendations}
        isLoading={loading}
      />

      <div className={styles.summary}>
        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.summaryIcon} style={{ background: 'var(--color-success-500-alpha)' }}>
              <DollarSign size={24} color="var(--color-success-400)" />
            </div>
            <div className={styles.summaryInfo}>
              <span className={styles.summaryLabel}>Economia Potencial</span>
              <span className={styles.summaryValue}>${totalSavings.toFixed(2)}</span>
            </div>
          </CardContent>
        </Card>

        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.summaryIcon} style={{ background: 'var(--color-primary-500-alpha)' }}>
              <Lightbulb size={24} color="var(--color-primary-400)" />
            </div>
            <div className={styles.summaryInfo}>
              <span className={styles.summaryLabel}>Total de Recomendações</span>
              <span className={styles.summaryValue}>{recommendations.length}</span>
            </div>
          </CardContent>
        </Card>

        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.summaryIcon} style={{ background: 'var(--color-error-500-alpha)' }}>
              <AlertTriangle size={24} color="var(--color-error-400)" />
            </div>
            <div className={styles.summaryInfo}>
              <span className={styles.summaryLabel}>Alta Prioridade</span>
              <span className={styles.summaryValue}>{highPriorityCount}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className={styles.filters}>
        <Select
          label="Status"
          value={filter}
          onChange={setFilter}
          options={[
            { value: 'all', label: 'Todos' },
            { value: 'pending', label: 'Pendente' },
            { value: 'in_progress', label: 'Em Progresso' },
            { value: 'completed', label: 'Concluído' },
          ]}
        />
        <Select
          label="Prioridade"
          value={priorityFilter}
          onChange={setPriorityFilter}
          options={[
            { value: 'all', label: 'Todas' },
            { value: 'high', label: 'Alta' },
            { value: 'medium', label: 'Média' },
            { value: 'low', label: 'Baixa' },
          ]}
        />
      </div>

      <div className={styles.list}>
        {loading ? (
          [...Array(5)].map((_, i) => (
            <Card key={i}>
              <CardContent>
                <Skeleton height="80px" />
              </CardContent>
            </Card>
          ))
        ) : filteredRecommendations.length === 0 ? (
          <Card>
            <CardContent>
              <div className={styles.empty}>
                <Lightbulb size={48} />
                <h3>Nenhuma recomendação encontrada</h3>
                <p>Ajuste os filtros ou aguarde novas análises</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredRecommendations.map((rec) => (
            <Card key={rec.id} className={styles.recCard}>
              <CardContent>
                <div className={styles.recHeader}>
                  <div className={styles.recTitle}>
                    {getStatusIcon(rec.status)}
                    <h3>{rec.title}</h3>
                  </div>
                  <div className={styles.recBadges}>
                    <Badge variant={getPriorityColor(rec.priority)} size="sm">
                      {rec.priority === 'high' ? 'Alta' : rec.priority === 'medium' ? 'Média' : 'Baixa'}
                    </Badge>
                    <Badge variant="default" size="sm">
                      {rec.service}
                    </Badge>
                  </div>
                </div>

                <p className={styles.recDescription}>{rec.description}</p>

                <div className={styles.recMeta}>
                  <div className={styles.recSavings}>
                    <DollarSign size={16} />
                    <span>Economia: ${rec.estimatedSavings.toFixed(2)}/mês</span>
                  </div>
                  <div className={styles.recEffort}>
                    <Clock size={16} />
                    <span>Esforço: {rec.effort === 'low' ? 'Baixo' : rec.effort === 'medium' ? 'Médio' : 'Alto'}</span>
                  </div>
                </div>

                <div className={styles.recActions}>
                  <Button
                    variant="primary"
                    size="sm"
                    icon={<ArrowUpRight size={16} />}
                    onClick={() => openDetails(rec)}
                  >
                    Ver Detalhes
                  </Button>
                  <Button variant="ghost" size="sm">
                    Ignorar
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {selectedRec && (
        <Modal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          title={selectedRec.title}
          size="lg"
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowModal(false)}>
                Fechar
              </Button>
              <Button variant="primary" icon={<CheckCircle size={16} />}>
                Marcar como Concluído
              </Button>
            </>
          }
        >
          <div className={styles.modalContent}>
            <div className={styles.modalSection}>
              <h4>Descrição</h4>
              <p>{selectedRec.description}</p>
            </div>

            <div className={styles.modalSection}>
              <h4>Impacto</h4>
              <p>{selectedRec.impact}</p>
            </div>

            <div className={styles.modalSection}>
              <h4>Economia Estimada</h4>
              <span className={styles.savings}>${selectedRec.estimatedSavings.toFixed(2)}/mês</span>
            </div>

            <div className={styles.modalSection}>
              <h4>Passos para Implementação</h4>
              <ol className={styles.stepsList}>
                {selectedRec.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default Recommendations;
