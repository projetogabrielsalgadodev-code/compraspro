import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { DashboardShell } from "@/components/layout/DashboardShell"

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
        {children}
      </div>
    </DashboardShell>
  )
}
