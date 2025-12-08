import { type HTMLAttributes, forwardRef } from 'react';
import styles from './Skeleton.module.css';

export interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'rectangular' | 'circular';
  animation?: 'pulse' | 'shimmer' | 'none';
}

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  (
    {
      width,
      height,
      variant = 'rectangular',
      animation = 'shimmer',
      className = '',
      style,
      ...props
    },
    ref
  ) => {
    const skeletonClasses = [
      styles.skeleton,
      styles[variant],
      styles[animation],
      className,
    ]
      .filter(Boolean)
      .join(' ');

    const skeletonStyle = {
      width: typeof width === 'number' ? `${width}px` : width,
      height: typeof height === 'number' ? `${height}px` : height,
      ...style,
    };

    return (
      <div
        ref={ref}
        className={skeletonClasses}
        style={skeletonStyle}
        aria-hidden="true"
        {...props}
      />
    );
  }
);

Skeleton.displayName = 'Skeleton';

export interface SkeletonCardProps {
  lines?: number;
  showHeader?: boolean;
}

export const SkeletonCard = ({ lines = 3, showHeader = true }: SkeletonCardProps) => {
  return (
    <div className={styles.card}>
      {showHeader && (
        <div className={styles.cardHeader}>
          <Skeleton width={120} height={16} />
          <Skeleton width={80} height={12} />
        </div>
      )}
      <div className={styles.cardContent}>
        <Skeleton width="60%" height={32} />
        <div className={styles.cardLines}>
          {Array.from({ length: lines }).map((_, i) => (
            <Skeleton key={i} width={`${100 - i * 15}%`} height={12} />
          ))}
        </div>
      </div>
    </div>
  );
};

SkeletonCard.displayName = 'SkeletonCard';

export default Skeleton;
