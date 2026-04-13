import { getEmpresasParaConfig } from "./actions";
import { ConfigForm } from "./components/config-form";

export default async function ParametrosPage() {
  const empresas = await getEmpresasParaConfig()

  return (
    <div className="p-8 h-full flex flex-col space-y-6 max-w-4xl mx-auto w-full">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-texto">Parâmetros do Sistema</h2>
        <p className="text-mutedtext">
          Ajuste as margens, margens de erro e histórico do algoritmo de inteligência de compras.
        </p>
      </div>

      <ConfigForm empresas={empresas} />
    </div>
  );
}
