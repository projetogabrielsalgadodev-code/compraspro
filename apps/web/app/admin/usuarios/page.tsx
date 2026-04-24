import { getUsers, getEmpresasList, getEmpresaById, getUsersUsageStats } from './actions'
import { UserManager } from './components/user-manager'
import { Building2, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export const dynamic = 'force-dynamic'

export default async function UsuariosPage({
  searchParams,
}: {
  searchParams: { empresa_id?: string }
}) {
  const empresaId = searchParams.empresa_id
  const [users, empresas, empresaFiltrada, usageStats] = await Promise.all([
    getUsers(empresaId),
    getEmpresasList(),
    empresaId ? getEmpresaById(empresaId) : null,
    getUsersUsageStats(),
  ])

  return (
    <>
      {empresaFiltrada && (
        <div className="mb-8">
          <Link
            href="/admin/empresas"
            className="inline-flex items-center gap-1.5 text-sm text-secondary hover:text-primariaapp transition-colors mb-3"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Voltar para Empresas
          </Link>
          <div className="flex items-center gap-3 mb-2">
            <div className="ds-icon-chip h-10 w-10">
              <Building2 className="h-4 w-4 text-primariaapp" />
            </div>
            <div>
              <p className="ds-eyebrow mb-0.5">Usuários de</p>
              <h1 className="text-2xl font-bold tracking-tight text-texto lg:text-3xl">
                {empresaFiltrada.nome}
              </h1>
            </div>
          </div>
          <p className="mt-1 text-sm text-secondary">
            Gerencie os membros vinculados a esta empresa.
          </p>
        </div>
      )}

      <UserManager
        initialUsers={users}
        empresas={empresas}
        empresaIdFilter={empresaId}
        usageStats={usageStats}
      />
    </>
  )
}
