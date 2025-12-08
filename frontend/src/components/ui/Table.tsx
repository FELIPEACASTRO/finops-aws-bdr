import { type HTMLAttributes, type ReactNode, forwardRef } from 'react';
import styles from './Table.module.css';

export interface TableProps extends HTMLAttributes<HTMLTableElement> {
  children: ReactNode;
}

export const Table = forwardRef<HTMLTableElement, TableProps>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <div className={styles.wrapper}>
        <table ref={ref} className={`${styles.table} ${className}`} {...props}>
          {children}
        </table>
      </div>
    );
  }
);

Table.displayName = 'Table';

export interface TableHeadProps extends HTMLAttributes<HTMLTableSectionElement> {
  children: ReactNode;
}

export const TableHead = forwardRef<HTMLTableSectionElement, TableHeadProps>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <thead ref={ref} className={`${styles.thead} ${className}`} {...props}>
        {children}
      </thead>
    );
  }
);

TableHead.displayName = 'TableHead';

export interface TableBodyProps extends HTMLAttributes<HTMLTableSectionElement> {
  children: ReactNode;
}

export const TableBody = forwardRef<HTMLTableSectionElement, TableBodyProps>(
  ({ children, className = '', ...props }, ref) => {
    return (
      <tbody ref={ref} className={`${styles.tbody} ${className}`} {...props}>
        {children}
      </tbody>
    );
  }
);

TableBody.displayName = 'TableBody';

export interface TableRowProps extends HTMLAttributes<HTMLTableRowElement> {
  children: ReactNode;
  clickable?: boolean;
}

export const TableRow = forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ children, clickable = false, className = '', ...props }, ref) => {
    const rowClasses = [
      styles.tr,
      clickable ? styles.clickable : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <tr ref={ref} className={rowClasses} {...props}>
        {children}
      </tr>
    );
  }
);

TableRow.displayName = 'TableRow';

export interface TableCellProps extends HTMLAttributes<HTMLTableCellElement> {
  children?: ReactNode;
  align?: 'left' | 'center' | 'right';
}

export const TableCell = forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ children, align = 'left', className = '', ...props }, ref) => {
    const cellClasses = [styles.td, styles[`align-${align}`], className]
      .filter(Boolean)
      .join(' ');

    return (
      <td ref={ref} className={cellClasses} {...props}>
        {children}
      </td>
    );
  }
);

TableCell.displayName = 'TableCell';

export interface TableHeaderCellProps extends HTMLAttributes<HTMLTableCellElement> {
  children?: ReactNode;
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  sorted?: 'asc' | 'desc' | null;
  onSort?: () => void;
}

export const TableHeaderCell = forwardRef<HTMLTableCellElement, TableHeaderCellProps>(
  (
    { children, align = 'left', sortable = false, sorted = null, onSort, className = '', ...props },
    ref
  ) => {
    const cellClasses = [
      styles.th,
      styles[`align-${align}`],
      sortable ? styles.sortable : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    const handleClick = () => {
      if (sortable && onSort) {
        onSort();
      }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (sortable && onSort && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault();
        onSort();
      }
    };

    return (
      <th
        ref={ref}
        className={cellClasses}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        tabIndex={sortable ? 0 : undefined}
        aria-sort={sorted === 'asc' ? 'ascending' : sorted === 'desc' ? 'descending' : undefined}
        {...props}
      >
        <span className={styles.thContent}>
          {children}
          {sortable && (
            <span className={styles.sortIcon} aria-hidden="true">
              {sorted === 'asc' ? '↑' : sorted === 'desc' ? '↓' : '↕'}
            </span>
          )}
        </span>
      </th>
    );
  }
);

TableHeaderCell.displayName = 'TableHeaderCell';

export interface EmptyStateProps {
  message?: string;
  icon?: ReactNode;
  action?: ReactNode;
  colSpan?: number;
}

export const TableEmptyState = ({
  message = 'Nenhum dado encontrado',
  icon,
  action,
  colSpan = 1,
}: EmptyStateProps) => {
  return (
    <tr>
      <td colSpan={colSpan} className={styles.emptyState}>
        {icon && <span className={styles.emptyIcon}>{icon}</span>}
        <p className={styles.emptyMessage}>{message}</p>
        {action && <div className={styles.emptyAction}>{action}</div>}
      </td>
    </tr>
  );
};

TableEmptyState.displayName = 'TableEmptyState';

export default Table;
