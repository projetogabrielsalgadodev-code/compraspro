import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { DashboardShell } from "@/components/layout/DashboardShell";

/**
 * Layout de todas as rotas do dashboard.
 * Segunda camada de proteção: verifica sessão server-side.
 * Primeira camada: middleware em lib/supabase/middleware.ts.
 */
export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    // Sessão inválida ou expirada — jogar para login
    redirect("/auth/login");
  }

  // Buscar isadmin do perfil para mostrar link de admin na sidebar
  const { data: perfil } = await supabase
    .from("perfis")
    .select("isadmin")
    .eq("id", user.id)
    .single();

  const isAdmin = perfil?.isadmin === true;

  return <DashboardShell isAdmin={isAdmin}>{children}</DashboardShell>;
}
