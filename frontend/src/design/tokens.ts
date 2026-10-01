/**
 * Design System - Design Tokens
 * Dark Command Center aesthetic with glasmorphism
 */

export const designTokens = {
  // Background Colors
  colors: {
    bg: {
      dark: '#0f1419',
      panel: '#1a1f2e',
      overlay: 'rgba(26, 31, 46, 0.85)',
    },
    
    // Disaster Severity
    severity: {
      high: '#ff6b6b',
      medium: '#f39c12',
      low: '#2ecc71',
    },
    
    // Glasmorphism
    glass: {
      bg: 'rgba(26, 31, 46, 0.7)',
      border: 'rgba(255, 255, 255, 0.15)',
      blur: 'blur(10px)',
    },
    
    // Accent Colors
    accent: {
      cyan: '#00bcd4',
      green: '#1dd1a1',
      purple: '#9c27b0',
    },
    
    // Text
    text: {
      primary: '#e0e0e0',
      secondary: '#9e9e9e',
      muted: '#666666',
    },
    
    // Border
    border: 'rgba(255, 255, 255, 0.15)',
  },
  
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },
  
  typography: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: {
      xs: '12px',
      sm: '14px',
      base: '16px',
      lg: '18px',
      xl: '20px',
      '2xl': '24px',
    },
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
  },
  
  shadow: {
    sm: '0 1px 3px rgba(0, 0, 0, 0.1)',
    md: '0 4px 6px rgba(0, 0, 0, 0.1)',
    lg: '0 8px 32px rgba(0, 0, 0, 0.4)',
    glow: '0 0 20px rgba(255, 107, 107, 0.5)',
  },
  
  transition: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    normal: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '350ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
  
  radius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
  },
}

export type DesignTokens = typeof designTokens
