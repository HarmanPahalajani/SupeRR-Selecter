/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        rr: {
          pink: "#E50695",         // Official Vibrant Rajasthan Royals Pink
          darkpink: "#C30B99",     // Deep Magenta-Pink
          hoverpink: "#D20588",    // Button Hover State
          blush: "#FDF2F8",        // Light Blush Secondary Surface (pink-50)
          blushcard: "#FFF5FA",    // Subtle Card Tint
          blushborder: "#FCE7F3",  // Blush Border (pink-100)
          navy: "#001C58",         // Official Deep Royal Navy
          navydark: "#0A1128",     // Dark Navy Contrast
          navylight: "#0E296D",    // Medium Royal Blue
          purple: "#3920A6",       // Restrained Royal Purple Accent
          purplelight: "#5A3ED8",  // Light Purple Accent
        },
        slate: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
          900: "#0F172A",
        }
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif"
        ],
        mono: [
          "JetBrains Mono",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace"
        ],
      },
      boxShadow: {
        'rr-subtle': '0 1px 3px 0 rgba(0, 28, 88, 0.04), 0 1px 2px -1px rgba(0, 28, 88, 0.04)',
        'rr-card': '0 4px 6px -1px rgba(0, 28, 88, 0.05), 0 2px 4px -2px rgba(0, 28, 88, 0.05)',
        'rr-elevated': '0 10px 15px -3px rgba(0, 28, 88, 0.08), 0 4px 6px -4px rgba(0, 28, 88, 0.04)',
        'rr-pink-glow': '0 0 15px -3px rgba(229, 6, 149, 0.25)',
      }
    },
  },
  plugins: [],
};
