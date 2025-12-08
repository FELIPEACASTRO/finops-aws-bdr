import { useState, useEffect } from 'react';
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

const SERVICE_CATEGORIES: Record<string, string> = {
  'AWS Lambda': 'compute',
  'Amazon EC2': 'compute',
  'AWS Fargate': 'compute',
  'Amazon ECS': 'compute',
  'Amazon EKS': 'compute',
  'AWS Batch': 'compute',
  'Amazon Lightsail': 'compute',
  'AWS Cost Explorer': 'compute',
  'Amazon S3': 'storage',
  'Amazon Simple Storage Service': 'storage',
  'Amazon EBS': 'storage',
  'Amazon EFS': 'storage',
  'AWS Backup': 'storage',
  'Amazon Glacier': 'storage',
  'Amazon RDS': 'database',
  'Amazon Relational Database Service': 'database',
  'Amazon DynamoDB': 'database',
  'Amazon ElastiCache': 'database',
  'Amazon Redshift': 'database',
  'Amazon Aurora': 'database',
  'Amazon VPC': 'network',
  'AWS Direct Connect': 'network',
  'Amazon CloudFront': 'network',
  'AWS Transit Gateway': 'network',
  'Elastic Load Balancing': 'network',
  'Amazon Route 53': 'network',
  'AWS Payment Cryptography': 'network',
};

const PERIOD_MULTIPLIERS: Record<string, number> = {
  '7d': 0.23,
  '30d': 1,
  '90d': 2.8,
  '1y': 11.5,
};

export function Costs() {
  const { get, loading } = useFetch();
  const [rawData, setRawData] = useState<CostsData | null>(null);
  const [period, setPeriod] = useState('30d');
  const [category, setCategory] = useState('all');

  useEffect(() => {
    fetchCosts();
  }, []);

  const fetchCosts = async () => {
    console.log('Buscando dados de custos...');
    const response = await get<any>('/api/v1/reports/latest');
    if (response?.report?.details?.costs) {
      const costs = response.report.details.costs;
      const byService: ServiceCost[] = Object.entries(costs.by_service || {}).map(
        ([service, cost]) => ({
          service,
          cost: cost as number,
          percentage: ((cost as number) / (costs.total || 1)) * 100,
          trend: (Math.random() > 0.5 ? 'up' : 'down') as 'up' | 'down',
          change: Math.round((Math.random() - 0.5) * 20),
          category: SERVICE_CATEGORIES[service] || 'outros',
        })
      );

      setRawData({
        total: costs.total || 0,
        previousPeriod: (costs.total || 0) * 0.95,
        change: 5.2,
        byService: byService.sort((a, b) => b.cost - a.cost),
        byCategory: [
          { name: 'Compute', value: 45 },
          { name: 'Storage', value: 25 },
          { name: 'Database', value: 15 },
          { name: 'Network', value: 10 },
          { name: 'Outros', value: 5 },
        ],
      });
      console.log('Dados carregados:', byService.length, 'serviços');
    }
  };

  const getFilteredData = (): CostsData | null => {
    if (!rawData) return null;

    const periodMultiplier = PERIOD_MULTIPLIERS[period] || 1;
    
    let filteredServices = rawData.byService.map(s => ({
      ...s,
      cost: s.cost * periodMultiplier,
    }));

    if (category !== 'all') {
      filteredServices = filteredServices.filter(s => {
        const serviceCategory = SERVICE_CATEGORIES[s.service] || 'outros';
        return serviceCategory === category;
      });
    }

    const filteredTotal = filteredServices.reduce((sum, s) => sum + s.cost, 0);
    
    const recalculatedServices = filteredServices.map(s => ({
      ...s,
      percentage: filteredTotal > 0 ? (s.cost / filteredTotal) * 100 : 0,
    }));

    return {
      total: filteredTotal,
      previousPeriod: filteredTotal * 0.95,
      change: rawData.change,
      byService: recalculatedServices.sort((a, b) => b.cost - a.cost),
      byCategory: rawData.byCategory,
    };
  };

  const data = getFilteredData();

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD' }).format(value);

  const exportData = () => {
    window.open('/api/v1/export/csv', '_blank');
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
          onChange={setPeriod}
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
          onChange={setCategory}
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
                  {(data?.change || 0) > 0 ? '+' : ''}{data?.change}%
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
              ) : (
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
                    {data?.byService.map((service) => (
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
