import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        /* Tokens semânticos de superfície */
        fundo: "rgb(var(--bg-app) / <alpha-value>)",
        texto: "rgb(var(--text-primary) / <alpha-value>)",
        card: "rgb(var(--bg-card) / <alpha-value>)",
        cardstrong: "rgb(var(--bg-card-strong) / <alpha-value>)",
        inputapp: "rgb(var(--bg-input) / <alpha-value>)",
        sidebarapp: "rgb(var(--bg-sidebar) / <alpha-value>)",
        /* Tokens semânticos de texto */
        secondarytext: "rgb(var(--text-secondary) / <alpha-value>)",
        mutedtext: "rgb(var(--text-muted) / <alpha-value>)",
        /* Tokens semânticos de borda */
        borderapp: "rgb(var(--border-soft) / <alpha-value>)",
        /* Tokens de acento */
        primaria: "rgb(var(--accent-primary) / <alpha-value>)",
        primary: "rgb(var(--accent-primary) / <alpha-value>)",
        secondaryaccent: "rgb(var(--accent-secondary) / <alpha-value>)",
        tertiaryaccent: "rgb(var(--accent-tertiary) / <alpha-value>)",
        primariaapp: { DEFAULT: "rgb(var(--accent-primary) / <alpha-value>)", claro: "#EFF6FF" },
        /* Tokens de status — alinhados com design system.md */
        ouro: { DEFAULT: "#16A34A", claro: "#DCFCE7", borda: "#86EFAC" },
        prata: { DEFAULT: "#D97706", claro: "#FEF3C7", borda: "#FCD34D" },
        atencao: { DEFAULT: "#D97706", claro: "#FFF7ED", borda: "#FDBA74" },
        descartavel: { DEFAULT: "#DC2626", claro: "#FEE2E2", borda: "#FCA5A5" },
        sucesso: { DEFAULT: "#10B981", claro: "#ECFDF5" },
        /* C-04: Tokens de ação do design system */
        "action-primary": "rgb(var(--accent-primary) / <alpha-value>)",
        "action-secondary": "rgb(var(--accent-secondary) / <alpha-value>)",
        "status-success": "#10B981",
        "status-warning": "#D97706",
        "status-error": "#DC2626",
      },
      boxShadow: {
        cartao: "var(--shadow-card)",
        "cartao-hover": "var(--shadow-card-hover)",
        primario: "0 0 0 1px rgb(var(--accent-primary) / 0.18), 0 12px 32px rgb(var(--accent-primary-glow) / 0.85)"
      },
      borderRadius: {
        xl2: "1.5rem"
      },
      /* C-10: ring-offset precisa saber a cor de fundo para contraste WCAG */
      ringOffsetColor: {
        fundo: "rgb(var(--bg-app))",
      }
    }
  },
  plugins: []
};

export default config;
