import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        duo: {
          green: "#58cc02",
          "green-dark": "#46a302",
          "green-light": "#89e219",
          red: "#ff4b4b",
          "red-dark": "#ea2b2b",
          "red-light": "#ff7878",
          blue: "#1cb0f6",
          "blue-dark": "#1899d6",
          orange: "#ff9600",
          "orange-dark": "#e08500",
          yellow: "#ffc800",
          "yellow-dark": "#e5a400",
          gray: {
            100: "#f7f7f7",
            200: "#e5e5e5",
            300: "#afafaf",
            700: "#4b4b4b",
            900: "#1f1f1f",
          },
        },
      },
      fontFamily: {
        nunito: ["var(--font-nunito)", "Nunito", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
