import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, AlertTriangle, Lightbulb, TrendingUp, FileText, Check, ExternalLink, RefreshCw, Loader2 } from 'lucide-react';
import styles from './NotificationPanel.module.css';

interface Notification {
  id: string;
  type: 'anomaly' | 'recommendation' | 'budget' | 'report';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  link: string;
  severity?: string;
  source?: string;
}

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const NOTIFICATION_ICONS = {
  anomaly: <AlertTriangle size={16} />,
  recommendation: <Lightbulb size={16} />,
  budget: <TrendingUp size={16} />,
  report: <FileText size={16} />,
};

const NOTIFICATION_COLORS = {
  anomaly: '#ef4444',
  recommendation: '#3b82f6',
  budget: '#f59e0b',
  report: '#10b981',
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#dc2626',
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#3b82f6',
  info: '#10b981',
};

export function NotificationPanel({ isOpen, onClose }: NotificationPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [readIds, setReadIds] = useState<Set<string>>(() => {
    const saved = localStorage.getItem('finops_read_notifications');
    return saved ? new Set(JSON.parse(saved)) : new Set();
  });

  const fetchNotifications = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/v1/notifications');
      const data = await response.json();
      
      if (data.status === 'success' && Array.isArray(data.notifications)) {
        const notificationsWithReadState = data.notifications.map((n: Notification) => ({
          ...n,
          read: readIds.has(n.id)
        }));
        setNotifications(notificationsWithReadState);
      } else {
        setNotifications([]);
      }
    } catch (err) {
      console.error('Erro ao carregar notificações:', err);
      setError('Erro ao carregar notificações');
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, [readIds]);

  useEffect(() => {
    if (isOpen) {
      fetchNotifications();
    }
  }, [isOpen, fetchNotifications]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        const notificationButton = document.querySelector('[aria-label="Notificações"]');
        if (notificationButton && !notificationButton.contains(event.target as Node)) {
          onClose();
        }
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose]);

  useEffect(() => {
    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        onClose();
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  const handleNotificationClick = (notification: Notification) => {
    const newReadIds = new Set(readIds);
    newReadIds.add(notification.id);
    setReadIds(newReadIds);
    localStorage.setItem('finops_read_notifications', JSON.stringify([...newReadIds]));
    
    setNotifications(notifications.map(n => 
      n.id === notification.id ? { ...n, read: true } : n
    ));
    onClose();
    navigate(notification.link);
  };

  const markAllAsRead = () => {
    const allIds = new Set(notifications.map(n => n.id));
    const newReadIds = new Set([...readIds, ...allIds]);
    setReadIds(newReadIds);
    localStorage.setItem('finops_read_notifications', JSON.stringify([...newReadIds]));
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  const getNotificationColor = (notification: Notification): string => {
    if (notification.severity) {
      return SEVERITY_COLORS[notification.severity] || NOTIFICATION_COLORS[notification.type];
    }
    return NOTIFICATION_COLORS[notification.type] || '#6b7280';
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  if (!isOpen) return null;

  return (
    <div ref={panelRef} className={styles.panel}>
      <div className={styles.header}>
        <h3 className={styles.title}>Notificações</h3>
        <div className={styles.headerActions}>
          <button
            className={styles.refreshButton}
            onClick={fetchNotifications}
            disabled={loading}
            title="Atualizar notificações"
          >
            {loading ? <Loader2 size={14} className={styles.spinning} /> : <RefreshCw size={14} />}
          </button>
          {unreadCount > 0 && (
            <button 
              className={styles.markAllRead}
              onClick={markAllAsRead}
              title="Marcar todas como lidas"
            >
              <Check size={14} />
              Marcar todas
            </button>
          )}
          <button 
            className={styles.closeButton}
            onClick={onClose}
            aria-label="Fechar painel"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      <div className={styles.content}>
        {loading && notifications.length === 0 ? (
          <div className={styles.empty}>
            <Loader2 size={24} className={styles.spinning} />
            <p>Carregando...</p>
          </div>
        ) : error ? (
          <div className={styles.empty}>
            <p>{error}</p>
            <button onClick={fetchNotifications} className={styles.retryButton}>
              Tentar novamente
            </button>
          </div>
        ) : notifications.length === 0 ? (
          <div className={styles.empty}>
            <p>Nenhuma notificação</p>
            <span className={styles.emptyHint}>
              As notificações aparecem quando há anomalias de custo, alertas de orçamento ou novas recomendações.
            </span>
          </div>
        ) : (
          <ul className={styles.list}>
            {notifications.map(notification => (
              <li 
                key={notification.id}
                className={`${styles.item} ${notification.read ? styles.read : styles.unread}`}
                onClick={() => handleNotificationClick(notification)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleNotificationClick(notification)}
              >
                <div 
                  className={styles.icon}
                  style={{ 
                    backgroundColor: `${getNotificationColor(notification)}20`, 
                    color: getNotificationColor(notification) 
                  }}
                >
                  {NOTIFICATION_ICONS[notification.type]}
                </div>
                <div className={styles.details}>
                  <span className={styles.itemTitle}>{notification.title}</span>
                  <p className={styles.message}>{notification.message}</p>
                  <div className={styles.meta}>
                    <span className={styles.timestamp}>{notification.timestamp}</span>
                    {notification.source && (
                      <span className={styles.source}>{notification.source}</span>
                    )}
                  </div>
                </div>
                <div className={styles.actionIcon}>
                  <ExternalLink size={14} />
                </div>
                {!notification.read && <div className={styles.unreadDot} />}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className={styles.footer}>
        <a href="/settings" className={styles.settingsLink}>
          Configurar notificações
        </a>
      </div>
    </div>
  );
}

export default NotificationPanel;
