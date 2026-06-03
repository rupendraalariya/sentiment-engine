import React from 'react';
import { cn } from '@/utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'positive' | 'negative' | 'neutral' | 'primary' | 'secondary';
  children: React.ReactNode;
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'primary', children, ...props }, ref) => {
    const variants = {
      positive: 'bg-green-500/20 text-green-400 border-green-500/50',
      negative: 'bg-red-500/20 text-red-400 border-red-500/50',
      neutral: 'bg-gray-500/20 text-gray-400 border-gray-500/50',
      primary: 'bg-primary/20 text-primary border-primary/50',
      secondary: 'bg-secondary/20 text-secondary border-secondary/50',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold transition-colors',
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
