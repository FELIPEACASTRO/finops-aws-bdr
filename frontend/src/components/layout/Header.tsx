import { RefreshCw, Bell, Download, Menu } from 'lucide-react';
import { Button } from '../ui';
import styles from './Header.module.css';

interface Breadcrumb {
  label: string;
  path?: string;
}

interface HeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: Breadcrumb[];
  onRefresh?: () => void;
  onExport?: () => void;
  isLoading?: boolean;
  onMenuClick?: () => void;
  showMobileMenu?: boolean;
}

export function Header({
  title,
  subtitle,
  breadcrumbs,
  onRefresh,
  onExport,
  isLoading = false,
  onMenuClick,
  showMobileMenu = false,
}: HeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.left}>
        {showMobileMenu && (
          <button
            className={styles.menuButton}
            onClick={onMenuClick}
            aria-label="Abrir menu"
          >
            <Menu size={24} />
          </button>
        )}

        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className={styles.breadcrumbs} aria-label="Breadcrumbs">
            <ol className={styles.breadcrumbList}>
              {breadcrumbs.map((crumb, index) => (
                <li key={index} className={styles.breadcrumbItem}>
                  {crumb.path ? (
                    <a href={crumb.path} className={styles.breadcrumbLink}>
                      {crumb.label}
                    </a>
                  ) : (
                    <span className={styles.breadcrumbCurrent} aria-current="page">
                      {crumb.label}
                    </span>
                  )}
                  {index < breadcrumbs.length - 1 && (
                    <span className={styles.breadcrumbSeparator} aria-hidden="true">
                      /
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </nav>
        )}

        <div className={styles.titleGroup}>
          <h1 className={styles.title}>{title}</h1>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
      </div>

      <div className={styles.right}>
        {onExport && (
          <Button
            variant="secondary"
            size="sm"
            icon={<Download size={16} />}
            onClick={onExport}
            aria-label="Exportar dados"
          >
            Exportar
          </Button>
        )}

        {onRefresh && (
          <Button
            variant="primary"
            size="sm"
            icon={<RefreshCw size={16} className={isLoading ? styles.spinning : ''} />}
            onClick={onRefresh}
            loading={isLoading}
            aria-label="Atualizar dados"
          >
            Atualizar
          </Button>
        )}

        <button
          className={styles.notificationButton}
          aria-label="Notificações"
        >
          <Bell size={20} />
          <span className={styles.notificationBadge} aria-label="3 notificações">
            3
          </span>
        </button>
      </div>
    </header>
  );
}

export default Header;
