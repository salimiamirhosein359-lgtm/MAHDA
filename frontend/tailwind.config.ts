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
        /* McKinsey & Company palette */
        navy: {
          DEFAULT: "#051C2C",
          soft: "#0B2B42",
          900: "#051C2C",
          800: "#0B2B42",
          700: "#14415E",
        },
        mblue: {
          DEFAULT: "#2251FF",
          dark: "#1A3FD6",
          600: "#1A3FD6",
          500: "#2251FF",
          400: "#5C7DFF",
        },
        lblue: {
          DEFAULT: "#A7C5FF",
          soft: "#D0DEFF",
          300: "#D0DEFF",
          400: "#A7C5FF",
        },
        cgray: {
          DEFAULT: "#E6E6E6",
          soft: "#F5F5F5",
          200: "#F5F5F5",
          300: "#E6E6E6",
        },
        ink: {
          DEFAULT: "#111111",
          dim: "#565656",
          faint: "#8A8A8A",
        },
        rule: "#D9D9D9",
        mred: "#E52A2A",
      },
      letterSpacing: {
        tightest: "-0.02em",
      },
    },
  },
  plugins: [],
};

export default config;
