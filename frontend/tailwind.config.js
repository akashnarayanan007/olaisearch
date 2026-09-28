/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Noto Serif"', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      colors: {
        palm: {
          50: '#faf6f0',
          100: '#f3ebe0',
          200: '#e8d5c0',
          300: '#d4b596',
          400: '#c09168',
          500: '#a87348',
          600: '#8b5a36',
          700: '#6d452b',
          800: '#5a3a27',
          900: '#4a3022',
          950: '#271a10',
        },
        ink: {
          50: '#f6f6f7',
          100: '#e7e8ea',
          200: '#d0d2d7',
          300: '#afb3bc',
          400: '#868c9b',
          500: '#6b7280',
          600: '#4f5766',
          700: '#3d4554',
          800: '#323846',
          900: '#2a2f3a',
          950: '#13161c',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
