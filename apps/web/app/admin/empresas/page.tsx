import { getEmpresas } from "./actions";
import { EmpresaManager } from "./components/empresa-manager";

export default async function EmpresasPage() {
  const empresas = await getEmpresas();

  return (
    <div className="p-8 h-full flex flex-col space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-texto">Empresas</h2>
        <p className="text-mutedtext">
          Gerencie suas filiais, farmácias e as entidades conectadas ao Compras PRO.
        </p>
      </div>

      <EmpresaManager initialData={empresas} />
    </div>
  );
}
