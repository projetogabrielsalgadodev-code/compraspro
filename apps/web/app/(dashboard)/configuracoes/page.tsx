import type { Metadata } from "next";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { ConfiguracoesEmpresaForm } from "@/components/configuracoes/ConfiguracoesEmpresaForm";

export const metadata: Metadata = { title: "Configurações" };

export default function ConfiguracoesPage() {
  return (
    <DashboardPage titulo="Configurações" subtitulo="Ajuste regras operacionais e parâmetros que alimentam a análise de ofertas." eyebrow="Governança">
      <ConfiguracoesEmpresaForm />
    </DashboardPage>
  );
}
