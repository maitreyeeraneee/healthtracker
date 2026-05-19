"""
Modern Design System for NutriVerse HealthTracker
Clean, minimalist, premium UI components and styles
"""

# Color Palette - Modern, professional health & wellness colors
COLORS = {
    # Primary colors
    'primary': '#10b981',          # Emerald green - main brand color
    'primary_light': '#34d399',    # Lighter emerald
    'primary_dark': '#059669',     # Darker emerald
    'primary_bg': '#f0fdf4',       # Very light green background
    
    # Secondary colors
    'secondary': '#3b82f6',        # Blue - for secondary actions
    'secondary_light': '#60a5fa',  # Light blue
    'secondary_bg': '#eff6ff',     # Light blue background
    
    # Accent colors
    'accent': '#f59e0b',           # Amber - for highlights
    'accent_light': '#fbbf24',     # Light amber
    'accent_bg': '#fffbeb',        # Light amber background
    
    # Status colors
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'info': '#3b82f6',
    
    # Neutrals
    'gray_50': '#f9fafb',
    'gray_100': '#f3f4f6',
    'gray_200': '#e5e7eb',
    'gray_300': '#d1d5db',
    'gray_400': '#9ca3af',
    'gray_500': '#6b7280',
    'gray_600': '#4b5563',
    'gray_700': '#374151',
    'gray_800': '#1f2937',
    'gray_900': '#111827',
    
    # Functional
    'white': '#ffffff',
    'black': '#000000',
    'card_bg': '#ffffff',
    'page_bg': '#f9fafb',
}

# Typography
TYPOGRAPHY = {
    'font_family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    'heading_font': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    
    # Font sizes
    'h1': '2.5rem',
    'h2': '2rem',
    'h3': '1.5rem',
    'h4': '1.25rem',
    'h5': '1.125rem',
    'h6': '1rem',
    'body': '1rem',
    'small': '0.875rem',
    'caption': '0.75rem',
    
    # Font weights
    'light': 300,
    'regular': 400,
    'medium': 500,
    'semibold': 600,
    'bold': 700,
}

# Spacing system (based on 4px grid)
SPACING = {
    'xs': '4px',
    'sm': '8px',
    'md': '12px',
    'lg': '16px',
    'xl': '20px',
    '2xl': '24px',
    '3xl': '32px',
    '4xl': '40px',
    '5xl': '48px',
}

# Border radius
BORDER_RADIUS = {
    'sm': '4px',
    'md': '8px',
    'lg': '12px',
    'xl': '16px',
    '2xl': '20px',
    'full': '9999px',
}

# Shadows
SHADOWS = {
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    'card': '0 1px 3px rgba(0, 0, 0, 0.08)',
    'card_hover': '0 4px 6px rgba(0, 0, 0, 0.1)',
}

# Chart colors (professional palette)
CHART_COLORS = {
    'primary': '#10b981',
    'secondary': '#3b82f6',
    'tertiary': '#f59e0b',
    'quaternary': '#ef4444',
    'palette': [
        '#10b981',  # Emerald
        '#3b82f6',  # Blue
        '#f59e0b',  # Amber
        '#ef4444',  # Red
        '#8b5cf6',  # Purple
        '#ec4899',  # Pink
        '#14b8a6',  # Teal
        '#f97316',  # Orange
        '#84cc16',  # Lime
        '#06b6d4',  # Cyan
    ],
    'meal_types': {
        'Breakfast': '#f59e0b',  # Amber
        'Lunch': '#3b82f6',      # Blue
        'Dinner': '#10b981',     # Emerald
        'Snack': '#8b5cf6',      # Purple
    }
}

# Animation
ANIMATIONS = {
    'transition_fast': 'all 0.15s ease-in-out',
    'transition_normal': 'all 0.2s ease-in-out',
    'transition_slow': 'all 0.3s ease-in-out',
    'transition_card': 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
}