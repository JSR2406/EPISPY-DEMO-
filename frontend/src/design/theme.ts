/**
 * EpiSPY Design System - Comprehensive Design Tokens
 * 
 * Healthcare-optimized color psychology, accessibility-first design,
 * and modern 2025 visual trends (glassmorphism, gradients, micro-interactions)
 */

// ============================================================================
// COLOR PALETTE - Healthcare Optimized
// ============================================================================

export const colors = {
  // Primary (Medical Blue - Trust, Professional, Calm)
  primary: {
    50: '#E3F2FD',   // Lightest - backgrounds
    100: '#BBDEFB',  // Light - hover states
    200: '#90CAF9',  // Lighter - subtle accents
    300: '#64B5F6',  // Light - secondary actions
    400: '#42A5F5',  // Medium-light - active states
    500: '#2196F3',  // Main brand color - primary actions
    600: '#1E88E5',  // Medium-dark - hover primary
    700: '#1976D2',  // Dark - pressed states
    800: '#1565C0',  // Darker - emphasis
    900: '#0D47A1',  // Darkest - high contrast
  },

  // Secondary (Teal - Health, Growth, Recovery)
  secondary: {
    50: '#E0F7FA',
    100: '#B2EBF2',
    200: '#80DEEA',
    300: '#4DD0E1',
    400: '#26C6DA',
    500: '#00BCD4',  // Main secondary
    600: '#00ACC1',
    700: '#0097A7',
    800: '#00838F',
    900: '#006064',
  },

  // Risk Level Colors (Semantic - Color-blind friendly)
  risk: {
    minimal: '#4CAF50',   // Green - Safe
    low: '#8BC34A',       // Light Green - Low risk
    moderate: '#FFC107',  // Amber - Moderate risk
    high: '#FF9800',      // Orange - High risk
    critical: '#F44336',  // Red - Critical
    unknown: '#9E9E9E',   // Gray - Unknown
  },

  // Health Status Colors
  health: {
    healthy: '#00E676',     // Bright Green
    exposed: '#FFB300',    // Amber
    infected: '#FF5252',    // Red
    recovered: '#40C4FF',  // Cyan
    deceased: '#424242',   // Dark Gray
    vaccinated: '#7C4DFF', // Purple
    quarantined: '#FF6F00', // Deep Orange
  },

  // Data Visualization Palette (Color-blind accessible)
  charts: {
    primary: '#2196F3',    // Blue
    secondary: '#4CAF50',  // Green
    tertiary: '#FF9800',   // Orange
    quaternary: '#9C27B0', // Purple
    quinary: '#00BCD4',    // Cyan
    senary: '#F44336',     // Red
    septenary: '#FFEB3B',  // Yellow
    octonary: '#795548',   // Brown
  },

  // Neutral Grays (Accessible contrast ratios)
  gray: {
    50: '#FAFAFA',   // Almost white - backgrounds
    100: '#F5F5F5',  // Very light - subtle backgrounds
    200: '#EEEEEE',  // Light - borders, dividers
    300: '#E0E0E0',  // Light gray - disabled states
    400: '#BDBDBD',  // Medium-light - placeholder text
    500: '#9E9E9E',  // Medium - secondary text
    600: '#757575',  // Medium-dark - body text
    700: '#616161',  // Dark - headings
    800: '#424242',  // Darker - emphasis
    900: '#212121',  // Darkest - high contrast text
  },

  // UI State Colors
  semantic: {
    success: {
      light: '#C8E6C9',
      main: '#4CAF50',
      dark: '#388E3C',
      contrast: '#FFFFFF',
    },
    warning: {
      light: '#FFE082',
      main: '#FFB300',
      dark: '#F57C00',
      contrast: '#000000',
    },
    error: {
      light: '#EF9A9A',
      main: '#D32F2F',
      dark: '#C62828',
      contrast: '#FFFFFF',
    },
    info: {
      light: '#B3E5FC',
      main: '#0288D1',
      dark: '#01579B',
      contrast: '#FFFFFF',
    },
  },

  // Dark Mode Palette
  dark: {
    background: '#0A0E27',      // Deep navy - main background
    surface: '#151A30',         // Slightly lighter - cards
    surfaceHover: '#1E2642',   // Hover state
    surfaceElevated: '#252D47', // Elevated cards
    text: '#E8EAED',           // Primary text
    textSecondary: '#9AA0A6',  // Secondary text
    textTertiary: '#5F6368',  // Tertiary text
    border: '#2C3550',         // Borders
    borderLight: '#3A4258',    // Light borders
    divider: '#2C3550',        // Dividers
  },

  // Light Mode Palette
  light: {
    background: '#FFFFFF',
    surface: '#F9FAFB',
    surfaceHover: '#F3F4F6',
    surfaceElevated: '#FFFFFF',
    text: '#111827',
    textSecondary: '#6B7280',
    textTertiary: '#9CA3AF',
    border: '#E5E7EB',
    borderLight: '#F3F4F6',
    divider: '#E5E7EB',
  },
} as const;

// ============================================================================
// TYPOGRAPHY SCALE
// ============================================================================

export const typography = {
  fonts: {
    primary: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif",
    mono: "'Fira Code', 'Monaco', 'Courier New', 'Consolas', monospace",
    display: "'Poppins', 'Inter', sans-serif", // For headings
  },

  sizes: {
    xs: '0.75rem',      // 12px - Labels, captions
    sm: '0.875rem',     // 14px - Small text
    base: '1rem',       // 16px - Body text
    lg: '1.125rem',     // 18px - Large body
    xl: '1.25rem',      // 20px - Small headings
    '2xl': '1.5rem',    // 24px - H4
    '3xl': '1.875rem',  // 30px - H3
    '4xl': '2.25rem',   // 36px - H2
    '5xl': '3rem',      // 48px - H1
    '6xl': '4rem',      // 64px - Display
    '7xl': '5rem',      // 80px - Hero
  },

  weights: {
    light: 300,
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    extrabold: 800,
  },

  lineHeights: {
    none: 1,
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },

  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },
} as const;

// ============================================================================
// SPACING SCALE (8px base unit)
// ============================================================================

export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
  32: '8rem',     // 128px
} as const;

// ============================================================================
// SHADOWS (Elevation System)
// ============================================================================

export const shadows = {
  none: 'none',
  xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  base: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  md: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  lg: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  xl: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  '2xl': '0 30px 60px -12px rgba(0, 0, 0, 0.3)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  
  // Colored shadows for glassmorphism and depth
  glow: {
    primary: '0 0 20px rgba(33, 150, 243, 0.3)',
    success: '0 0 20px rgba(76, 175, 80, 0.3)',
    warning: '0 0 20px rgba(255, 179, 0, 0.3)',
    error: '0 0 20px rgba(211, 47, 47, 0.3)',
  },
  
  // Dark mode shadows (lighter, more subtle)
  dark: {
    sm: '0 1px 3px 0 rgba(0, 0, 0, 0.3), 0 1px 2px 0 rgba(0, 0, 0, 0.2)',
    base: '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)',
    md: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
    lg: '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
  },
} as const;

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const borderRadius = {
  none: '0',
  xs: '0.125rem',  // 2px
  sm: '0.25rem',   // 4px
  base: '0.5rem',  // 8px
  md: '0.75rem',   // 12px
  lg: '1rem',      // 16px
  xl: '1.5rem',    // 24px
  '2xl': '2rem',   // 32px
  '3xl': '3rem',   // 48px
  full: '9999px',
} as const;

// ============================================================================
// TRANSITIONS & ANIMATIONS
// ============================================================================

export const transitions = {
  // Timing functions
  easing: {
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  },

  // Durations
  duration: {
    instant: '0ms',
    fast: '150ms',
    base: '250ms',
    slow: '350ms',
    slower: '500ms',
    slowest: '750ms',
  },

  // Common transitions
  fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
  base: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
  slow: '350ms cubic-bezier(0.4, 0, 0.2, 1)',
  bounce: '500ms cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  spring: '400ms cubic-bezier(0.175, 0.885, 0.32, 1.275)',
} as const;

// ============================================================================
// Z-INDEX SCALE
// ============================================================================

export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
  notification: 1080,
  max: 9999,
} as const;

// ============================================================================
// BREAKPOINTS (Mobile-first)
// ============================================================================

export const breakpoints = {
  xs: '0px',      // Mobile
  sm: '640px',    // Large mobile
  md: '768px',    // Tablet
  lg: '1024px',   // Desktop
  xl: '1280px',   // Large desktop
  '2xl': '1536px', // Extra large desktop
} as const;

// ============================================================================
// GLASSMORPHISM PRESETS
// ============================================================================

export const glassmorphism = {
  light: {
    background: 'rgba(255, 255, 255, 0.7)',
    backdrop: 'blur(12px) saturate(180%)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
  },
  dark: {
    background: 'rgba(21, 26, 48, 0.7)',
    backdrop: 'blur(12px) saturate(180%)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  strong: {
    background: 'rgba(255, 255, 255, 0.85)',
    backdrop: 'blur(16px) saturate(180%)',
    border: '1px solid rgba(255, 255, 255, 0.4)',
  },
} as const;

// ============================================================================
// GRADIENTS
// ============================================================================

export const gradients = {
  primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  secondary: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  success: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  warning: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  error: 'linear-gradient(135deg, #ff6a00 0%, #ee0979 100%)',
  health: 'linear-gradient(135deg, #00c9ff 0%, #92fe9d 100%)',
  risk: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',
  dark: 'linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%)',
  light: 'linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%)',
  
  // Glassmorphism gradients
  glass: {
    light: 'linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%)',
    dark: 'linear-gradient(135deg, rgba(0, 0, 0, 0.1) 0%, rgba(0, 0, 0, 0.05) 100%)',
  },
} as const;

// ============================================================================
// THEME CONFIGURATION
// ============================================================================

export type ThemeMode = 'light' | 'dark';

export interface Theme {
  mode: ThemeMode;
  colors: typeof colors;
  typography: typeof typography;
  spacing: typeof spacing;
  shadows: typeof shadows;
  borderRadius: typeof borderRadius;
  transitions: typeof transitions;
  zIndex: typeof zIndex;
  breakpoints: typeof breakpoints;
  glassmorphism: typeof glassmorphism;
  gradients: typeof gradients;
}

export const createTheme = (mode: ThemeMode = 'light'): Theme => ({
  mode,
  colors,
  typography,
  spacing,
  shadows,
  borderRadius,
  transitions,
  zIndex,
  breakpoints,
  glassmorphism,
  gradients,
});

// Default theme
export const defaultTheme = createTheme('light');

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get color value from theme
 */
export const getColor = (path: string, theme: Theme = defaultTheme): string => {
  const keys = path.split('.');
  let value: any = theme.colors;
  
  for (const key of keys) {
    value = value?.[key];
    if (value === undefined) break;
  }
  
  return typeof value === 'string' ? value : '';
};

/**
 * Get spacing value
 */
export const getSpacing = (size: keyof typeof spacing): string => {
  return spacing[size];
};

/**
 * Get shadow value
 */
export const getShadow = (size: keyof typeof shadows): string => {
  return shadows[size];
};

/**
 * Get transition value
 */
export const getTransition = (type: keyof typeof transitions): string => {
  return transitions[type];
};

