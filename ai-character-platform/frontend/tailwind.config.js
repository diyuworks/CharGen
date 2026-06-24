/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      keyframes: {
        shimmer: {
          '0%': { transform: 'translateX(-120%)' },
          '100%': { transform: 'translateX(220%)' },
        },
        'pulse-ring': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(139, 92, 246, 0.35)' },
          '50%': { boxShadow: '0 0 0 6px rgba(139, 92, 246, 0)' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.1s ease-out',
        'pulse-ring': 'pulse-ring 1.8s ease-in-out infinite',
      },
      boxShadow: {
        'glow-violet': '0 0 24px -4px rgba(139, 92, 246, 0.45)',
        'glow-rose': '0 0 24px -4px rgba(244, 63, 94, 0.4)',
        'glow-cyan': '0 0 24px -4px rgba(34, 211, 238, 0.4)',
      },
    },
  },
  plugins: [],
}
