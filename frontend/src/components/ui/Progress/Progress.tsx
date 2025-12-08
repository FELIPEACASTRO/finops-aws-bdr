import styles from './Progress.module.css';

interface ProgressProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'success' | 'warning' | 'danger';
  showLabel?: boolean;
  label?: string;
  className?: string;
}

export function Progress({
  value,
  max = 100,
  size = 'md',
  variant = 'primary',
  showLabel = false,
  label,
  className = '',
}: ProgressProps) {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={`${styles.wrapper} ${className}`}>
      {(showLabel || label) && (
        <div className={styles.labelRow}>
          {label && <span className={styles.label}>{label}</span>}
          {showLabel && (
            <span className={styles.percentage}>{Math.round(percentage)}%</span>
          )}
        </div>
      )}
      <div
        className={`${styles.track} ${styles[size]}`}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
      >
        <div
          className={`${styles.bar} ${styles[variant]}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export default Progress;
