/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: "#09090b",
          panel: "#111113",
          raised: "#18181b",
          border: "#27272a",
        },
        accent: {
          DEFAULT: "#22d3ee",
          dim: "#0e7490",
        },
      },
    },
  },
  plugins: [],
};
