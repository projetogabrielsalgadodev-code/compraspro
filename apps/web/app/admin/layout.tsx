import { redirect } from 'next/navigation'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { DashboardShell } from "@/components/layout/DashboardShell"

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const cookieStore = cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    redirect('/auth/login')
  }

  // Verifica o perfil do usuário para garantir que é admin
  const { data: perfil } = await supabase
    .from('perfis')
    .select('papel')
    .eq('id', user.id)
    .single()

  const isAdmin = perfil?.papel === 'admin'

  if (!isAdmin) {
    redirect('/auth/login?error=Unauthorized')
  }

  return (
    <DashboardShell>
      <div className="p-5 lg:py-8 lg:px-10 max-w-7xl mx-auto w-full">
        {children}
      </div>
    </DashboardShell>
  )
}
