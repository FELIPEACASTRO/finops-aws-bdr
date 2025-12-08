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

interface TrendData {
  period: string;
  label: string;
  value: number;
}

export function Analytics() {
  const { get } = useFetch();
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [maturityLevels, setMaturityLevels] = useState<MaturityLevel[]>([]);
  const [overallScore, setOverallScore] = useState(0);
  const [maturityLevel, setMaturityLevel] = useState('CRAWL');
  const [trendData, setTrendData] = useState<TrendData[]>([]);
  const [trendLoading, setTrendLoading] = useState(false);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  useEffect(() => {
    if (dataLoaded) return;
    
    const loadData = async () => {
      await Promise.all([
        fetchAnalytics(),
        fetchTrendData(),
      ]);
      setDataLoaded(true);
    };
    loadData();
  }, [dataLoaded]);

  const fetchTrendData = async () => {
    setTrendLoading(true);
    console.log('Buscando dados de tendência...');
    try {
      const periods = [
        { period: '7d', label: '7 dias' },
        { period: '30d', label: '30 dias' },
        { period: '90d', label: '90 dias' },
        { period: '1y', label: '1 ano' },
      ];
      
      const results: TrendData[] = [];
      for (const p of periods) {
        const response = await get<any>(`/api/v1/costs?period=${p.period}&category=all`);
        if (response?.status === 'success' && response?.data) {
          results.push({
            period: p.period,
            label: p.label,
            value: response.data.total || 0,
          });
        }
      }
      
      console.log('Tendências carregadas:', results);
      setTrendData(results);
    } catch (err) {
      console.error('Erro ao carregar tendências:', err);
    } finally {
      setTrendLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    console.log('Buscando analytics do endpoint real...');
    try {
    const response = await get<any>('/api/v1/analytics');
    
    if (response?.status === 'success' && response?.data) {
      const { maturity, kpis: kpiData, trends } = response.data;
      console.log('Analytics recebido:', { maturity, kpis: kpiData });
      
      const getKpiStatus = (value: number, target: number, higherIsBetter: boolean = true): 'good' | 'warning' | 'critical' => {
        const ratio = value / Math.max(target, 1);
        if (higherIsBetter) {
          if (ratio >= 0.8) return 'good';
          if (ratio >= 0.5) return 'warning';
          return 'critical';
        } else {
          if (ratio <= 1.2) return 'good';
          if (ratio <= 1.5) return 'warning';
          return 'critical';
        }
      };

      setKpis([
        {
          id: 'cost_per_service',
          name: 'Custo Médio por Serviço',
          value: kpiData.avg_cost_per_service || 0,
          target: 0.5,
          unit: 'USD',
          trend: trends.cost_trend || 0,
          status: getKpiStatus(kpiData.avg_cost_per_service || 0, 0.5, false),
        },
        {
          id: 'recommendations_implemented',
          name: 'Recomendações Implementadas',
          value: kpiData.implementation_rate || 0,
          target: kpiData.recommendations_total || 11,
          unit: '%',
          trend: 0,
          status: getKpiStatus(kpiData.implementation_rate || 0, 50),
        },
        {
          id: 'tag_coverage',
          name: 'Cobertura de Tags',
          value: kpiData.tag_coverage || 0,
          target: 80,
          unit: '%',
          trend: 5,
          status: getKpiStatus(kpiData.tag_coverage || 0, 80),
        },
        {
          id: 'cost_optimization',
          name: 'Otimização de Custos',
          value: kpiData.cost_optimization_rate || 0,
          target: 30,
          unit: '%',
          trend: 8,
          status: getKpiStatus(kpiData.cost_optimization_rate || 0, 30),
        },
        {
          id: 'ri_utilization',
          name: 'Utilização de RIs',
          value: kpiData.ri_utilization || 0,
          target: 80,
          unit: '%',
          trend: 0,
          status: getKpiStatus(kpiData.ri_utilization || 0, 80),
        },
        {
          id: 'sp_coverage',
          name: 'Cobertura Savings Plans',
          value: kpiData.sp_coverage || 0,
          target: 70,
          unit: '%',
          trend: 0,
          status: getKpiStatus(kpiData.sp_coverage || 0, 70),
        },
      ]);

      const getMaturityStatus = (score: number): 'completed' | 'in_progress' | 'pending' => {
        if (score >= 80) return 'completed';
        if (score >= 30) return 'in_progress';
        return 'pending';
      };

      setMaturityLevels([
        { 
          level: 'Nível 1', 
          name: 'Visibilidade de Custos', 
          score: maturity.crawl || 0, 
          maxScore: 100, 
          status: getMaturityStatus(maturity.crawl || 0)
        },
        { 
          level: 'Nível 2', 
          name: 'Alocação e Controle', 
          score: maturity.walk || 0, 
          maxScore: 100, 
          status: getMaturityStatus(maturity.walk || 0)
        },
        { 
          level: 'Nível 3', 
          name: 'Otimização Ativa', 
          score: maturity.run || 0, 
          maxScore: 100, 
          status: getMaturityStatus(maturity.run || 0)
        },
        { 
          level: 'Nível 4', 
          name: 'Excelência Operacional', 
          score: maturity.fly || 0, 
          maxScore: 100, 
          status: getMaturityStatus(maturity.fly || 0)
        },
      ]);

      setOverallScore(Math.round(maturity.overall_score || 0));
      setMaturityLevel(maturity.level || 'CRAWL');
    }
    } catch (err) {
      console.error('Erro ao carregar analytics:', err);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const isLoading = analyticsLoading || trendLoading;

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

  const getMaturityLevelName = () => {
    switch (maturityLevel) {
      case 'FLY':
        return 'Excelência';
      case 'RUN':
        return 'Avançado';
      case 'WALK':
        return 'Intermediário';
      default:
        return 'Iniciante';
    }
  };

  const getMaturityDescription = () => {
    switch (maturityLevel) {
      case 'FLY':
        return 'Excelência operacional: automação completa, decisões estratégicas baseadas em dados e cultura FinOps estabelecida';
      case 'RUN':
        return 'Otimização ativa: processos automatizados, redução contínua de custos e práticas FinOps consolidadas';
      case 'WALK':
        return 'Controle financeiro: alocação de custos por equipe/projeto, alertas de orçamento e relatórios estruturados';
      default:
        return 'Primeiros passos: construindo visibilidade dos custos na nuvem e identificando oportunidades de economia';
    }
  };

  return (
    <div className={styles.page}>
      <Header
        title="Analytics"
        subtitle="Métricas FinOps, KPIs e Maturidade"
        onRefresh={() => { setDataLoaded(false); }}
        isLoading={isLoading}
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
                    stroke={overallScore >= 60 ? "var(--color-success-400)" : overallScore >= 30 ? "var(--color-warning-400)" : "var(--color-error-400)"}
                    strokeWidth="10"
                    strokeDasharray={`${overallScore * 2.83} 283`}
                    strokeLinecap="round"
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div className={styles.scoreValue}>
                  {isLoading ? <Skeleton width="60px" height="40px" /> : `${overallScore}%`}
                </div>
              </div>
              <div className={styles.scoreInfo}>
                <h2>Maturidade FinOps</h2>
                <p>{getMaturityDescription()}</p>
                <Badge 
                  variant={overallScore >= 60 ? 'success' : overallScore >= 30 ? 'warning' : 'error'} 
                  size="sm" 
                  icon={<Award size={14} />}
                >
                  {getMaturityLevelName()}
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
                    {Math.round(level.score)}%
                  </Badge>
                </div>
                <span className={styles.levelTitle}>{level.name}</span>
                <Progress
                  value={level.score}
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
            {isLoading ? (
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
                      value={Math.min((kpi.value / Math.max(kpi.target, 1)) * 100, 100)}
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
            <CardHeader title="Evolução de Custos" subtitle="Comparativo por período" />
            <CardContent>
              <div className={styles.trendChart}>
                {trendLoading ? (
                  <Skeleton height="200px" />
                ) : trendData.length > 0 ? (
                  <div className={styles.barChart}>
                    {(() => {
                      const maxValue = Math.max(...trendData.map(d => d.value), 1);
                      return trendData.map((item) => (
                        <div key={item.period} className={styles.barItem}>
                          <div className={styles.barLabel}>{item.label}</div>
                          <div className={styles.barContainer}>
                            <div 
                              className={styles.bar}
                              style={{ 
                                width: `${(item.value / maxValue) * 100}%`,
                                background: item.period === '1y' 
                                  ? 'var(--color-primary-400)' 
                                  : item.period === '90d'
                                    ? 'var(--color-info-400)'
                                    : item.period === '30d'
                                      ? 'var(--color-warning-400)'
                                      : 'var(--color-success-400)'
                              }}
                            />
                          </div>
                          <div className={styles.barValue}>${item.value.toFixed(2)}</div>
                        </div>
                      ));
                    })()}
                  </div>
                ) : (
                  <div className={styles.chartPlaceholder}>
                    <BarChart3 size={64} />
                    <p>Gráfico de tendências</p>
                    <span>Os dados de histórico estarão disponíveis após a coleta contínua</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader title="Resumo de Custos" subtitle="Visão consolidada" />
            <CardContent>
              <div className={styles.summaryGrid}>
                {trendData.map((item) => (
                  <div key={item.period} className={styles.summaryItem}>
                    <span className={styles.summaryLabel}>{item.label}</span>
                    <span className={styles.summaryValue}>${item.value.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabPanel>
      </Tabs>
    </div>
  );
}

export default Analytics;
