import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/toaster";
import "./globals.css";

/* C-05: Importação de Inter via next/font/google para garantir carregamento */
const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

/* C-25: Meta description melhorada com acentos e og:tags */
export const metadata: Metadata = {
  title: {
    default: "Compras PRO",
    template: "%s | Compras PRO",
  },
  description: "Inteligência de compras para farmácias — análise automatizada de ofertas, histórico de preços e sugestões de pedido.",
  openGraph: {
    title: "Compras PRO",
    description: "Inteligência de compras para farmácias — análise automatizada de ofertas, histórico de preços e sugestões de pedido.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR" className={inter.variable} suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider>
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  );
}
