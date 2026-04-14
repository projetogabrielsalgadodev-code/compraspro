import type { Metadata } from "next";
import { cookies } from "next/headers";
import { createServerClient } from "@supabase/ssr";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { ConfiguracoesTabs } from "@/components/configuracoes/ConfiguracoesTabs";

export const metadata: Metadata = { title: "Configurações" };

export default async function ConfiguracoesPage() {
  const cookieStore = await cookies();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll() {}
      },
    }
  );

  const { data: { user } } = await supabase.auth.getUser();

  let empresa = null;
  let perfil = null;

  if (user) {
    // Buscar perfil com empresa vinculada
    const { data: perfilData } = await supabase
      .from("perfis")
      .select("id, nome, email, telefone, avatar_url, papel, empresa_id, empresas(id, nome, cnpj, razao_social, telefone, email, endereco)")
      .eq("id", user.id)
      .single();

    if (perfilData) {
      perfil = {
        id: perfilData.id,
        nome: perfilData.nome,
        email: perfilData.email,
        telefone: perfilData.telefone,
        avatar_url: perfilData.avatar_url,
        papel: perfilData.papel,
      };

      // empresas vem como objeto (relação 1:1 via FK)
      const emp = perfilData.empresas as any;
      if (emp) {
        empresa = {
          id: emp.id,
          nome: emp.nome,
          cnpj: emp.cnpj,
          razao_social: emp.razao_social,
          telefone: emp.telefone,
          email: emp.email,
          endereco: emp.endereco,
        };
      }
    }
  }

  return (
    <DashboardPage titulo="Configurações" subtitulo="Ajuste regras operacionais, dados da empresa e seu perfil." eyebrow="Governança">
      <ConfiguracoesTabs empresa={empresa} perfil={perfil} />
    </DashboardPage>
  );
}
