/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        meet: {
          bg: '#202124',
          surface: '#303134',
          surfaceLight: '#3c4043',
          border: '#4a4d51',
          text: '#e8eaed',
          textMuted: '#9aa0a6',
          primary: '#8ab4f8',
          primaryHover: '#aecbfa',
          blue: '#1a73e8',
          red: '#ea4335',
          redHover: '#d93025',
          green: '#34a853',
          yellow: '#fbbc04',
          activeSpeaker: '#8ab4f8'
        }
      },
      fontFamily: {
        sans: ['"Google Sans"', 'Inter', 'Roboto', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'meet-bar': '0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15)',
        'meet-tile': '0 1px 2px 0 rgba(0,0,0,0.3)',
      },
      animation: {
        'pulse-subtle': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
