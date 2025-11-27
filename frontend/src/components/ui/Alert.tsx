/**
 * Alert Component - EpiSPY Design System
 * 
 * Notification alerts with icons, animations, and semantic colors.
 * Perfect for system alerts, warnings, and information messages.
 */

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { X, CheckCircle2, AlertCircle, AlertTriangle, Info } from 'lucide-react';

const alertVariants = cva(
  // Base styles
  'relative w-full rounded-lg border p-4',
  'flex items-start gap-3',
  'transition-all duration-base',
  {
    variants: {
      variant: {
        success: 'bg-success-light/50 border-success-main text-success-dark dark:bg-success-main/10 dark:text-success-light',
        warning: 'bg-warning-light/50 border-warning-main text-warning-dark dark:bg-warning-main/10 dark:text-warning-dark',
        error: 'bg-error-light/50 border-error-main text-error-dark dark:bg-error-main/10 dark:text-error-light',
        info: 'bg-info-light/50 border-info-main text-info-dark dark:bg-info-main/10 dark:text-info-light',
      },
    },
    defaultVariants: {
      variant: 'info',
    },
  }
);

const iconMap = {
  success: CheckCircle2,
  warning: AlertTriangle,
  error: AlertCircle,
  info: Info,
};

export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {
  children: React.ReactNode;
  title?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  icon?: React.ReactNode;
  showIcon?: boolean;
}

export const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      className,
      variant = 'info',
      children,
      title,
      dismissible = false,
      onDismiss,
      icon,
      showIcon = true,
      ...props
    },
    ref
  ) => {
    const Icon = variant ? iconMap[variant] : Info;
    const displayIcon = icon || (showIcon && <Icon className="h-5 w-5 flex-shrink-0" />);

    return (
      <motion.div
        ref={ref}
        className={cn(alertVariants({ variant }), className)}
        initial={{ opacity: 0, y: -10, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        {...props}
      >
        {displayIcon && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.1, type: 'spring' }}
            className="flex-shrink-0"
          >
            {displayIcon}
          </motion.div>
        )}

        <div className="flex-1 min-w-0">
          {title && (
            <h4 className="mb-1 font-semibold leading-none tracking-tight">
              {title}
            </h4>
          )}
          <div className="text-sm [&_p]:leading-relaxed">{children}</div>
        </div>

        {dismissible && (
          <motion.button
            type="button"
            onClick={onDismiss}
            className="flex-shrink-0 rounded-md p-1 opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-current"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <X className="h-4 w-4" />
            <span className="sr-only">Dismiss</span>
          </motion.button>
        )}
      </motion.div>
    );
  }
);

Alert.displayName = 'Alert';

// Alert container for stacking multiple alerts
export interface AlertContainerProps {
  children: React.ReactNode;
  className?: string;
}

export const AlertContainer: React.FC<AlertContainerProps> = ({
  children,
  className,
}) => {
  return (
    <div className={cn('flex flex-col gap-3', className)}>
      <AnimatePresence mode="popLayout">
        {React.Children.map(children, (child, index) => (
          <motion.div
            key={index}
            layout
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10, transition: { duration: 0.2 } }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
          >
            {child}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default Alert;

