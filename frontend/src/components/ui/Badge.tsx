/**
 * Badge Component - EpiSPY Design System
 * 
 * Status indicators, risk levels, and labels with semantic colors.
 * Healthcare-optimized for risk communication.
 */

import React from 'react';
import { motion } from 'framer-motion';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  // Base styles
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
  'transition-all duration-fast',
  {
    variants: {
      variant: {
        // Risk levels
        minimal: 'bg-risk-minimal/10 text-risk-minimal border border-risk-minimal/20',
        low: 'bg-risk-low/10 text-risk-low border border-risk-low/20',
        moderate: 'bg-risk-moderate/10 text-risk-moderate border border-risk-moderate/20',
        high: 'bg-risk-high/10 text-risk-high border border-risk-high/20',
        critical: 'bg-risk-critical/10 text-risk-critical border border-risk-critical/20 animate-pulse-glow',
        
        // Health status
        healthy: 'bg-health-healthy/10 text-health-healthy border border-health-healthy/20',
        exposed: 'bg-health-exposed/10 text-health-exposed border border-health-exposed/20',
        infected: 'bg-health-infected/10 text-health-infected border border-health-infected/20',
        recovered: 'bg-health-recovered/10 text-health-recovered border border-health-recovered/20',
        vaccinated: 'bg-health-vaccinated/10 text-health-vaccinated border border-health-vaccinated/20',
        
        // Semantic
        success: 'bg-success-light text-success-dark border border-success-main',
        warning: 'bg-warning-light text-warning-dark border border-warning-main',
        error: 'bg-error-light text-error-dark border border-error-main',
        info: 'bg-info-light text-info-dark border border-info-main',
        
        // Neutral
        default: 'bg-gray-100 text-gray-800 border border-gray-300 dark:bg-gray-800 dark:text-gray-200 dark:border-gray-600',
        primary: 'bg-primary-100 text-primary-700 border border-primary-300 dark:bg-primary-900/30 dark:text-primary-300',
        secondary: 'bg-secondary-100 text-secondary-700 border border-secondary-300 dark:bg-secondary-900/30 dark:text-secondary-300',
      },
      size: {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-2.5 py-0.5 text-xs',
        lg: 'px-3 py-1 text-sm',
      },
      dot: {
        true: 'pl-1.5',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'md',
      dot: false,
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  children: React.ReactNode;
  pulse?: boolean;
  icon?: React.ReactNode;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  (
    {
      className,
      variant,
      size,
      dot = false,
      children,
      pulse = false,
      icon,
      ...props
    },
    ref
  ) => {
    return (
      <motion.span
        ref={ref}
        className={cn(badgeVariants({ variant, size, dot: dot || !!icon }), className)}
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.2 }}
        whileHover={{ scale: 1.05 }}
        {...props}
      >
        {icon && (
          <span className="mr-1 flex-shrink-0">
            {icon}
          </span>
        )}
        {dot && !icon && (
          <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current opacity-75" />
        )}
        <span>{children}</span>
        {pulse && (
          <motion.span
            className="absolute inset-0 rounded-full bg-current opacity-20"
            animate={{ scale: [1, 1.5, 1], opacity: [0.2, 0, 0.2] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        )}
      </motion.span>
    );
  }
);

Badge.displayName = 'Badge';

export default Badge;

