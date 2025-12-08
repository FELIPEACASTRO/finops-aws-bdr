import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  DollarSign,
  Lightbulb,
  Bot,
  Globe,
  Settings,
  BarChart3,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import styles from './Sidebar.module.css';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  path: string;
  badge?: number;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard />, path: '/' },
  { id: 'costs', label: 'Custos', icon: <DollarSign />, path: '/costs' },
  { id: 'recommendations', label: 'Recomendações', icon: <Lightbulb />, path: '/recommendations' },
  { id: 'ai-consultant', label: 'Consultor IA', icon: <Bot />, path: '/ai-consultant' },
  { id: 'multi-region', label: 'Multi-Region', icon: <Globe />, path: '/multi-region' },
  { id: 'analytics', label: 'Analytics', icon: <BarChart3 />, path: '/analytics' },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();

  return (
    <aside
      className={`${styles.sidebar} ${collapsed ? styles.collapsed : ''}`}
      aria-label="Menu principal"
    >
      <div className={styles.header}>
        <div className={styles.logo}>
          <span className={styles.logoIcon} aria-hidden="true">📊</span>
          {!collapsed && <span className={styles.logoText}>FinOps AWS</span>}
        </div>
        <button
          className={styles.toggle}
          onClick={onToggle}
          aria-label={collapsed ? 'Expandir menu' : 'Recolher menu'}
          aria-expanded={!collapsed}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
      </div>

      <nav className={styles.nav} aria-label="Navegação principal">
        <ul className={styles.navList} role="list">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            
            return (
              <li key={item.id} role="listitem">
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `${styles.navLink} ${isActive ? styles.active : ''}`
                  }
                  aria-current={isActive ? 'page' : undefined}
                  title={collapsed ? item.label : undefined}
                >
                  <span className={styles.navIcon} aria-hidden="true">
                    {item.icon}
                  </span>
                  {!collapsed && (
                    <>
                      <span className={styles.navLabel}>{item.label}</span>
                      {item.badge !== undefined && item.badge > 0 && (
                        <span className={styles.navBadge} aria-label={`${item.badge} itens`}>
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className={styles.footer}>
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `${styles.navLink} ${isActive ? styles.active : ''}`
          }
          title={collapsed ? 'Configurações' : undefined}
        >
          <span className={styles.navIcon} aria-hidden="true">
            <Settings />
          </span>
          {!collapsed && <span className={styles.navLabel}>Configurações</span>}
        </NavLink>
      </div>
    </aside>
  );
}

export default Sidebar;
