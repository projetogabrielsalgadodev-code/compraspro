import { redirect } from 'next/navigation'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import Link from 'next/link'
import { Building2, Users, Settings, LogOut } from 'lucide-react'

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
    // Redireciona para o login ou uma tela sem permissão, vamos deslogar por segurança
    redirect('/auth/login?error=Unauthorized')
  }

  return (
    <div className="flex h-screen bg-fundo overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-sidebarapp border-r border-borderapp flex flex-col items-stretch">
        <div className="h-16 flex items-center border-b border-borderapp px-6 space-x-2">
          <div className="h-8 w-8 bg-primaria rounded-lg flex items-center justify-center shadow-primario">
            <span className="text-white font-bold tracking-wider text-xs">CP</span>
          </div>
          <span className="text-lg font-bold text-texto">Compras PRO</span>
        </div>

        <div className="p-4 flex-1 space-y-1">
          <div className="text-xs font-semibold text-mutedtext uppercase tracking-wider mb-2 ml-2">
            Administração
          </div>
          <Link href="/admin/empresas" className="flex items-center space-x-3 text-secondarytext hover:text-primaria hover:bg-primaria/10 px-3 py-2 rounded-lg transition-colors">
            <Building2 className="w-5 h-5" />
            <span className="font-medium">Empresas</span>
          </Link>
          <Link href="/admin/usuarios" className="flex items-center space-x-3 text-secondarytext hover:text-primaria hover:bg-primaria/10 px-3 py-2 rounded-lg transition-colors">
            <Users className="w-5 h-5" />
            <span className="font-medium">Usuários</span>
          </Link>
          <Link href="/admin/parametros" className="flex items-center space-x-3 text-secondarytext hover:text-primaria hover:bg-primaria/10 px-3 py-2 rounded-lg transition-colors">
            <Settings className="w-5 h-5" />
            <span className="font-medium">Parâmetros</span>
          </Link>
        </div>

        <div className="p-4 border-t border-borderapp">
          <div className="mb-4">
             <div className="text-sm font-medium text-texto truncate">{user.email}</div>
             <div className="text-xs text-mutedtext">Administrador</div>
          </div>
          <form action="/auth/logout" method="post">
            <button type="submit" className="w-full flex items-center space-x-3 text-descartavel hover:bg-descartavel-claro/50 px-3 py-2 rounded-lg transition-colors">
              <LogOut className="w-5 h-5" />
              <span className="font-medium">Sair</span>
            </button>
          </form>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-y-auto">
        {/* Simple top header */}
        <header className="h-16 flex items-center bg-fundo border-b border-borderapp px-8">
           <h1 className="text-xl font-semibold text-texto">Painel de Controle</h1>
        </header>

        {children}
      </main>
    </div>
  )
}
