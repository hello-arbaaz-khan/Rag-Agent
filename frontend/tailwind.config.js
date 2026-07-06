export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"]
      },
      colors: {
        brand: {
          blue: "#1E40AF",
          purple: "#7C3AED",
          bg: "#111827",
          card: "#1F2937"
        }
      },
      boxShadow: {
        soft: "0 18px 60px rgba(0, 0, 0, 0.22)"
      }
    }
  },
  plugins: []
};
