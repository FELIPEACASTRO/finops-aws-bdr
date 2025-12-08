import { useState, useEffect, useCallback } from 'react';
import { DollarSign, TrendingDown, TrendingUp, Filter, Download } from 'lucide-react';
import { Header } from '../components/layout/Header';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableHeaderCell,
  Skeleton,
  Badge,
  Select,
  Tabs,
  TabList,
  Tab,
  TabPanel,
  Progress,
} from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import styles from './Costs.module.css';

interface ServiceCost {
  service: string;
  cost: number;
  percentage: number;
  trend: 'up' | 'down' | 'stable';
  change: number;
}

interface CostsData {
  total: number;
  previousPeriod: number;
  change: number;
  byService: ServiceCost[];
  byCategory: { name: string; value: number }[];
}

export function Costs() {
  const { get, loading } = useFetch();
  const [data, setData] = useState<CostsData | null>(null);
  const [period, setPeriod] = useState('30d');
  const [category, setCategory] = useState('all');

  const fetchCosts = useCallback(async () => {
    console.log(`Buscando custos: período=${period}, categoria=${category}`);
    const response = await get<any>(`/api/v1/costs?period=${period}&category=${category}`);
    
    if (response?.status === 'success' && response?.data) {
      const costsData = response.data;
      
      const byService: ServiceCost[] = (costsData.by_service || []).map((s: any) => ({
        service: s.service,
        cost: s.cost,
        percentage: s.percentage,
        trend: s.trend as 'up' | 'down' | 'stable',
        change: s.change,
      }));

      setData({
        total: costsData.total || 0,
        previousPeriod: costsData.previous_period || 0,
        change: costsData.change || 0,
        byService: byService,
        byCategory: costsData.by_category || [],
      });
      console.log(`Custos carregados: ${byService.length} serviços, total: $${costsData.total}`);
    }
  }, [get, period, category]);

  useEffect(() => {
    fetchCosts();
  }, [period, category]);

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD' }).format(value);

  const exportData = () => {
    window.open('/api/v1/export/csv', '_blank');
  };

  const handlePeriodChange = (newPeriod: string) => {
    console.log(`Alterando período para: ${newPeriod}`);
    setPeriod(newPeriod);
  };

  const handleCategoryChange = (newCategory: string) => {
    console.log(`Alterando categoria para: ${newCategory}`);
    setCategory(newCategory);
  };

  return (
    <div className={styles.page}>
      <Header
        title="Custos"
        subtitle="Análise detalhada de custos AWS por serviço e categoria"
        onRefresh={fetchCosts}
        onExport={exportData}
        isLoading={loading}
      />

      <div className={styles.filters}>
        <Select
          label="Período"
          value={period}
          onChange={handlePeriodChange}
          options={[
            { value: '7d', label: 'Últimos 7 dias' },
            { value: '30d', label: 'Últimos 30 dias' },
            { value: '90d', label: 'Últimos 90 dias' },
            { value: '1y', label: 'Último ano' },
          ]}
        />
        <Select
          label="Categoria"
          value={category}
          onChange={handleCategoryChange}
          options={[
            { value: 'all', label: 'Todas as categorias' },
            { value: 'compute', label: 'Compute' },
            { value: 'storage', label: 'Storage' },
            { value: 'database', label: 'Database' },
            { value: 'network', label: 'Network' },
          ]}
        />
      </div>

      <div className={styles.summary}>
        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.metric}>
              <span className={styles.metricLabel}>Custo Total</span>
              {loading ? (
                <Skeleton width="120px" height="36px" />
              ) : (
                <span className={styles.metricValue}>
                  {formatCurrency(data?.total || 0)}
                </span>
              )}
            </div>
            <div className={styles.metricIcon}>
              <DollarSign size={24} />
            </div>
          </CardContent>
        </Card>

        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.metric}>
              <span className={styles.metricLabel}>Período Anterior</span>
              {loading ? (
                <Skeleton width="120px" height="36px" />
              ) : (
                <span className={styles.metricValue}>
                  {formatCurrency(data?.previousPeriod || 0)}
                </span>
              )}
            </div>
            <div className={styles.metricIcon}>
              <TrendingDown size={24} />
            </div>
          </CardContent>
        </Card>

        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.metric}>
              <span className={styles.metricLabel}>Variação</span>
              {loading ? (
                <Skeleton width="80px" height="36px" />
              ) : (
                <span className={`${styles.metricValue} ${(data?.change || 0) > 0 ? styles.negative : styles.positive}`}>
                  {(data?.change || 0) > 0 ? '+' : ''}{data?.change?.toFixed(1)}%
                </span>
              )}
            </div>
            <div className={styles.metricIcon}>
              <TrendingUp size={24} />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultTab="services">
        <TabList>
          <Tab id="services" icon={<DollarSign size={16} />}>
            Por Serviço
          </Tab>
          <Tab id="categories" icon={<Filter size={16} />}>
            Por Categoria
          </Tab>
        </TabList>

        <TabPanel id="services">
          <Card>
            <CardHeader
              title="Custos por Serviço AWS"
              action={
                <Button variant="ghost" size="sm" icon={<Download size={16} />} onClick={exportData}>
                  Exportar
                </Button>
              }
            />
            <CardContent>
              {loading ? (
                <div className={styles.tableLoading}>
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} height="48px" />
                  ))}
                </div>
              ) : data?.byService && data.byService.length > 0 ? (
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell>Serviço</TableHeaderCell>
                      <TableHeaderCell align="right">Custo</TableHeaderCell>
                      <TableHeaderCell align="right">%</TableHeaderCell>
                      <TableHeaderCell align="center">Tendência</TableHeaderCell>
                      <TableHeaderCell align="right">Variação</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.byService.map((service) => (
                      <TableRow key={service.service}>
                        <TableCell>
                          <span className={styles.serviceName}>{service.service}</span>
                        </TableCell>
                        <TableCell align="right">
                          {formatCurrency(service.cost)}
                        </TableCell>
                        <TableCell align="right">
                          <Progress
                            value={service.percentage}
                            size="sm"
                            variant={service.percentage > 50 ? 'warning' : 'primary'}
                          />
                          <span className={styles.percentageText}>
                            {service.percentage.toFixed(1)}%
                          </span>
                        </TableCell>
                        <TableCell align="center">
                          {service.trend === 'up' ? (
                            <TrendingUp size={16} className={styles.trendUp} />
                          ) : (
                            <TrendingDown size={16} className={styles.trendDown} />
                          )}
                        </TableCell>
                        <TableCell align="right">
                          <Badge
                            variant={service.change > 0 ? 'error' : 'success'}
                            size="sm"
                          >
                            {service.change > 0 ? '+' : ''}{service.change}%
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className={styles.emptyState}>
                  <p>Nenhum serviço encontrado para os filtros selecionados.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel id="categories">
          <Card>
            <CardHeader title="Distribuição por Categoria" />
            <CardContent>
              <div className={styles.categoryList}>
                {data?.byCategory.map((cat) => (
                  <div key={cat.name} className={styles.categoryItem}>
                    <div className={styles.categoryInfo}>
                      <span className={styles.categoryName}>{cat.name}</span>
                      <span className={styles.categoryValue}>{cat.value}%</span>
                    </div>
                    <Progress value={cat.value} variant="primary" size="md" />
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

export default Costs;
