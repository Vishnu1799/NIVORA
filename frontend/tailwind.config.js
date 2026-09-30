/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        nivora: {
          green: '#22c55e',
          dark: '#15803d',
          light: '#f0fdf4',
        },
        aurev: {
          blue: '#3b82f6',
          dark: '#1d4ed8',
          glow: '#93c5fd',
        }
      }
    },
  },
  plugins: [],
}
