"use client"

import { useState } from "react"
import { Settings2, Building2, User } from "lucide-react"
import { ConfiguracoesEmpresaForm } from "@/components/configuracoes/ConfiguracoesEmpresaForm"
import { EmpresaForm } from "@/components/configuracoes/EmpresaForm"
import { PerfilForm } from "@/components/configuracoes/PerfilForm"

interface EmpresaData {
  id: string
  nome: string
  cnpj: string | null
  razao_social: string | null
  telefone: string | null
  email: string | null
  endereco: string | null
}

interface PerfilData {
  id: string
  nome: string | null
  email: string | null
  telefone: string | null
  avatar_url: string | null
  papel: string
}

interface UsageStats {
  total_analises: number
  total_tokens: number
  total_custo: number
}

const TABS = [
  { id: "parametros", label: "Parâmetros", icon: Settings2 },
  { id: "empresa", label: "Empresa", icon: Building2 },
  { id: "perfil", label: "Perfil", icon: User },
] as const

type TabId = typeof TABS[number]["id"]

export function ConfiguracoesTabs({
  empresa,
  perfil,
  usageStats,
}: {
  empresa: EmpresaData | null
  perfil: PerfilData | null
  usageStats?: UsageStats
}) {
  const [activeTab, setActiveTab] = useState<TabId>("parametros")

  return (
    <div className="space-y-6">
      {/* Tab navigation */}
      <div className="flex gap-1 rounded-2xl bg-[rgb(var(--bg-surface-section))] p-1">
        {TABS.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? "bg-white text-texto shadow-sm dark:bg-[rgb(var(--bg-card))]"
                  : "text-secondary hover:text-texto"
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab content */}
      {activeTab === "parametros" && <ConfiguracoesEmpresaForm />}
      {activeTab === "empresa" && empresa && <EmpresaForm empresa={empresa} />}
      {activeTab === "empresa" && !empresa && (
        <div className="ds-subpanel rounded-2xl p-6 text-center text-secondary">
          Nenhuma empresa vinculada ao seu perfil.
        </div>
      )}
      {activeTab === "perfil" && perfil && <PerfilForm perfil={perfil} usageStats={usageStats} />}
      {activeTab === "perfil" && !perfil && (
        <div className="ds-subpanel rounded-2xl p-6 text-center text-secondary">
          Perfil não encontrado.
        </div>
      )}
    </div>
  )
}

