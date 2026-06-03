import { HTMLAttributes, forwardRef } from 'react';
import { cn } from '@/utils/cn';

export interface BadgeProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'positive' | 'negative' | 'neutral' | 'default' | 'success' | 'error' | 'warning';
}

const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', children, ...props }, ref) => {
    const variants = {
      positive: 'bg-green-500/20 text-green-400 border-green-500/30',
      negative: 'bg-red-500/20 text-red-400 border-red-500/30',
      neutral: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
      default: 'bg-primary/20 text-primary border-primary/30',
      success: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      error: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
      warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border backdrop-blur-sm',
          variants[variant],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Badge.displayName = 'Badge';

export default Badge;
