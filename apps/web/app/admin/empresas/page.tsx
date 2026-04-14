import { getEmpresas } from './actions'
import { EmpresaManager } from './components/empresa-manager'

export const dynamic = 'force-dynamic'

export default async function EmpresasPage() {
  const empresas = await getEmpresas()

  return (
    <>
      <EmpresaManager initialData={empresas} />
    </>
  )
}
