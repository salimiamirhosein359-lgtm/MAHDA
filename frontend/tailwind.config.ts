import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        vazirmatn: ["Vazirmatn", "Segoe UI", "Tahoma", "sans-serif"],
        serif: ["var(--font-serif)", "Noto Naskh Arabic", "Georgia", "serif"],
      },
      colors: {
        /* Teal-Green palette */
        navy: {
          DEFAULT: "#0a2e36",
          soft: "#0f3d47",
          900: "#0a2e36",
          800: "#0f3d47",
          700: "#1a5462",
        },
        mblue: {
          DEFAULT: "#0ea5a0",
          dark: "#0c8c88",
          600: "#0c8c88",
          500: "#0ea5a0",
          400: "#3dbfbb",
        },
        lblue: {
          DEFAULT: "#7edcd8",
          soft: "#d0f5f3",
          300: "#d0f5f3",
          400: "#7edcd8",
        },
        cgray: {
          DEFAULT: "#e8f0ef",
          soft: "#f3f8f7",
          200: "#f3f8f7",
          300: "#e8f0ef",
        },
        ink: {
          DEFAULT: "#111111",
          dim: "#4a5a5e",
          faint: "#7a8e92",
        },
        rule: "#cddcda",
        mred: "#E52A2A",
      },
    },
  },
  plugins: [],
};

export default config;
