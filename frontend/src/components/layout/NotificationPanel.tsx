import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, AlertTriangle, Lightbulb, TrendingUp, FileText, Check, ExternalLink } from 'lucide-react';
import styles from './NotificationPanel.module.css';

interface Notification {
  id: string;
  type: 'anomaly' | 'recommendation' | 'budget' | 'report';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  link: string;
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

export function NotificationPanel({ isOpen, onClose }: NotificationPanelProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      type: 'anomaly',
      title: 'Anomalia de Custo Detectada',
      message: 'Aumento de 45% nos custos de EC2 na região us-east-1 nas últimas 24h.',
      timestamp: '2 min atrás',
      read: false,
      link: '/costs',
    },
    {
      id: '2',
      type: 'recommendation',
      title: 'Nova Recomendação Disponível',
      message: '3 instâncias EC2 identificadas para rightsizing. Economia potencial: $847/mês.',
      timestamp: '15 min atrás',
      read: false,
      link: '/recommendations',
    },
    {
      id: '3',
      type: 'budget',
      title: 'Alerta de Orçamento',
      message: 'Orçamento mensal atingiu 85% do limite. Projeção: ultrapassar em 5 dias.',
      timestamp: '1 hora atrás',
      read: false,
      link: '/analytics',
    },
  ]);

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
    setNotifications(notifications.map(n => 
      n.id === notification.id ? { ...n, read: true } : n
    ));
    onClose();
    navigate(notification.link);
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  const unreadCount = notifications.filter(n => !n.read).length;

  if (!isOpen) return null;

  return (
    <div ref={panelRef} className={styles.panel}>
      <div className={styles.header}>
        <h3 className={styles.title}>Notificações</h3>
        <div className={styles.headerActions}>
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
        {notifications.length === 0 ? (
          <div className={styles.empty}>
            <p>Nenhuma notificação</p>
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
                  style={{ backgroundColor: `${NOTIFICATION_COLORS[notification.type]}20`, color: NOTIFICATION_COLORS[notification.type] }}
                >
                  {NOTIFICATION_ICONS[notification.type]}
                </div>
                <div className={styles.details}>
                  <span className={styles.itemTitle}>{notification.title}</span>
                  <p className={styles.message}>{notification.message}</p>
                  <span className={styles.timestamp}>{notification.timestamp}</span>
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
