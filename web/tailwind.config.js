/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // 确保支持暗色模式
  theme: {
    extend: {
      colors: {
        // 复刻设计稿中的 UI 颜色
        "primary": "#00DC82",
        "primary-strong": "#00B86B",
        "primary-deep": "#00995A",
        "primary-soft": "#EAFBF3",
        "background-light": "#ffffff",
        "background-dark": "#f5f7f4",
        "surface-dark": "#ffffff",
        "border-dark": "#e2e8e3",
        "ink-950": "#101312",
        "ink-700": "#3b4540",
        "ink-500": "#69736e",
        "ink-300": "#aeb8b2",
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
