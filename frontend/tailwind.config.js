/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // A considered palette, not Tailwind's default indigo/gray --
        // cool neutrals for structure, a deep forest/teal accent for
        // primary actions rather than the generic SaaS-indigo default.
        ink: {
          900: '#14171F',
          700: '#3A3F4B',
          500: '#5B6270',
          300: '#9AA1AF',
          100: '#E4E6EB',
        },
        canvas: {
          DEFAULT: '#F7F8FA',
          card: '#FFFFFF',
        },
        brand: {
          700: '#0B5D4F',
          600: '#0F7A66',
          500: '#159B80',
          100: '#DCF3ED',
        },
        amber: {
          600: '#B45309',
          100: '#FEF3C7',
        },
        rose: {
          600: '#B91C1C',
          100: '#FEE2E2',
        },
      },
      fontFamily: {
        sans: [
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
