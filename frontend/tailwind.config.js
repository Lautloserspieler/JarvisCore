/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        jarvis: {
          cyan: '#00f0ff',
          blue: '#0088ff',
          dark: '#0a0e27',
          darker: '#050814',
        },
      },
      fontFamily: {
        orbitron: ['Orbitron', 'sans-serif'],
        space: ['Space Grotesk', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite',
      },
      keyframes: {
        glow: {
          '0%, 100%': { boxShadow: '0 0 20px rgba(0, 240, 255, 0.5)' },
          '50%': { boxShadow: '0 0 40px rgba(0, 240, 255, 0.8)' },
        },
      },
    },
  },
  plugins: [],
}
