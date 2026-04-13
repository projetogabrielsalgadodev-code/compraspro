import type { Metadata } from "next";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { NovaOfertaForm } from "@/components/oferta/NovaOfertaForm";

export const metadata: Metadata = { title: "Nova Análise" };

export default function NovaOfertaPage() {
  return (
    <DashboardPage titulo="Nova analise" subtitulo="Cole texto, adicione a base do cliente e inicie a analise completa." eyebrow="Entrada operacional">
      <NovaOfertaForm />
    </DashboardPage>
  );
}
