/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cal: {
          bg: "#ffffff",
          surface: "#f8fafd",
          border: "#dadce0",
          blue: "#1a73e8",
          blueHover: "#1557b0",
          text: "#3c4043",
          textMuted: "#70757a",
          darkBg: "#202124",
          darkSurface: "#303134",
          darkBorder: "#5f6368",
        }
      }
    },
  },
  plugins: [],
}
