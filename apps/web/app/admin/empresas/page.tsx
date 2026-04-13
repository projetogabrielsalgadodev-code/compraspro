import { getEmpresas } from './actions'
import { EmpresaManager } from './components/empresa-manager'

export const dynamic = 'force-dynamic'

export default async function EmpresasPage() {
  const empresas = await getEmpresas()

  return (
    <>
      <div className="mb-8">
        <p className="ds-eyebrow mb-2">Administração</p>
        <h1 className="text-2xl font-bold tracking-tight text-texto lg:text-3xl">Empresas</h1>
        <p className="mt-1 text-sm text-secondary">
          Gerencie as empresas e filiais cadastradas na plataforma.
        </p>
      </div>

      <EmpresaManager initialData={empresas} />
    </>
  )
}
