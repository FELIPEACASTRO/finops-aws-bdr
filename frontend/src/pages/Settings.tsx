import { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Key,
  Bell,
  Palette,
  Database,
  Shield,
  Save,
  RefreshCw,
  CheckCircle,
} from 'lucide-react';
import { Header } from '../components/layout/Header';
import {
  Card,
  CardContent,
  CardHeader,
  Button,
  Select,
  Tabs,
  TabList,
  Tab,
  TabPanel,
  Badge,
  Alert,
  Skeleton,
} from '../components/ui';
import { useFetch } from '../hooks/useFetch';
import styles from './Settings.module.css';

interface Integration {
  provider: string;
  id: string;
  status: 'ok' | 'warning' | 'error';
  detail: string;
}

interface NotificationTypes {
  cost_anomaly: boolean;
  new_recommendations: boolean;
  budget_alert: boolean;
  weekly_report: boolean;
}

export function Settings() {
  const { get, put, post, loading } = useFetch();
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [clearingCache, setClearingCache] = useState(false);
  const [cacheCleared, setCacheCleared] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [theme, setTheme] = useState('dark');
  const [region, setRegion] = useState('us-east-1');
  const [notificationFrequency, setNotificationFrequency] = useState('all');
  const [notificationTypes, setNotificationTypes] = useState<NotificationTypes>({
    cost_anomaly: true,
    new_recommendations: true,
    budget_alert: true,
    weekly_report: false,
  });
  const [aiProvider, setAiProvider] = useState('perplexity');
  const [cacheEnabled, setCacheEnabled] = useState('enabled');
  const [cacheTTL, setCacheTTL] = useState('15');
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [integrationsLoading, setIntegrationsLoading] = useState(true);

  useEffect(() => {
    loadSettings();
    loadIntegrations();
  }, []);

  const loadSettings = async () => {
    console.log('Carregando configurações da API...');
    const response = await get<any>('/api/v1/settings');
    if (response?.status === 'success' && response?.settings) {
      const settings = response.settings;
      console.log('Configurações carregadas da API:', settings);
      setTheme(settings.theme || 'dark');
      setRegion(settings.region || 'us-east-1');
      setAiProvider(settings.ai_provider || 'perplexity');
      setCacheEnabled(settings.cache?.enabled ? 'enabled' : 'disabled');
      setCacheTTL(String(settings.cache?.ttl_minutes || 15));
      setNotificationFrequency(settings.notifications?.frequency || 'all');
      if (settings.notifications?.types) {
        setNotificationTypes({
          cost_anomaly: settings.notifications.types.cost_anomaly ?? true,
          new_recommendations: settings.notifications.types.new_recommendations ?? true,
          budget_alert: settings.notifications.types.budget_alert ?? true,
          weekly_report: settings.notifications.types.weekly_report ?? false,
        });
      }
    }
  };

  const loadIntegrations = async () => {
    setIntegrationsLoading(true);
    console.log('Carregando status das integrações...');
    try {
      const response = await get<any>('/api/v1/integrations/status');
      if (response?.status === 'success' && response?.integrations) {
        console.log('Integrações carregadas:', response.integrations);
        setIntegrations(response.integrations);
      }
    } catch (error) {
      console.error('Erro ao carregar integrações:', error);
    } finally {
      setIntegrationsLoading(false);
    }
  };

  const handleSave = async () => {
    setValidationError(null);
    
    const ttlNum = parseInt(cacheTTL);
    if (isNaN(ttlNum) || ttlNum < 1 || ttlNum > 1440) {
      setValidationError('TTL deve ser entre 1 e 1440 minutos');
      return;
    }
    
    setSaving(true);
    console.log('Salvando configurações...');
    
    try {
      const response = await put<any>('/api/v1/settings', {
        theme,
        region,
        ai_provider: aiProvider,
        notifications: {
          frequency: notificationFrequency,
          types: notificationTypes
        },
        cache: {
          enabled: cacheEnabled === 'enabled',
          ttl_minutes: ttlNum
        }
      });
      
      if (response?.status === 'success') {
        console.log('Configurações salvas com sucesso na API');
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (error) {
      console.error('Erro ao salvar configurações na API:', error);
      setValidationError('Erro ao salvar configurações. Tente novamente.');
    } finally {
      setSaving(false);
    }
  };

  const handleClearCache = async () => {
    setClearingCache(true);
    console.log('Limpando cache...');
    try {
      const response = await post<any>('/api/v1/cache/clear', {});
      if (response?.status === 'success') {
        console.log('Cache limpo:', response.cleared_at);
        setCacheCleared(true);
        setTimeout(() => setCacheCleared(false), 3000);
      }
    } catch (error) {
      console.error('Erro ao limpar cache:', error);
    } finally {
      setClearingCache(false);
    }
  };

  const handleNotificationTypeChange = (type: keyof NotificationTypes) => {
    setNotificationTypes(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ok':
        return <Badge variant="success" size="sm">Conectado</Badge>;
      case 'warning':
        return <Badge variant="warning" size="sm">Limitado</Badge>;
      default:
        return <Badge variant="warning" size="sm">Não Configurado</Badge>;
    }
  };

  return (
    <div className={styles.page}>
      <Header
        title="Configurações"
        subtitle="Preferências e configurações do sistema"
        onRefresh={loadSettings}
        isLoading={loading}
      />

      {saved && (
        <Alert variant="success" className={styles.alert}>
          <CheckCircle size={16} />
          Configurações salvas com sucesso!
        </Alert>
      )}

      {validationError && (
        <Alert variant="error" className={styles.alert}>
          {validationError}
        </Alert>
      )}

      <Tabs defaultTab="general">
        <TabList>
          <Tab id="general" icon={<SettingsIcon size={16} />}>
            Geral
          </Tab>
          <Tab id="api" icon={<Key size={16} />}>
            API & Integrações
          </Tab>
          <Tab id="notifications" icon={<Bell size={16} />}>
            Notificações
          </Tab>
          <Tab id="cache" icon={<Database size={16} />}>
            Cache
          </Tab>
        </TabList>

        <TabPanel id="general">
          <Card>
            <CardHeader
              title="Aparência"
              subtitle="Personalize a interface do dashboard"
              icon={<Palette size={20} />}
            />
            <CardContent>
              {loading ? (
                <Skeleton height="60px" />
              ) : (
                <div className={styles.formGroup}>
                  <Select
                    label="Tema"
                    value={theme}
                    onChange={(value) => {
                      console.log('Tema alterado para:', value);
                      setTheme(value);
                    }}
                    options={[
                      { value: 'dark', label: 'Escuro' },
                      { value: 'light', label: 'Claro' },
                      { value: 'system', label: 'Sistema' },
                    ]}
                  />
                  <p className={styles.hint}>
                    O tema escuro é recomendado para reduzir o cansaço visual.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Região Padrão"
              subtitle="Configure a região AWS principal"
              icon={<Shield size={20} />}
            />
            <CardContent>
              {loading ? (
                <Skeleton height="60px" />
              ) : (
                <div className={styles.formGroup}>
                  <Select
                    label="Região AWS"
                    value={region}
                    onChange={(value) => {
                      console.log('Região alterada para:', value);
                      setRegion(value);
                    }}
                    options={[
                      { value: 'us-east-1', label: 'US East (N. Virginia)' },
                      { value: 'us-west-2', label: 'US West (Oregon)' },
                      { value: 'eu-west-1', label: 'EU (Ireland)' },
                      { value: 'sa-east-1', label: 'South America (São Paulo)' },
                    ]}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel id="api">
          <Card>
            <CardHeader
              title="Provedor de IA"
              subtitle="Selecione o provedor para o Consultor IA"
              icon={<Key size={20} />}
            />
            <CardContent>
              <div className={styles.formGroup}>
                <Select
                  label="Provedor Padrão"
                  value={aiProvider}
                  onChange={(value) => {
                    console.log('Provedor IA alterado para:', value);
                    setAiProvider(value);
                  }}
                  options={[
                    { value: 'perplexity', label: 'Perplexity AI' },
                    { value: 'openai', label: 'OpenAI ChatGPT' },
                    { value: 'gemini', label: 'Google Gemini' },
                    { value: 'amazon_q', label: 'Amazon Q Business' },
                  ]}
                />
              </div>

              <div className={styles.apiStatus}>
                <h4>Status das APIs</h4>
                {integrationsLoading ? (
                  <div className={styles.statusList}>
                    <Skeleton height="40px" />
                    <Skeleton height="40px" />
                    <Skeleton height="40px" />
                  </div>
                ) : (
                  <div className={styles.statusList}>
                    {integrations.map((integration) => (
                      <div key={integration.id} className={styles.statusItem}>
                        <span>{integration.provider}</span>
                        {getStatusBadge(integration.status)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel id="notifications">
          <Card>
            <CardHeader
              title="Preferências de Notificação"
              subtitle="Configure quando receber alertas"
              icon={<Bell size={20} />}
            />
            <CardContent>
              <div className={styles.formGroup}>
                <Select
                  label="Frequência"
                  value={notificationFrequency}
                  onChange={(value) => {
                    console.log('Frequência de notificações alterada para:', value);
                    setNotificationFrequency(value);
                  }}
                  options={[
                    { value: 'all', label: 'Todas as notificações' },
                    { value: 'important', label: 'Apenas importantes' },
                    { value: 'critical', label: 'Apenas críticas' },
                    { value: 'none', label: 'Desativado' },
                  ]}
                />
              </div>

              <div className={styles.notificationTypes}>
                <h4>Tipos de Alerta</h4>
                <div className={styles.checkList}>
                  <label className={styles.checkItem}>
                    <input 
                      type="checkbox" 
                      checked={notificationTypes.cost_anomaly}
                      onChange={() => handleNotificationTypeChange('cost_anomaly')}
                    />
                    <span>Anomalias de custo detectadas</span>
                  </label>
                  <label className={styles.checkItem}>
                    <input 
                      type="checkbox" 
                      checked={notificationTypes.new_recommendations}
                      onChange={() => handleNotificationTypeChange('new_recommendations')}
                    />
                    <span>Novas recomendações de otimização</span>
                  </label>
                  <label className={styles.checkItem}>
                    <input 
                      type="checkbox" 
                      checked={notificationTypes.budget_alert}
                      onChange={() => handleNotificationTypeChange('budget_alert')}
                    />
                    <span>Orçamento próximo do limite</span>
                  </label>
                  <label className={styles.checkItem}>
                    <input 
                      type="checkbox" 
                      checked={notificationTypes.weekly_report}
                      onChange={() => handleNotificationTypeChange('weekly_report')}
                    />
                    <span>Relatórios semanais</span>
                  </label>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel id="cache">
          <Card>
            <CardHeader
              title="Configurações de Cache"
              subtitle="Otimize a performance das consultas AWS"
              icon={<Database size={20} />}
            />
            <CardContent>
              {loading ? (
                <Skeleton height="80px" />
              ) : (
                <div className={styles.formRow}>
                  <Select
                    label="Status do Cache"
                    value={cacheEnabled}
                    onChange={(value) => {
                      console.log('Cache alterado para:', value);
                      setCacheEnabled(value);
                    }}
                    options={[
                      { value: 'enabled', label: 'Ativado' },
                      { value: 'disabled', label: 'Desativado' },
                    ]}
                  />
                  <Select
                    label="TTL (Tempo de vida)"
                    value={cacheTTL}
                    onChange={(value) => {
                      console.log('TTL alterado para:', value);
                      setCacheTTL(value);
                    }}
                    options={[
                      { value: '5', label: '5 minutos' },
                      { value: '15', label: '15 minutos' },
                      { value: '30', label: '30 minutos' },
                      { value: '60', label: '1 hora' },
                      { value: '120', label: '2 horas' },
                    ]}
                  />
                </div>
              )}

              <div className={styles.cacheInfo}>
                <p>
                  O cache reduz chamadas repetidas às APIs da AWS, melhorando a
                  performance e reduzindo custos. Configure o TTL de acordo com
                  a frequência de mudanças em seus recursos.
                </p>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<RefreshCw size={16} />}
                  onClick={handleClearCache}
                  loading={clearingCache}
                >
                  {clearingCache ? 'Limpando...' : 'Limpar Cache'}
                </Button>
                {cacheCleared && (
                  <span className={styles.cacheSuccess}>Cache limpo com sucesso!</span>
                )}
              </div>
            </CardContent>
          </Card>
        </TabPanel>
      </Tabs>

      <div className={styles.actions}>
        <Button 
          variant="primary" 
          icon={<Save size={16} />} 
          onClick={handleSave}
          loading={saving}
        >
          {saving ? 'Salvando...' : 'Salvar Configurações'}
        </Button>
      </div>
    </div>
  );
}

export default Settings;
