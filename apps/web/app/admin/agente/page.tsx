import { AgentSettings } from "./components/agent-settings"
import { getAgentSettings, getAgentMetrics } from "./actions"

export const dynamic = 'force-dynamic'

export default async function AgentePage() {
  const [initialData, metrics] = await Promise.all([
    getAgentSettings(),
    getAgentMetrics(),
  ])

  return (
    <>
      <div className="mb-8">
        <p className="ds-eyebrow mb-0.5">Inteligência Artificial</p>
        <h1 className="text-2xl font-bold tracking-tight text-texto lg:text-3xl">
          Configuração do Agente
        </h1>
        <p className="mt-1 text-sm text-secondary">
          Configure os parâmetros do modelo, instruções de sistema e acompanhe os custos de IA.
        </p>
      </div>

      <AgentSettings initialData={initialData} metrics={metrics} />
    </>
  )
}
