import { type HTMLAttributes, type ReactNode, forwardRef } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import styles from './Alert.module.css';

export type AlertVariant = 'success' | 'warning' | 'error' | 'info';

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  variant?: AlertVariant;
  title?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  icon?: ReactNode;
  children: ReactNode;
}

const defaultIcons: Record<AlertVariant, ReactNode> = {
  success: <CheckCircle />,
  warning: <AlertTriangle />,
  error: <XCircle />,
  info: <Info />,
};

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      variant = 'info',
      title,
      dismissible = false,
      onDismiss,
      icon,
      children,
      className = '',
      ...props
    },
    ref
  ) => {
    const alertClasses = [styles.alert, styles[variant], className]
      .filter(Boolean)
      .join(' ');

    const displayIcon = icon ?? defaultIcons[variant];

    return (
      <div
        ref={ref}
        className={alertClasses}
        role="alert"
        aria-live="polite"
        {...props}
      >
        <span className={styles.icon} aria-hidden="true">
          {displayIcon}
        </span>
        <div className={styles.content}>
          {title && <p className={styles.title}>{title}</p>}
          <p className={styles.message}>{children}</p>
        </div>
        {dismissible && (
          <button
            type="button"
            className={styles.dismiss}
            onClick={onDismiss}
            aria-label="Fechar alerta"
          >
            <X size={16} />
          </button>
        )}
      </div>
    );
  }
);

Alert.displayName = 'Alert';

export default Alert;
