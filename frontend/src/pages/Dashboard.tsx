import { useState } from 'react';
import { DollarSign, TrendingDown, Server, Lightbulb, Play, FileDown, Printer, Globe, Check } from 'lucide-react';
import { Header } from '../components/layout';
import { Card, CardHeader, CardContent, Button, Badge, Table, TableHead, TableBody, TableRow, TableCell, TableHeaderCell, TableEmptyState, Alert, SkeletonCard } from '../components/ui';
import { useDashboard } from '../hooks';
import { api } from '../services/api';
import styles from './Dashboard.module.css';

interface MetricCardProps {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  trend?: 'up' | 'down' | 'stable';
  loading?: boolean;
}

function MetricCard({ title, value, subtitle, icon, trend, loading }: MetricCardProps) {
  if (loading) {
    return <SkeletonCard lines={2} />;
  }

  return (
    <Card variant="interactive" className={styles.metricCard}>
      <div className={styles.metricHeader}>
        <span className={styles.metricTitle}>{title}</span>
      </div>
      <div className={styles.metricValue}>{value}</div>
      <div className={styles.metricFooter}>
        <span className={`${styles.metricSubtitle} ${trend ? styles[trend] : ''}`}>
          {trend === 'down' && '↓ '}
          {trend === 'up' && '↑ '}
          {subtitle}
        </span>
        <span className={styles.metricIcon} aria-hidden="true">{icon}</span>
      </div>
    </Card>
  );
}

export function Dashboard() {
  const { stats, services, recommendations, isLoading, error, refresh, runAnalysis } = useDashboard();
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);
  const [analysisType, setAnalysisType] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleExport = async (format: 'csv' | 'json' | 'html') => {
    console.log('Exportando formato:', format);
    setExportingFormat(format);
    try {
      await api.exportReport(format);
      console.log('Exportação concluída:', format);
      showSuccess(`Exportação ${format.toUpperCase()} iniciada com sucesso!`);
    } catch (err) {
      console.error('Erro ao exportar:', err);
      alert(`Erro ao exportar ${format}: ${err instanceof Error ? err.message : 'Erro desconhecido'}`);
    } finally {
      setExportingFormat(null);
    }
  };

  const handleAnalysis = async (type: 'full' | 'costs_only' | 'recommendations_only') => {
    console.log('Iniciando análise:', type);
    setAnalysisType(type);
    try {
      await runAnalysis(type);
      console.log('Análise concluída:', type);
      showSuccess('Análise concluída com sucesso!');
    } catch (err) {
      console.error('Erro na análise:', err);
    } finally {
      setAnalysisType(null);
    }
  };

  return (
    <div className={styles.page}>
      <Header
        title="Dashboard"
        subtitle="Análise Inteligente de Custos AWS - Otimize seus gastos em nuvem"
        onRefresh={refresh}
        isLoading={isLoading}
      />

      <div className={styles.content}>
        {error && (
          <Alert variant="error" title="Erro ao carregar dados" dismissible>
            {error.message}. Clique em "Atualizar" para tentar novamente.
          </Alert>
        )}

        {stats && !error && (
          <Alert variant="success" dismissible>
            Dados carregados: {formatCurrency(stats.totalCost)} em {stats.servicesAnalyzed} serviços
          </Alert>
        )}

        {successMessage && (
          <Alert variant="info" dismissible icon={<Check size={16} />}>
            {successMessage}
          </Alert>
        )}

        <section className={styles.metrics} aria-label="Métricas principais">
          <MetricCard
            title="Custo Total (30d)"
            value={stats ? formatCurrency(stats.totalCost) : '...'}
            subtitle="AWS Cost Explorer"
            icon={<DollarSign size={24} />}
            loading={isLoading && !stats}
          />
          <MetricCard
            title="Economia Potencial"
            value={stats ? formatCurrency(stats.potentialSavings) : '...'}
            subtitle="economia estimada"
            icon={<TrendingDown size={24} />}
            trend="down"
            loading={isLoading && !stats}
          />
          <MetricCard
            title="Serviços Analisados"
            value={stats ? stats.servicesAnalyzed.toString() : '...'}
            subtitle="AWS Cost Explorer"
            icon={<Server size={24} />}
            loading={isLoading && !stats}
          />
          <MetricCard
            title="Recomendações"
            value={stats ? stats.recommendationsCount.toString() : '...'}
            subtitle="Otimizações"
            icon={<Lightbulb size={24} />}
            loading={isLoading && !stats}
          />
        </section>

        <Card className={styles.actionsCard}>
          <CardHeader
            title="Executar Análise"
            icon={<Play size={20} />}
          />
          <CardContent>
            <div className={styles.actionButtons}>
              <div className={styles.actionRow}>
                <Button
                  variant="primary"
                  onClick={() => handleAnalysis('full')}
                  loading={analysisType === 'full' || isLoading}
                  disabled={!!analysisType || isLoading}
                  icon={<Play size={16} />}
                >
                  Análise Completa
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => handleAnalysis('costs_only')}
                  loading={analysisType === 'costs_only'}
                  disabled={!!analysisType || isLoading}
                >
                  Apenas Custos
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => handleAnalysis('recommendations_only')}
                  loading={analysisType === 'recommendations_only'}
                  disabled={!!analysisType || isLoading}
                >
                  Apenas Recomendações
                </Button>
              </div>
              <div className={styles.actionRow}>
                <Button
                  variant="success"
                  onClick={() => handleExport('csv')}
                  loading={exportingFormat === 'csv'}
                  disabled={!!exportingFormat}
                  icon={<FileDown size={16} />}
                >
                  Exportar CSV
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => handleExport('json')}
                  loading={exportingFormat === 'json'}
                  disabled={!!exportingFormat}
                  icon={<FileDown size={16} />}
                  style={{ background: 'var(--color-accent-purple)' }}
                >
                  Exportar JSON
                </Button>
                <Button
                  variant="warning"
                  onClick={() => handleExport('html')}
                  loading={exportingFormat === 'html'}
                  disabled={!!exportingFormat}
                  icon={<Printer size={16} />}
                >
                  Versão Impressão
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => window.location.href = '/multi-region'}
                  icon={<Globe size={16} />}
                  style={{ background: 'var(--color-accent-cyan)' }}
                >
                  Multi-Region
                </Button>
              </div>
            </div>
            {stats && (
              <p className={styles.lastUpdated}>
                Atualizado em {stats.lastUpdated} | Custo: {formatCurrency(stats.totalCost)}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Top 10 Serviços por Custo"
            icon={<DollarSign size={20} />}
          />
          <CardContent>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Serviço</TableHeaderCell>
                  <TableHeaderCell align="right">Custo Mensal</TableHeaderCell>
                  <TableHeaderCell align="right">% do Total</TableHeaderCell>
                  <TableHeaderCell align="center">Tendência</TableHeaderCell>
                  <TableHeaderCell align="center">Status</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoading && services.length === 0 ? (
                  <TableEmptyState message="Carregando dados..." colSpan={5} />
                ) : services.length === 0 ? (
                  <TableEmptyState 
                    message="Nenhum serviço encontrado. Execute uma análise para ver os custos." 
                    colSpan={5}
                    action={
                      <Button variant="primary" onClick={() => runAnalysis('full')}>
                        Executar Análise
                      </Button>
                    }
                  />
                ) : (
                  services.map((service) => (
                    <TableRow key={service.name}>
                      <TableCell>{service.name}</TableCell>
                      <TableCell align="right">{formatCurrency(service.cost)}</TableCell>
                      <TableCell align="right">{service.percentage.toFixed(1)}%</TableCell>
                      <TableCell align="center">→ Estável</TableCell>
                      <TableCell align="center">
                        <Badge variant="warning">Monitor</Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader
            title="Top Recomendações de Economia"
            icon={<Lightbulb size={20} />}
          />
          <CardContent>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell>Recomendação</TableHeaderCell>
                  <TableHeaderCell>Recurso</TableHeaderCell>
                  <TableHeaderCell align="right">Economia/Mês</TableHeaderCell>
                  <TableHeaderCell align="center">Prioridade</TableHeaderCell>
                  <TableHeaderCell align="center">Ação</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {isLoading && recommendations.length === 0 ? (
                  <TableEmptyState message="Carregando recomendações..." colSpan={5} />
                ) : recommendations.length === 0 ? (
                  <TableEmptyState 
                    message="Nenhuma recomendação pendente" 
                    colSpan={5}
                    icon={<Lightbulb size={48} />}
                  />
                ) : (
                  recommendations.slice(0, 10).map((rec, index) => (
                    <TableRow key={rec.id || index}>
                      <TableCell>{rec.title || rec.type}</TableCell>
                      <TableCell>{rec.resource_id || '-'}</TableCell>
                      <TableCell align="right">{formatCurrency(rec.savings || 0)}</TableCell>
                      <TableCell align="center">
                        <Badge 
                          variant={
                            rec.priority === 'HIGH' ? 'error' : 
                            rec.priority === 'MEDIUM' ? 'warning' : 'success'
                          }
                        >
                          {rec.priority}
                        </Badge>
                      </TableCell>
                      <TableCell align="center">
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => window.open('https://console.aws.amazon.com', '_blank')}
                        >
                          Ver AWS
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default Dashboard;
