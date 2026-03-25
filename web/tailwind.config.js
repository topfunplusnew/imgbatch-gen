/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // 确保支持暗色模式
  theme: {
    extend: {
      screens: {
        'xs': '475px',
        '3xl': '1920px',
      },
      spacing: {
        '18': '4.5rem',
        '128': '32rem',
        '22': '5.5rem',
        '4.5': '1.125rem',
        '5.5': '1.375rem',
      },
      colors: {
        // 黑白配色
        "primary": "#000000",
        "primary-strong": "#1a1a1a",
        "primary-deep": "#333333",
        "primary-soft": "#f0f0f0",
        "background-light": "#ffffff",
        "background-dark": "#f5f5f5",
        "surface-dark": "#ffffff",
        "border-dark": "#e0e0e0",
        "ink-950": "#000000",
        "ink-700": "#333333",
        "ink-500": "#666666",
        "ink-300": "#999999",
        // Purple accent colors
        "accent-purple": "#8B5CF6",
        "accent-purple-light": "#A78BFA",
        "accent-purple-dark": "#7C3AED",
      },
      borderRadius: {
        "lg": "0.7rem",
        "xl": "0.9rem",
        "2xl": "1.1rem",
      },
      boxShadow: {
        "lg": "0 18px 40px -28px rgba(16, 19, 18, 0.22)",
        "xl": "0 24px 64px -36px rgba(16, 19, 18, 0.18)",
      },
      fontFamily: {
        "display": ["Public Sans", "sans-serif"]
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'), // 优化输入框样式
  ],
}
