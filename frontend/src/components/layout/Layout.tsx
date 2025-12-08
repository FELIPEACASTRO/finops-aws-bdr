import { useState, type ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import styles from './Layout.module.css';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => !prev);
  };

  return (
    <div className={styles.layout}>
      <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />
      
      <main
        className={`${styles.main} ${sidebarCollapsed ? styles.collapsed : ''}`}
        id="main-content"
      >
        <a href="#main-content" className={styles.skipLink}>
          Pular para o conteúdo principal
        </a>
        {children}
      </main>
    </div>
  );
}

export default Layout;
