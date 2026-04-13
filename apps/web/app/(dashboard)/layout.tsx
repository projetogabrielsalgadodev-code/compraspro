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

  return <DashboardShell>{children}</DashboardShell>;
}
