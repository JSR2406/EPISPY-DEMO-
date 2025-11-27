import type { Config } from 'tailwindcss';
import { colors, typography, spacing, shadows, borderRadius, transitions, breakpoints } from './theme';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './index.html',
  ],
  darkMode: 'class', // Enable class-based dark mode
  theme: {
    extend: {
      colors: {
        // Primary colors
        primary: colors.primary,
        secondary: colors.secondary,
        
        // Risk colors
        risk: colors.risk,
        
        // Health status colors
        health: colors.health,
        
        // Chart colors
        chart: colors.charts,
        
        // Semantic colors
        success: colors.semantic.success,
        warning: colors.semantic.warning,
        error: colors.semantic.error,
        info: colors.semantic.info,
        
        // Gray scale
        gray: colors.gray,
        
        // Theme-aware colors
        background: {
          DEFAULT: colors.light.background,
          dark: colors.dark.background,
        },
        surface: {
          DEFAULT: colors.light.surface,
          dark: colors.dark.surface,
        },
        text: {
          DEFAULT: colors.light.text,
          secondary: colors.light.textSecondary,
          tertiary: colors.light.textTertiary,
          dark: colors.dark.text,
          'dark-secondary': colors.dark.textSecondary,
        },
        border: {
          DEFAULT: colors.light.border,
          dark: colors.dark.border,
        },
      },
      
      fontFamily: {
        sans: typography.fonts.primary.split(','),
        mono: typography.fonts.mono.split(','),
        display: typography.fonts.display.split(','),
      },
      
      fontSize: {
        ...typography.sizes,
      },
      
      fontWeight: {
        ...typography.weights,
      },
      
      lineHeight: {
        ...typography.lineHeights,
      },
      
      letterSpacing: {
        ...typography.letterSpacing,
      },
      
      spacing: {
        ...spacing,
      },
      
      boxShadow: {
        ...shadows,
      },
      
      borderRadius: {
        ...borderRadius,
      },
      
      transitionDuration: {
        ...transitions.duration,
      },
      
      transitionTimingFunction: {
        ...transitions.easing,
      },
      
      screens: {
        ...breakpoints,
      },
      
      backdropBlur: {
        xs: '2px',
      },
      
      // Custom animations
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'fade-out': 'fadeOut 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'slide-left': 'slideLeft 0.3s ease-out',
        'slide-right': 'slideRight 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'scale-out': 'scaleOut 0.2s ease-in',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'bounce-slow': 'bounce 2s infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideLeft: {
          '0%': { transform: 'translateX(10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideRight: {
          '0%': { transform: 'translateX(-10px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        scaleIn: {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        scaleOut: {
          '0%': { transform: 'scale(1)', opacity: '1' },
          '100%': { transform: 'scale(0.95)', opacity: '0' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
};

export default config;

