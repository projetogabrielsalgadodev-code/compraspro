import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Detalhe do Item | Compras PRO",
  description: "Análise detalhada do item com histórico de preços, cobertura de estoque e recomendação de compra.",
};

export default function ItemLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
