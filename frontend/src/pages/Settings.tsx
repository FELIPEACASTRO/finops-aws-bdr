import { useState } from 'react';
import {
  Settings as SettingsIcon,
  Key,
  Bell,
  Palette,
  Database,
  Shield,
  Save,
  RefreshCw,
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
} from '../components/ui';
import styles from './Settings.module.css';

export function Settings() {
  const [saved, setSaved] = useState(false);
  const [cacheEnabled, setCacheEnabled] = useState('enabled');
  const [cacheTTL, setCacheTTL] = useState('3600');
  const [theme, setTheme] = useState('dark');
  const [notifications, setNotifications] = useState('all');
  const [aiProvider, setAiProvider] = useState('perplexity');

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className={styles.page}>
      <Header
        title="Configurações"
        subtitle="Preferências e configurações do sistema"
      />

      {saved && (
        <Alert variant="success" className={styles.alert}>
          Configurações salvas com sucesso!
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
              <div className={styles.formGroup}>
                <Select
                  label="Tema"
                  value={theme}
                  onChange={setTheme}
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
            </CardContent>
          </Card>

          <Card>
            <CardHeader
              title="Região Padrão"
              subtitle="Configure a região AWS principal"
              icon={<Shield size={20} />}
            />
            <CardContent>
              <div className={styles.formGroup}>
                <Select
                  label="Região AWS"
                  value="us-east-1"
                  onChange={() => {}}
                  options={[
                    { value: 'us-east-1', label: 'US East (N. Virginia)' },
                    { value: 'us-west-2', label: 'US West (Oregon)' },
                    { value: 'eu-west-1', label: 'EU (Ireland)' },
                    { value: 'sa-east-1', label: 'South America (São Paulo)' },
                  ]}
                />
              </div>
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
                  onChange={setAiProvider}
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
                <div className={styles.statusList}>
                  <div className={styles.statusItem}>
                    <span>AWS Cost Explorer</span>
                    <Badge variant="success" size="sm">Conectado</Badge>
                  </div>
                  <div className={styles.statusItem}>
                    <span>Perplexity AI</span>
                    <Badge variant="success" size="sm">Configurado</Badge>
                  </div>
                  <div className={styles.statusItem}>
                    <span>Amazon Q Business</span>
                    <Badge variant="warning" size="sm">Não Configurado</Badge>
                  </div>
                  <div className={styles.statusItem}>
                    <span>OpenAI</span>
                    <Badge variant="warning" size="sm">Não Configurado</Badge>
                  </div>
                </div>
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
                  value={notifications}
                  onChange={setNotifications}
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
                    <input type="checkbox" defaultChecked />
                    <span>Anomalias de custo detectadas</span>
                  </label>
                  <label className={styles.checkItem}>
                    <input type="checkbox" defaultChecked />
                    <span>Novas recomendações de otimização</span>
                  </label>
                  <label className={styles.checkItem}>
                    <input type="checkbox" defaultChecked />
                    <span>Orçamento próximo do limite</span>
                  </label>
                  <label className={styles.checkItem}>
                    <input type="checkbox" />
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
              <div className={styles.formRow}>
                <Select
                  label="Status do Cache"
                  value={cacheEnabled}
                  onChange={setCacheEnabled}
                  options={[
                    { value: 'enabled', label: 'Ativado' },
                    { value: 'disabled', label: 'Desativado' },
                  ]}
                />
                <Select
                  label="TTL (Tempo de vida)"
                  value={cacheTTL}
                  onChange={setCacheTTL}
                  options={[
                    { value: '300', label: '5 minutos' },
                    { value: '900', label: '15 minutos' },
                    { value: '1800', label: '30 minutos' },
                    { value: '3600', label: '1 hora' },
                    { value: '7200', label: '2 horas' },
                  ]}
                />
              </div>

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
                >
                  Limpar Cache
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabPanel>
      </Tabs>

      <div className={styles.actions}>
        <Button variant="primary" icon={<Save size={16} />} onClick={handleSave}>
          Salvar Configurações
        </Button>
      </div>
    </div>
  );
}

export default Settings;
