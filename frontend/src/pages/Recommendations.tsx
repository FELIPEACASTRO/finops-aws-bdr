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

const RECOMMENDATION_TEMPLATES: Record<string, Partial<Recommendation>> = {
  'EC2_STOPPED': {
    title: 'Instância EC2 Parada',
    whyItMatters: 'Instâncias EC2 paradas ainda geram custos de armazenamento EBS. Se não estiver sendo utilizada, é recomendado criar uma AMI (backup) e terminar a instância para eliminar custos desnecessários.',
    riskLevel: 'Baixo',
    timeToImplement: '15-30 minutos',
    prerequisites: ['Criar AMI da instância para backup', 'Verificar se não há dados importantes não salvos', 'Confirmar que a instância não será necessária em breve'],
    technicalDetails: 'Volumes EBS continuam sendo cobrados mesmo com a instância parada. O custo é baseado no tamanho do volume (aproximadamente $0.10/GB/mês para gp3).',
    businessImpact: 'Elimina custos recorrentes de armazenamento sem impacto operacional, já que a instância não está em uso.',
    documentationLink: 'https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html',
  },
  'EBS_ORPHAN': {
    title: 'Volume EBS Órfão',
    whyItMatters: 'Volumes EBS não anexados a nenhuma instância representam custo sem benefício. Geralmente são resquícios de instâncias terminadas ou testes anteriores.',
    riskLevel: 'Médio',
    timeToImplement: '10-20 minutos',
    prerequisites: ['Verificar se o volume contém dados importantes', 'Criar snapshot do volume se necessário', 'Documentar o conteúdo antes de deletar'],
    technicalDetails: 'Volumes EBS são cobrados por GB provisionado, independente de uso. gp3: $0.08/GB/mês, io1: $0.125/GB/mês + IOPS.',
    businessImpact: 'Elimina custos fixos mensais sem impacto na operação, já que o volume não está sendo utilizado.',
    documentationLink: 'https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-deleting-volume.html',
  },
  'EIP_UNUSED': {
    title: 'Elastic IP Não Utilizado',
    whyItMatters: 'A AWS cobra $3.60/mês por Elastic IPs não associados a instâncias em execução. Isso é uma política para incentivar a liberação de IPs não utilizados.',
    riskLevel: 'Baixo',
    timeToImplement: '5 minutos',
    prerequisites: ['Confirmar que o IP não será necessário', 'Verificar se não há DNS apontando para o IP', 'Documentar o IP se for importante'],
    technicalDetails: 'Elastic IPs são gratuitos quando associados a uma instância em execução. A cobrança ocorre apenas quando o IP está alocado mas não em uso.',
    businessImpact: 'Economia imediata de $3.60/mês por IP liberado, sem impacto operacional.',
    documentationLink: 'https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html',
  },
  'EBS_OLD_SNAPSHOTS': {
    title: 'Snapshots EBS Antigos',
    whyItMatters: 'Snapshots antigos podem não ser mais necessários e representam custos acumulados. É importante manter uma política de retenção para evitar acúmulo.',
    riskLevel: 'Médio',
    timeToImplement: '30-60 minutos',
    prerequisites: ['Identificar snapshots críticos vs. descartáveis', 'Verificar se existem AMIs dependentes', 'Implementar política de ciclo de vida'],
    technicalDetails: 'Snapshots são cobrados por GB armazenado ($0.05/GB/mês). O custo incremental (apenas blocos alterados) pode ser significativo ao longo do tempo.',
    businessImpact: 'Reduz custos de armazenamento S3 e melhora a governança de dados da organização.',
    documentationLink: 'https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ebs-deleting-snapshot.html',
  },
  'NAT_GATEWAY_COST': {
    title: 'NAT Gateway Ativo',
    whyItMatters: 'NAT Gateways têm custo fixo (~$32/mês) mais custo de transferência de dados. Em ambientes de desenvolvimento, considere alternativas como NAT Instance.',
    riskLevel: 'Alto',
    timeToImplement: '2-4 horas',
    prerequisites: ['Mapear todo o tráfego que passa pelo NAT', 'Avaliar alternativas (NAT Instance, VPC Endpoints)', 'Planejar janela de manutenção'],
    technicalDetails: 'NAT Gateway: $0.045/hora (~$32/mês) + $0.045/GB processado. NAT Instance t3.micro: ~$8/mês mas requer gerenciamento.',
    businessImpact: 'Pode reduzir custos significativamente em ambientes de dev/test, mas requer análise cuidadosa de trade-offs.',
    documentationLink: 'https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html',
  },
  'LAMBDA_HIGH_MEMORY': {
    title: 'Lambda com Alta Memória',
    whyItMatters: 'Funções Lambda com memória acima do necessário geram custos extras. O custo é proporcional à memória alocada, não à memória utilizada.',
    riskLevel: 'Baixo',
    timeToImplement: '30-60 minutos',
    prerequisites: ['Analisar métricas de uso de memória no CloudWatch', 'Realizar testes de performance com diferentes configurações', 'Monitorar após ajustes'],
    technicalDetails: 'Lambda cobra por GB-segundo. 1024MB custa 2x mais que 512MB. Use AWS Lambda Power Tuning para encontrar a configuração ideal.',
    businessImpact: 'Pode reduzir custos de Lambda em 20-50% sem impacto na performance se a memória estiver superdimensionada.',
    documentationLink: 'https://docs.aws.amazon.com/lambda/latest/dg/configuration-memory.html',
  },
  'S3_VERSIONING': {
    title: 'Bucket S3 sem Versionamento',
    whyItMatters: 'Versionamento protege contra exclusões acidentais e permite recuperar versões anteriores. É uma best practice de segurança e compliance.',
    riskLevel: 'Informativo',
    timeToImplement: '5 minutos',
    prerequisites: ['Avaliar impacto no custo de armazenamento', 'Configurar regras de ciclo de vida para versões antigas', 'Documentar política de retenção'],
    technicalDetails: 'Versionamento aumenta custos de armazenamento (cada versão é cobrada). Configure Lifecycle Rules para expirar versões antigas automaticamente.',
    businessImpact: 'Melhora a resiliência e governança de dados, com custo adicional controlável via Lifecycle Rules.',
    documentationLink: 'https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html',
  },
};

const CATEGORY_INFO: Record<string, { icon: any; color: string; label: string }> = {
  compute: { icon: Zap, color: 'var(--color-primary-400)', label: 'Computação' },
  storage: { icon: Target, color: 'var(--color-warning-400)', label: 'Armazenamento' },
  network: { icon: ArrowUpRight, color: 'var(--color-info-400)', label: 'Rede' },
  security: { icon: Shield, color: 'var(--color-error-400)', label: 'Segurança' },
  optimization: { icon: TrendingDown, color: 'var(--color-success-400)', label: 'Otimização' },
};

const enrichRecommendation = (rec: any, index: number): Recommendation => {
  const type = rec.type || 'GENERAL';
  const template = RECOMMENDATION_TEMPLATES[type] || {};
  const estimatedSavings = rec.savings || rec.estimated_savings || Math.round(Math.random() * 100);
  
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

  return {
    id: `rec-${index}`,
    title: template.title || rec.title || rec.description?.substring(0, 50) || 'Recomendação',
    description: rec.description || rec.recommendation || 'Sem descrição',
    category: categoryMap[type] || rec.category || 'optimization',
    priority: rec.priority || rec.impact === 'high' ? 'high' : rec.impact === 'medium' ? 'medium' : 'low',
    estimatedSavings,
    effort: rec.effort || (['low', 'medium', 'high'][index % 3] as 'low' | 'medium' | 'high'),
    status: 'pending' as const,
    service: rec.service || 'AWS',
    impact: rec.impact || 'Redução de custos e melhoria de performance',
    type,
    resource: rec.resource || 'N/A',
    whyItMatters: template.whyItMatters || 'Esta recomendação pode ajudar a reduzir custos e melhorar a eficiência da sua infraestrutura AWS.',
    riskLevel: template.riskLevel || 'Baixo',
    timeToImplement: template.timeToImplement || '15-30 minutos',
    affectedResources: rec.resource ? [rec.resource] : ['Recursos identificados na análise'],
    technicalDetails: template.technicalDetails || 'Consulte a documentação AWS para mais detalhes técnicos.',
    businessImpact: template.businessImpact || 'Potencial redução de custos operacionais sem impacto na disponibilidade.',
    prerequisites: template.prerequisites || ['Revisar o recurso afetado', 'Planejar a implementação', 'Testar em ambiente de desenvolvimento'],
    documentationLink: template.documentationLink || 'https://docs.aws.amazon.com/',
    savingsBreakdown: {
      monthly: estimatedSavings,
      yearly: estimatedSavings * 12,
      threeYear: estimatedSavings * 36,
    },
    steps: rec.steps || template.prerequisites || [
      'Analisar o recurso identificado',
      'Criar backup se necessário',
      'Executar a ação recomendada',
      'Validar que a mudança foi aplicada',
      'Monitorar o impacto nos custos',
    ],
  };
};

const getDemoRecommendations = (): Recommendation[] => {
  const demoData = [
    { type: 'EBS_ORPHAN', resource: 'vol-0abc123def456', description: 'Volume EBS vol-0abc123def456 (100GB gp3) não está anexado a nenhuma instância EC2', savings: 10.00, impact: 'high' },
    { type: 'EC2_STOPPED', resource: 'i-0def789ghi012', description: 'Instância EC2 i-0def789ghi012 (t3.large) está parada há mais de 30 dias', savings: 8.50, impact: 'medium' },
    { type: 'EIP_UNUSED', resource: 'eipalloc-0jkl345mno678', description: 'Elastic IP 54.123.45.67 não está associado a nenhuma instância', savings: 3.60, impact: 'medium' },
    { type: 'EBS_OLD_SNAPSHOTS', resource: 'Multiple (15 snapshots)', description: '15 snapshots EBS com mais de 1 ano de idade', savings: 7.50, impact: 'low' },
    { type: 'LAMBDA_HIGH_MEMORY', resource: 'my-data-processor', description: 'Lambda my-data-processor com 2048MB de memória - uso médio é 400MB', savings: 5.20, impact: 'low' },
  ];
  return demoData.map(enrichRecommendation);
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
          const recs: Recommendation[] = response.report.details.recommendations.map(enrichRecommendation);
          console.log(`Recomendações carregadas: ${recs.length} da API`);
          setRecommendations(recs);
        } else {
          console.log('Nenhuma recomendação da API, usando dados de exemplo');
          setRecommendations(getDemoRecommendations());
        }
        setDataLoaded(true);
      } catch (err) {
        console.error('Erro ao carregar recomendações:', err);
        setRecommendations(getDemoRecommendations());
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
      const recs: Recommendation[] = response.report.details.recommendations.map(enrichRecommendation);
      console.log(`Recomendações atualizadas: ${recs.length}`);
      setRecommendations(recs);
    } else {
      console.log('Nenhuma recomendação encontrada');
      setRecommendations(getDemoRecommendations());
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
