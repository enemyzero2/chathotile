/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
      song: ['SimSun', 'STSong', '宋体', 'serif'],
      },
    },
  },
  plugins: [],
}

