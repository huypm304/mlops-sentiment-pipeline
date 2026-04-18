/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // Dòng này cực quan trọng để hết lỗi warn
  ],
  darkMode: 'class',
  theme: {
    extend: {},
  },
  plugins: [],
}