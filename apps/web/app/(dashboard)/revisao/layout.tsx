import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Revisão Manual | Compras PRO",
  description: "Faça a revisão manual das correspondências de produtos com baixa confiança ou não encontrados.",
};

export default function RevisaoLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
