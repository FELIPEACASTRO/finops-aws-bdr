import { useState, useEffect } from 'react';
import {
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  Clock,
  DollarSign,
  ArrowUpRight,
  TrendingDown,
  Target,
  Zap,
  Shield,
  AlertCircle,
  Info,
  ExternalLink,
  Calculator,
  ListChecks,
  HelpCircle,
  BookOpen,
  Wrench,
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
  type: string;
  resource: string;
  whyItMatters: string;
  riskLevel: string;
  timeToImplement: string;
  affectedResources: string[];
  technicalDetails: string;
  businessImpact: string;
  prerequisites: string[];
  documentationLink: string;
  savingsBreakdown: {
    monthly: number;
    yearly: number;
    threeYear: number;
  };
}


const CATEGORY_INFO: Record<string, { icon: any; color: string; label: string }> = {
  compute: { icon: Zap, color: 'var(--color-primary-400)', label: 'Computação' },
  storage: { icon: Target, color: 'var(--color-warning-400)', label: 'Armazenamento' },
  network: { icon: ArrowUpRight, color: 'var(--color-info-400)', label: 'Rede' },
  security: { icon: Shield, color: 'var(--color-error-400)', label: 'Segurança' },
  optimization: { icon: TrendingDown, color: 'var(--color-success-400)', label: 'Otimização' },
};

const mapApiRecommendation = (rec: any, index: number): Recommendation => {
  const type = rec.type || 'GENERAL';
  const estimatedSavings = rec.savings || rec.estimated_savings || 0;
  
  const categoryMap: Record<string, string> = {
    'EC2_STOPPED': 'compute',
    'EBS_ORPHAN': 'storage',
    'EBS_OLD_SNAPSHOTS': 'storage',
    'EIP_UNUSED': 'network',
    'NAT_GATEWAY_COST': 'network',
    'LAMBDA_HIGH_MEMORY': 'compute',
    'S3_VERSIONING': 'storage',
    'S3_LIFECYCLE': 'storage',
  };

  const effortLevels: Array<'low' | 'medium' | 'high'> = ['low', 'medium', 'high'];
  
  return {
    id: rec.id || `rec-${index}`,
    title: rec.title || rec.description?.substring(0, 50) || 'Recomendação',
    description: rec.description || rec.recommendation || 'Sem descrição',
    category: rec.category || categoryMap[type] || 'optimization',
    priority: rec.priority || (rec.impact === 'high' ? 'high' : rec.impact === 'medium' ? 'medium' : 'low'),
    estimatedSavings,
    effort: rec.effort || effortLevels[index % 3],
    status: rec.status || 'pending',
    service: rec.service || 'AWS',
    impact: rec.impact || 'Redução de custos',
    type,
    resource: rec.resource || 'N/A',
    whyItMatters: rec.why_it_matters || rec.whyItMatters || 'Esta recomendação pode ajudar a reduzir custos.',
    riskLevel: rec.risk_level || rec.riskLevel || 'Baixo',
    timeToImplement: rec.time_to_implement || rec.timeToImplement || '15-30 minutos',
    affectedResources: rec.affected_resources || rec.affectedResources || (rec.resource ? [rec.resource] : []),
    technicalDetails: rec.technical_details || rec.technicalDetails || 'Consulte a documentação AWS.',
    businessImpact: rec.business_impact || rec.businessImpact || 'Potencial redução de custos.',
    prerequisites: rec.prerequisites || ['Revisar o recurso', 'Planejar implementação'],
    documentationLink: rec.documentation_link || rec.documentationLink || 'https://docs.aws.amazon.com/',
    savingsBreakdown: rec.savings_breakdown || {
      monthly: estimatedSavings,
      yearly: estimatedSavings * 12,
      threeYear: estimatedSavings * 36,
    },
    steps: rec.steps || [
      'Analisar o recurso identificado',
      'Criar backup se necessário',
      'Executar a ação recomendada',
      'Validar a mudança',
      'Monitorar impacto nos custos',
    ],
  };
};

export function Recommendations() {
  const { get, loading } = useFetch();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [filter, setFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  useEffect(() => {
    if (dataLoaded) return;
    
    const loadData = async () => {
      console.log('Carregando recomendações da API...');
      try {
        const response = await get<any>('/api/v1/reports/latest');
        if (response?.report?.details?.recommendations && response.report.details.recommendations.length > 0) {
          const recs: Recommendation[] = response.report.details.recommendations.map(mapApiRecommendation);
          console.log(`Recomendações carregadas: ${recs.length} da API`);
          setRecommendations(recs);
        } else {
          console.log('Nenhuma recomendação da API');
          setRecommendations([]);
        }
        setDataLoaded(true);
      } catch (err) {
        console.error('Erro ao carregar recomendações:', err);
        setRecommendations([]);
        setDataLoaded(true);
      } finally {
        setInitialLoading(false);
      }
    };
    loadData();
  }, [get, dataLoaded]);

  const fetchRecommendations = async () => {
    console.log('Atualizando recomendações...');
    const response = await get<any>('/api/v1/reports/latest');
    if (response?.report?.details?.recommendations && response.report.details.recommendations.length > 0) {
      const recs: Recommendation[] = response.report.details.recommendations.map(mapApiRecommendation);
      console.log(`Recomendações atualizadas: ${recs.length}`);
      setRecommendations(recs);
    } else {
      console.log('Nenhuma recomendação encontrada');
      setRecommendations([]);
    }
  };
  
  const isLoading = loading || initialLoading;

  const getPriorityInfo = (priority: string) => {
    switch (priority) {
      case 'high':
        return { color: 'error' as const, label: 'Alta Prioridade', icon: AlertTriangle, description: 'Ação imediata recomendada' };
      case 'medium':
        return { color: 'warning' as const, label: 'Média Prioridade', icon: AlertCircle, description: 'Avaliar em breve' };
      case 'low':
        return { color: 'info' as const, label: 'Baixa Prioridade', icon: Info, description: 'Pode ser planejado' };
      default:
        return { color: 'default' as const, label: 'Normal', icon: Info, description: '' };
    }
  };

  const getEffortInfo = (effort: string) => {
    switch (effort) {
      case 'low':
        return { label: 'Fácil', description: 'Menos de 30 minutos', color: 'var(--color-success-400)' };
      case 'medium':
        return { label: 'Moderado', description: '30 min - 2 horas', color: 'var(--color-warning-400)' };
      case 'high':
        return { label: 'Complexo', description: 'Mais de 2 horas', color: 'var(--color-error-400)' };
      default:
        return { label: 'Variável', description: 'Depende do contexto', color: 'var(--color-text-secondary)' };
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={18} />;
      case 'in_progress':
        return <Clock size={18} />;
      default:
        return <Lightbulb size={18} />;
    }
  };

  const getCategoryInfo = (category: string) => {
    return CATEGORY_INFO[category] || CATEGORY_INFO.optimization;
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
        title="Recomendações de Otimização"
        subtitle="Análise detalhada com ações práticas para reduzir custos AWS"
        onRefresh={fetchRecommendations}
        isLoading={isLoading}
      />

      <div className={styles.introCard}>
        <Card>
          <CardContent>
            <div className={styles.introContent}>
              <div className={styles.introIcon}>
                <HelpCircle size={24} />
              </div>
              <div className={styles.introText}>
                <h3>Como usar esta página?</h3>
                <p>
                  Cada recomendação foi identificada automaticamente pela análise da sua conta AWS. 
                  Clique em <strong>"Ver Detalhes"</strong> para entender o problema, o impacto financeiro 
                  e os passos exatos para implementar a otimização.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className={styles.summary}>
        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.summaryIcon} style={{ background: 'var(--color-success-500-alpha)' }}>
              <DollarSign size={24} color="var(--color-success-400)" />
            </div>
            <div className={styles.summaryInfo}>
              <span className={styles.summaryLabel}>Economia Potencial Mensal</span>
              <span className={styles.summaryValue}>${totalSavings.toFixed(2)}</span>
              <span className={styles.summarySubtext}>~${(totalSavings * 12).toFixed(0)}/ano</span>
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
              <span className={styles.summarySubtext}>oportunidades identificadas</span>
            </div>
          </CardContent>
        </Card>

        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.summaryIcon} style={{ background: 'var(--color-error-500-alpha)' }}>
              <AlertTriangle size={24} color="var(--color-error-400)" />
            </div>
            <div className={styles.summaryInfo}>
              <span className={styles.summaryLabel}>Ação Imediata</span>
              <span className={styles.summaryValue}>{highPriorityCount}</span>
              <span className={styles.summarySubtext}>recomendações prioritárias</span>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className={styles.filters}>
        <Select
          label="Filtrar por Status"
          value={filter}
          onChange={setFilter}
          options={[
            { value: 'all', label: 'Todos os Status' },
            { value: 'pending', label: 'Pendentes' },
            { value: 'in_progress', label: 'Em Progresso' },
            { value: 'completed', label: 'Concluídas' },
          ]}
        />
        <Select
          label="Filtrar por Prioridade"
          value={priorityFilter}
          onChange={setPriorityFilter}
          options={[
            { value: 'all', label: 'Todas as Prioridades' },
            { value: 'high', label: 'Alta - Ação Imediata' },
            { value: 'medium', label: 'Média - Avaliar em Breve' },
            { value: 'low', label: 'Baixa - Pode Planejar' },
          ]}
        />
      </div>

      <div className={styles.list}>
        {loading ? (
          [...Array(5)].map((_, i) => (
            <Card key={i}>
              <CardContent>
                <Skeleton height="120px" />
              </CardContent>
            </Card>
          ))
        ) : filteredRecommendations.length === 0 ? (
          <Card>
            <CardContent>
              <div className={styles.empty}>
                <Lightbulb size={48} />
                <h3>Nenhuma recomendação encontrada</h3>
                <p>Ajuste os filtros ou aguarde novas análises da sua conta AWS</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredRecommendations.map((rec) => {
            const priorityInfo = getPriorityInfo(rec.priority);
            const effortInfo = getEffortInfo(rec.effort);
            const categoryInfo = getCategoryInfo(rec.category);
            const CategoryIcon = categoryInfo.icon;

            return (
              <Card key={rec.id} className={styles.recCard}>
                <CardContent>
                  <div className={styles.recHeader}>
                    <div className={styles.recTitleArea}>
                      <div className={styles.recIcon} style={{ background: `${categoryInfo.color}20` }}>
                        <CategoryIcon size={20} color={categoryInfo.color} />
                      </div>
                      <div className={styles.recTitleContent}>
                        <div className={styles.recTitleRow}>
                          {getStatusIcon(rec.status)}
                          <h3>{rec.title}</h3>
                        </div>
                        <span className={styles.recCategory}>{categoryInfo.label} • {rec.service}</span>
                      </div>
                    </div>
                    <div className={styles.recBadges}>
                      <Badge variant={priorityInfo.color} size="sm">
                        <priorityInfo.icon size={12} />
                        {priorityInfo.label}
                      </Badge>
                    </div>
                  </div>

                  <p className={styles.recDescription}>{rec.description}</p>

                  <div className={styles.recHighlights}>
                    <div className={styles.recHighlight}>
                      <DollarSign size={18} color="var(--color-success-400)" />
                      <div className={styles.highlightContent}>
                        <span className={styles.highlightValue}>${rec.estimatedSavings.toFixed(2)}/mês</span>
                        <span className={styles.highlightLabel}>Economia Estimada</span>
                      </div>
                    </div>
                    <div className={styles.recHighlight}>
                      <Clock size={18} color={effortInfo.color} />
                      <div className={styles.highlightContent}>
                        <span className={styles.highlightValue}>{effortInfo.label}</span>
                        <span className={styles.highlightLabel}>{effortInfo.description}</span>
                      </div>
                    </div>
                    <div className={styles.recHighlight}>
                      <Target size={18} color="var(--color-primary-400)" />
                      <div className={styles.highlightContent}>
                        <span className={styles.highlightValue}>{rec.resource !== 'N/A' ? rec.resource.substring(0, 20) : 'Múltiplos'}</span>
                        <span className={styles.highlightLabel}>Recurso Afetado</span>
                      </div>
                    </div>
                  </div>

                  <div className={styles.recActions}>
                    <Button
                      variant="primary"
                      size="sm"
                      icon={<ArrowUpRight size={16} />}
                      onClick={() => openDetails(rec)}
                    >
                      Ver Detalhes Completos
                    </Button>
                    <Button variant="secondary" size="sm">
                      Marcar como Concluída
                    </Button>
                    <Button variant="ghost" size="sm">
                      Ignorar
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {selectedRec && (
        <Modal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          title=""
          size="xl"
          footer={
            <div className={styles.modalFooter}>
              <Button variant="secondary" onClick={() => setShowModal(false)}>
                Fechar
              </Button>
              <Button 
                variant="secondary" 
                icon={<ExternalLink size={16} />}
                onClick={() => window.open(selectedRec.documentationLink, '_blank')}
              >
                Ver Documentação AWS
              </Button>
              <Button variant="primary" icon={<CheckCircle size={16} />}>
                Marcar como Concluída
              </Button>
            </div>
          }
        >
          <div className={styles.modalContent}>
            <div className={styles.modalHeader}>
              <div className={styles.modalTitleArea}>
                <Badge variant={getPriorityInfo(selectedRec.priority).color} size="lg">
                  {getPriorityInfo(selectedRec.priority).label}
                </Badge>
                <h2 className={styles.modalTitle}>{selectedRec.title}</h2>
                <p className={styles.modalSubtitle}>{selectedRec.description}</p>
              </div>
            </div>

            <div className={styles.savingsBox}>
              <Calculator size={24} color="var(--color-success-400)" />
              <div className={styles.savingsContent}>
                <h3>Impacto Financeiro Estimado</h3>
                <div className={styles.savingsGrid}>
                  <div className={styles.savingsItem}>
                    <span className={styles.savingsAmount}>${selectedRec.savingsBreakdown.monthly.toFixed(2)}</span>
                    <span className={styles.savingsPeriod}>por mês</span>
                  </div>
                  <div className={styles.savingsItem}>
                    <span className={styles.savingsAmount}>${selectedRec.savingsBreakdown.yearly.toFixed(2)}</span>
                    <span className={styles.savingsPeriod}>por ano</span>
                  </div>
                  <div className={styles.savingsItem}>
                    <span className={styles.savingsAmount}>${selectedRec.savingsBreakdown.threeYear.toFixed(2)}</span>
                    <span className={styles.savingsPeriod}>em 3 anos</span>
                  </div>
                </div>
              </div>
            </div>

            <div className={styles.sectionGrid}>
              <div className={styles.section}>
                <div className={styles.sectionHeader}>
                  <HelpCircle size={20} color="var(--color-primary-400)" />
                  <h4>Por que isso é importante?</h4>
                </div>
                <p className={styles.sectionText}>{selectedRec.whyItMatters}</p>
              </div>

              <div className={styles.section}>
                <div className={styles.sectionHeader}>
                  <TrendingDown size={20} color="var(--color-success-400)" />
                  <h4>Impacto no Negócio</h4>
                </div>
                <p className={styles.sectionText}>{selectedRec.businessImpact}</p>
              </div>
            </div>

            <div className={styles.infoCards}>
              <div className={styles.infoCard}>
                <Clock size={20} color="var(--color-warning-400)" />
                <div>
                  <strong>Tempo Estimado</strong>
                  <span>{selectedRec.timeToImplement}</span>
                </div>
              </div>
              <div className={styles.infoCard}>
                <Shield size={20} color="var(--color-info-400)" />
                <div>
                  <strong>Nível de Risco</strong>
                  <span>{selectedRec.riskLevel}</span>
                </div>
              </div>
              <div className={styles.infoCard}>
                <Target size={20} color="var(--color-primary-400)" />
                <div>
                  <strong>Recurso Afetado</strong>
                  <span>{selectedRec.resource}</span>
                </div>
              </div>
            </div>

            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <BookOpen size={20} color="var(--color-text-secondary)" />
                <h4>Detalhes Técnicos</h4>
              </div>
              <div className={styles.technicalBox}>
                <p>{selectedRec.technicalDetails}</p>
              </div>
            </div>

            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <AlertCircle size={20} color="var(--color-warning-400)" />
                <h4>Antes de Começar (Pré-requisitos)</h4>
              </div>
              <ul className={styles.prerequisitesList}>
                {selectedRec.prerequisites.map((prereq, i) => (
                  <li key={i}>
                    <CheckCircle size={16} color="var(--color-success-400)" />
                    <span>{prereq}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className={styles.section}>
              <div className={styles.sectionHeader}>
                <ListChecks size={20} color="var(--color-success-400)" />
                <h4>Passos para Implementação</h4>
              </div>
              <div className={styles.stepsContainer}>
                {selectedRec.steps.map((step, i) => (
                  <div key={i} className={styles.step}>
                    <div className={styles.stepNumber}>{i + 1}</div>
                    <div className={styles.stepContent}>
                      <p>{step}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className={styles.helpBox}>
              <Wrench size={20} color="var(--color-primary-400)" />
              <div>
                <strong>Precisa de ajuda?</strong>
                <p>Use o Consultor IA na aba "AI Consultant" para tirar dúvidas específicas sobre esta recomendação ou pedir instruções detalhadas passo a passo.</p>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

export default Recommendations;
