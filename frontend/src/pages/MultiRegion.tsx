import { useState, useEffect } from 'react';
import {
  Globe,
  MapPin,
  TrendingUp,
  TrendingDown,
  Server,
  DollarSign,
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import {
  Card,
  CardContent,
  CardHeader,
  Badge,
  Skeleton,
  Progress,
  Table,
  TableHead,
  TableBody,
  TableRow,
  TableCell,
  TableHeaderCell,
} from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import styles from './MultiRegion.module.css';

interface RegionData {
  region: string;
  name: string;
  cost: number;
  resources: number;
  services: number;
  trend: number;
  status: 'active' | 'inactive';
}

const regionNames: Record<string, string> = {
  'us-east-1': 'N. Virginia',
  'us-east-2': 'Ohio',
  'us-west-1': 'N. California',
  'us-west-2': 'Oregon',
  'eu-west-1': 'Ireland',
  'eu-west-2': 'London',
  'eu-central-1': 'Frankfurt',
  'ap-southeast-1': 'Singapore',
  'ap-southeast-2': 'Sydney',
  'ap-northeast-1': 'Tokyo',
  'sa-east-1': 'São Paulo',
};

export function MultiRegion() {
  const { get } = useFetch();
  const [regions, setRegions] = useState<RegionData[]>([]);
  const [totalCost, setTotalCost] = useState(0);
  const [activeRegions, setActiveRegions] = useState(0);
  const [loading, setLoading] = useState(true);
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    if (!dataLoaded) {
      fetchMultiRegion();
    }
  }, [dataLoaded]);

  const fetchMultiRegion = async () => {
    console.log('Buscando dados multi-region...');
    setLoading(true);
    try {
      const response = await get<any>('/api/v1/multi-region');
      console.log('Multi-region response:', response);
      
      const rawData = response?.data || response;
      const regionsSource = rawData?.regions || rawData;
      const costsByRegion = rawData?.costs_by_region || {};
      
      let regionsData: RegionData[] = [];
      
      if (Array.isArray(regionsSource)) {
        console.log('Formato array detectado:', regionsSource.length, 'regiões');
        regionsData = regionsSource.map((item: any) => {
          const regionCode = item.region || item.name || 'unknown';
          const cost = item.cost || item.costs?.total || item.total_cost || 0;
          const resourceCount = item.resources || item.resource_count || 0;
          const serviceCount = item.services || item.service_count || 0;
          const trend = item.trend || 0;
          
          return {
            region: regionCode,
            name: regionNames[regionCode] || regionCode,
            cost: typeof cost === 'number' ? cost : parseFloat(cost) || 0,
            resources: typeof resourceCount === 'number' ? resourceCount : 
              (typeof resourceCount === 'object' ? Object.values(resourceCount).reduce((s: number, v: any) => s + (Number(v) || 0), 0) : 0),
            services: serviceCount,
            trend: trend,
            status: (cost > 0 || resourceCount > 0 ? 'active' : 'inactive') as 'active' | 'inactive',
          };
        });
      } else if (regionsSource && typeof regionsSource === 'object') {
        console.log('Formato objeto detectado:', Object.keys(regionsSource).length, 'regiões');
        regionsData = Object.entries(regionsSource).map(
          ([region, data]: [string, any]) => {
            const costFromData = typeof data.costs === 'number' ? data.costs : (data.costs?.total || 0);
            const costFromByRegion = costsByRegion[region] || 0;
            const cost = costFromData || costFromByRegion;
            
            const resourcesObj = data.resources || {};
            const resources = typeof resourcesObj === 'number' ? resourcesObj :
              Object.values(resourcesObj).reduce((sum: number, val: any) => sum + (typeof val === 'number' ? val : 0), 0);
            
            const trend = data.trend || 0;
            
            return {
              region,
              name: regionNames[region] || region,
              cost,
              resources,
              services: Object.keys(data.costs?.by_service || {}).length || (cost > 0 ? 1 : 0),
              trend,
              status: (resources > 0 || cost > 0 ? 'active' : 'inactive') as 'active' | 'inactive',
            };
          }
        );
      } else {
        console.log('Nenhuma região encontrada na resposta:', rawData);
        setLoading(false);
        setDataLoaded(true);
        return;
      }

      const sorted = regionsData.sort((a, b) => b.cost - a.cost);
      setRegions(sorted);
      setTotalCost(sorted.reduce((acc, r) => acc + r.cost, 0));
      setActiveRegions(sorted.filter((r) => r.status === 'active').length);
      setDataLoaded(true);
      console.log(`Multi-region carregado: ${sorted.length} regiões, total: $${sorted.reduce((acc, r) => acc + r.cost, 0).toFixed(2)}`);
    } catch (err) {
      console.error('Erro ao buscar multi-region:', err);
      setDataLoaded(true);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD' }).format(value);

  const getRegionPercentage = (cost: number) =>
    totalCost > 0 ? (cost / totalCost) * 100 : 0;

  return (
    <div className={styles.page}>
      <Header
        title="Multi-Region"
        subtitle="Análise de custos e recursos por região AWS"
        onRefresh={fetchMultiRegion}
        isLoading={loading}
      />

      <div className={styles.summary}>
        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.summaryIcon}>
              <Globe size={24} />
            </div>
            <div className={styles.summaryInfo}>
              <span className={styles.summaryLabel}>Regiões Ativas</span>
              {loading ? (
                <Skeleton width="60px" height="32px" />
              ) : (
                <span className={styles.summaryValue}>{activeRegions}</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.summaryIcon}>
              <DollarSign size={24} />
            </div>
            <div className={styles.summaryInfo}>
              <span className={styles.summaryLabel}>Custo Total</span>
              {loading ? (
                <Skeleton width="100px" height="32px" />
              ) : (
                <span className={styles.summaryValue}>{formatCurrency(totalCost)}</span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className={styles.summaryCard}>
          <CardContent>
            <div className={styles.summaryIcon}>
              <Server size={24} />
            </div>
            <div className={styles.summaryInfo}>
              <span className={styles.summaryLabel}>Total Recursos</span>
              {loading ? (
                <Skeleton width="60px" height="32px" />
              ) : (
                <span className={styles.summaryValue}>
                  {regions.reduce((acc, r) => acc + r.resources, 0)}
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className={styles.content}>
        <Card className={styles.tableCard}>
          <CardHeader title="Custos por Região" />
          <CardContent>
            {loading ? (
              <div className={styles.loading}>
                {[...Array(5)].map((_, i) => (
                  <Skeleton key={i} height="56px" />
                ))}
              </div>
            ) : (
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell>Região</TableHeaderCell>
                    <TableHeaderCell align="center">Status</TableHeaderCell>
                    <TableHeaderCell align="right">Custo</TableHeaderCell>
                    <TableHeaderCell align="right">Recursos</TableHeaderCell>
                    <TableHeaderCell>Distribuição</TableHeaderCell>
                    <TableHeaderCell align="right">Tendência</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {regions.map((region) => (
                    <TableRow key={region.region}>
                      <TableCell>
                        <div className={styles.regionCell}>
                          <MapPin size={16} className={styles.regionIcon} />
                          <div>
                            <span className={styles.regionCode}>{region.region}</span>
                            <span className={styles.regionName}>{region.name}</span>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell align="center">
                        <Badge
                          variant={region.status === 'active' ? 'success' : 'default'}
                          size="sm"
                        >
                          {region.status === 'active' ? 'Ativo' : 'Inativo'}
                        </Badge>
                      </TableCell>
                      <TableCell align="right">
                        <span className={styles.cost}>{formatCurrency(region.cost)}</span>
                      </TableCell>
                      <TableCell align="right">
                        <span className={styles.resources}>{region.resources}</span>
                      </TableCell>
                      <TableCell>
                        <div className={styles.progressWrapper}>
                          <Progress
                            value={getRegionPercentage(region.cost)}
                            size="sm"
                            variant={getRegionPercentage(region.cost) > 50 ? 'warning' : 'primary'}
                          />
                          <span className={styles.percentage}>
                            {getRegionPercentage(region.cost).toFixed(1)}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell align="right">
                        <div className={`${styles.trend} ${region.trend > 0 ? styles.up : styles.down}`}>
                          {region.trend > 0 ? (
                            <TrendingUp size={14} />
                          ) : (
                            <TrendingDown size={14} />
                          )}
                          <span>{Math.abs(region.trend)}%</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card className={styles.chartCard}>
          <CardHeader title="Distribuição Regional" />
          <CardContent>
            <div className={styles.barChart}>
              {regions.slice(0, 8).map((region) => (
                <div key={region.region} className={styles.barItem}>
                  <div className={styles.barLabel}>
                    <span className={styles.barRegion}>{region.name}</span>
                    <span className={styles.barValue}>{formatCurrency(region.cost)}</span>
                  </div>
                  <div className={styles.barTrack}>
                    <div
                      className={styles.barFill}
                      style={{ width: `${getRegionPercentage(region.cost)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default MultiRegion;
