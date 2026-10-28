import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        vazirmatn: ["Vazirmatn", "Tahoma", "sans-serif"],
      },
      colors: {
        base: {
          900: "#0a0f1e",
          800: "#0f1629",
          700: "#151d35",
          600: "#1c2745",
          500: "#2a3a63",
        },
        accent: {
          500: "#7c5cff",
          400: "#9b82ff",
          300: "#b8a4ff",
        },
        cyan: {
          500: "#22d3ee",
        },
      },
    },
  },
  plugins: [],
};

export default config;
