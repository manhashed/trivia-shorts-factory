/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        kid: {
          blue: '#38bdf8',
          yellow: '#facc15',
          green: '#4ade80',
          coral: '#fb7185',
          purple: '#c084fc',
        }
      },
      fontFamily: {
        sans: ['"Fredoka"', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
