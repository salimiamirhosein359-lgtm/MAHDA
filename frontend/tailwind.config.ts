import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        vazirmatn: ["Vazirmatn", "Segoe UI", "Tahoma", "sans-serif"],
        serif: ["Vazirmatn", "Segoe UI", "Tahoma", "sans-serif"],
      },
      colors: {
        /* Deep ocean teal — hero / footer / strong text */
        navy: {
          DEFAULT: "#082F3A",
          soft: "#0B4150",
          900: "#082F3A",
          800: "#0B4150",
          700: "#11596B",
        },
        /* Turquoise-blue — primary accent */
        mblue: {
          DEFAULT: "#0E9AA7",
          dark: "#0A7F8A",
          600: "#0A7F8A",
          500: "#0E9AA7",
          400: "#2DB8C4",
        },
        lblue: {
          DEFAULT: "#7FD8DE",
          soft: "#D7F3F5",
          300: "#D7F3F5",
          400: "#7FD8DE",
        },
        cgray: {
          DEFAULT: "#E6EFF1",
          soft: "#F3F8F9",
          200: "#F3F8F9",
          300: "#E6EFF1",
        },
        ink: {
          DEFAULT: "#0F1F26",
          dim: "#4B5F67",
          faint: "#7C909A",
        },
        rule: "#DCE7EA",
        mred: "#E5484D",
      },
      boxShadow: {
        card: "0 1px 2px rgba(8,47,58,0.05), 0 4px 16px rgba(8,47,58,0.06)",
        lift: "0 2px 4px rgba(8,47,58,0.06), 0 12px 32px rgba(14,154,167,0.16)",
        search: "0 8px 40px rgba(8,47,58,0.22)",
      },
    },
  },
  plugins: [],
};

export default config;
