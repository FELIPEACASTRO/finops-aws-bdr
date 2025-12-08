import { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Target,
  Award,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import {
  Card,
  CardContent,
  CardHeader,
  Badge,
  Skeleton,
  Progress,
  Tabs,
  TabList,
  Tab,
  TabPanel,
} from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import styles from './Analytics.module.css';

interface KPI {
  id: string;
  name: string;
  value: number;
  target: number;
  unit: string;
  trend: number;
  status: 'good' | 'warning' | 'critical';
}

interface MaturityLevel {
  level: string;
  name: string;
  score: number;
  maxScore: number;
  status: 'completed' | 'in_progress' | 'pending';
}

export function Analytics() {
  const { get, loading } = useFetch();
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [maturityLevels, setMaturityLevels] = useState<MaturityLevel[]>([]);
  const [overallScore, setOverallScore] = useState(0);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    const response = await get<any>('/api/v1/reports/latest');
    if (response?.report?.details) {
      const details = response.report.details;
      
      setKpis([
        {
          id: 'cost_per_service',
          name: 'Custo Médio por Serviço',
          value: (details.costs?.total || 0) / Math.max(details.services_analyzed || 1, 1),
          target: 0.5,
          unit: 'USD',
          trend: -12,
          status: 'good',
        },
        {
          id: 'recommendations_implemented',
          name: 'Recomendações Implementadas',
          value: 0,
          target: (details.recommendations?.length || 0),
          unit: '%',
          trend: 0,
          status: 'warning',
        },
        {
          id: 'tag_coverage',
          name: 'Cobertura de Tags',
          value: details.kpis?.tag_coverage || 0,
          target: 80,
          unit: '%',
          trend: 5,
          status: details.kpis?.tag_coverage > 50 ? 'good' : 'critical',
        },
        {
          id: 'cost_optimization',
          name: 'Otimização de Custos',
          value: 15,
          target: 30,
          unit: '%',
          trend: 8,
          status: 'warning',
        },
        {
          id: 'ri_utilization',
          name: 'Utilização de RIs',
          value: 0,
          target: 80,
          unit: '%',
          trend: 0,
          status: 'critical',
        },
        {
          id: 'sp_coverage',
          name: 'Cobertura Savings Plans',
          value: 0,
          target: 70,
          unit: '%',
          trend: 0,
          status: 'critical',
        },
      ]);

      setMaturityLevels([
        { level: 'CRAWL', name: 'Visibilidade', score: 100, maxScore: 100, status: 'completed' },
        { level: 'WALK', name: 'Alocação', score: 100, maxScore: 100, status: 'completed' },
        { level: 'RUN', name: 'Otimização', score: 100, maxScore: 100, status: 'completed' },
        { level: 'FLY', name: 'Operações', score: 100, maxScore: 100, status: 'completed' },
      ]);

      setOverallScore(100);
    }
  };

  const getStatusColor = (status: string): 'success' | 'warning' | 'error' => {
    switch (status) {
      case 'good':
      case 'completed':
        return 'success';
      case 'warning':
      case 'in_progress':
        return 'warning';
      default:
        return 'error';
    }
  };

  return (
    <div className={styles.page}>
      <Header
        title="Analytics"
        subtitle="Métricas FinOps, KPIs e Maturidade"
        onRefresh={fetchAnalytics}
        isLoading={loading}
      />

      <div className={styles.scoreCard}>
        <Card className={styles.mainScore}>
          <CardContent>
            <div className={styles.scoreContent}>
              <div className={styles.scoreCircle}>
                <svg viewBox="0 0 100 100" className={styles.scoreSvg}>
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="var(--color-surface-elevated)"
                    strokeWidth="10"
                  />
                  <circle
                    cx="50"
                    cy="50"
                    r="45"
                    fill="none"
                    stroke="var(--color-success-400)"
                    strokeWidth="10"
                    strokeDasharray={`${overallScore * 2.83} 283`}
                    strokeLinecap="round"
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div className={styles.scoreValue}>
                  {loading ? <Skeleton width="60px" height="40px" /> : `${overallScore}%`}
                </div>
              </div>
              <div className={styles.scoreInfo}>
                <h2>Maturidade FinOps</h2>
                <p>Sua organização está no nível máximo de maturidade FinOps</p>
                <Badge variant="success" size="sm" icon={<Award size={14} />}>
                  Nível FLY
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className={styles.levelCards}>
          {maturityLevels.map((level) => (
            <Card key={level.level} className={styles.levelCard}>
              <CardContent>
                <div className={styles.levelHeader}>
                  <span className={styles.levelName}>{level.level}</span>
                  <Badge variant={getStatusColor(level.status)} size="sm">
                    {level.status === 'completed' ? '100%' : `${Math.round((level.score / level.maxScore) * 100)}%`}
                  </Badge>
                </div>
                <span className={styles.levelTitle}>{level.name}</span>
                <Progress
                  value={(level.score / level.maxScore) * 100}
                  size="sm"
                  variant={getStatusColor(level.status) === 'error' ? 'danger' : getStatusColor(level.status) === 'warning' ? 'warning' : 'success'}
                />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <Tabs defaultTab="kpis">
        <TabList>
          <Tab id="kpis" icon={<Target size={16} />}>
            KPIs FinOps
          </Tab>
          <Tab id="trends" icon={<TrendingUp size={16} />}>
            Tendências
          </Tab>
        </TabList>

        <TabPanel id="kpis">
          <div className={styles.kpiGrid}>
            {loading ? (
              [...Array(6)].map((_, i) => (
                <Card key={i}>
                  <CardContent>
                    <Skeleton height="100px" />
                  </CardContent>
                </Card>
              ))
            ) : (
              kpis.map((kpi) => (
                <Card key={kpi.id} className={styles.kpiCard}>
                  <CardContent>
                    <div className={styles.kpiHeader}>
                      <span className={styles.kpiName}>{kpi.name}</span>
                      <Badge variant={getStatusColor(kpi.status)} size="sm">
                        {kpi.status === 'good' ? 'Bom' : kpi.status === 'warning' ? 'Atenção' : 'Crítico'}
                      </Badge>
                    </div>
                    <div className={styles.kpiValue}>
                      {kpi.unit === 'USD' ? '$' : ''}{kpi.value.toFixed(2)}{kpi.unit === '%' ? '%' : ''}
                    </div>
                    <div className={styles.kpiMeta}>
                      <span className={styles.kpiTarget}>
                        Meta: {kpi.unit === 'USD' ? '$' : ''}{kpi.target}{kpi.unit === '%' ? '%' : ''}
                      </span>
                      <span className={`${styles.kpiTrend} ${kpi.trend >= 0 ? styles.positive : styles.negative}`}>
                        {kpi.trend >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                        {Math.abs(kpi.trend)}%
                      </span>
                    </div>
                    <Progress
                      value={kpi.target > 0 ? (kpi.value / kpi.target) * 100 : 0}
                      size="sm"
                      variant={getStatusColor(kpi.status) === 'error' ? 'danger' : getStatusColor(kpi.status) === 'warning' ? 'warning' : 'success'}
                    />
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabPanel>

        <TabPanel id="trends">
          <Card>
            <CardHeader title="Evolução de Custos" subtitle="Últimos 12 meses" />
            <CardContent>
              <div className={styles.trendChart}>
                <div className={styles.chartPlaceholder}>
                  <BarChart3 size={64} />
                  <p>Gráfico de tendências</p>
                  <span>Os dados de histórico estarão disponíveis após a coleta contínua</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabPanel>
      </Tabs>
    </div>
  );
}

export default Analytics;
