import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { DashboardShell } from "@/components/layout/DashboardShell"
import { AdminNav } from "./components/AdminNav"

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/auth/login')
  }

  // Verifica se o usuário é admin
  const { data: perfil } = await supabase
    .from('perfis')
    .select('isadmin')
    .eq('id', user.id)
    .single()

  if (!perfil?.isadmin) {
    redirect('/home')
  }

  return (
    <DashboardShell isAdmin={true}>
      <div className="p-5 lg:py-8 lg:px-10 max-w-7xl mx-auto w-full">
        <h1 className="text-2xl font-bold text-texto mb-2">Painel de Administração</h1>
        <p className="text-secondary text-sm mb-6">Controle as empresas, acessos e configurações do sistema.</p>
        <AdminNav />
        {children}
      </div>
    </DashboardShell>
  )
}
