/**
 * Card Component - EpiSPY Design System
 * 
 * Elevated card with glassmorphism, hover effects, and smooth animations.
 * Perfect for displaying data, metrics, and information cards.
 */

import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const cardVariants = cva(
  // Base styles
  'rounded-lg border transition-all duration-base',
  'bg-surface dark:bg-surface-dark',
  'border-border dark:border-border-dark',
  {
    variants: {
      variant: {
        default: 'shadow-sm',
        elevated: 'shadow-md',
        glass: 'glass backdrop-blur-md bg-white/70 dark:bg-surface-dark/70 border-white/30 dark:border-white/10',
        outlined: 'shadow-none border-2',
        flat: 'shadow-none border-0 bg-transparent',
      },
      hover: {
        true: 'hover:shadow-lg hover:-translate-y-1 cursor-pointer',
        false: '',
      },
      interactive: {
        true: 'cursor-pointer select-none',
        false: '',
      },
    },
    defaultVariants: {
      variant: 'default',
      hover: false,
      interactive: false,
    },
  }
);

export interface CardProps
  extends Omit<HTMLMotionProps<'div'>, 'variants'>,
    VariantProps<typeof cardVariants> {
  children: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  glow?: boolean;
  glowColor?: 'primary' | 'success' | 'warning' | 'error';
}

const paddingMap = {
  none: 'p-0',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8',
};

const glowColors = {
  primary: 'shadow-glow-primary',
  success: 'shadow-[0_0_20px_rgba(76,175,80,0.3)]',
  warning: 'shadow-[0_0_20px_rgba(255,179,0,0.3)]',
  error: 'shadow-[0_0_20px_rgba(211,47,47,0.3)]',
};

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant,
      hover,
      interactive,
      children,
      padding = 'md',
      glow = false,
      glowColor = 'primary',
      ...props
    },
    ref
  ) => {
    return (
      <motion.div
        ref={ref}
        className={cn(
          cardVariants({ variant, hover, interactive }),
          paddingMap[padding],
          glow && glowColors[glowColor],
          className
        )}
        whileHover={hover ? { y: -4, transition: { duration: 0.2 } } : {}}
        whileTap={interactive ? { scale: 0.98 } : {}}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';

// Card sub-components
export const CardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex flex-col space-y-1.5 pb-4', className)}
    {...props}
  />
));
CardHeader.displayName = 'CardHeader';

export const CardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('text-2xl font-semibold leading-none tracking-tight text-text', className)}
    {...props}
  />
));
CardTitle.displayName = 'CardTitle';

export const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-text-secondary', className)}
    {...props}
  />
));
CardDescription.displayName = 'CardDescription';

export const CardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={cn('', className)} {...props} />
));
CardContent.displayName = 'CardContent';

export const CardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center pt-4', className)}
    {...props}
  />
));
CardFooter.displayName = 'CardFooter';

export default Card;

