import { useState, createContext, useContext, type ReactNode } from 'react';
import styles from './Tabs.module.css';

interface TabsContextValue {
  activeTab: string;
  setActiveTab: (id: string) => void;
}

const TabsContext = createContext<TabsContextValue | null>(null);

interface TabsProps {
  defaultTab: string;
  children: ReactNode;
  className?: string;
}

export function Tabs({ defaultTab, children, className = '' }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab);

  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className={`${styles.tabs} ${className}`}>{children}</div>
    </TabsContext.Provider>
  );
}

interface TabListProps {
  children: ReactNode;
  className?: string;
}

export function TabList({ children, className = '' }: TabListProps) {
  return (
    <div className={`${styles.tabList} ${className}`} role="tablist">
      {children}
    </div>
  );
}

interface TabProps {
  id: string;
  children: ReactNode;
  icon?: ReactNode;
}

export function Tab({ id, children, icon }: TabProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('Tab must be used within Tabs');

  const { activeTab, setActiveTab } = context;
  const isActive = activeTab === id;

  return (
    <button
      role="tab"
      aria-selected={isActive}
      aria-controls={`panel-${id}`}
      className={`${styles.tab} ${isActive ? styles.active : ''}`}
      onClick={() => setActiveTab(id)}
    >
      {icon && <span className={styles.tabIcon}>{icon}</span>}
      {children}
    </button>
  );
}

interface TabPanelProps {
  id: string;
  children: ReactNode;
  className?: string;
}

export function TabPanel({ id, children, className = '' }: TabPanelProps) {
  const context = useContext(TabsContext);
  if (!context) throw new Error('TabPanel must be used within Tabs');

  const { activeTab } = context;
  if (activeTab !== id) return null;

  return (
    <div
      role="tabpanel"
      id={`panel-${id}`}
      className={`${styles.tabPanel} ${className}`}
    >
      {children}
    </div>
  );
}

export default Tabs;
