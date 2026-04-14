"use client"

import { useState } from "react"
import { useToast } from "@/hooks/use-toast"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Slider } from "@/components/ui/slider"
import { Bot, Save, Loader2, Coins, Zap, CircleDollarSign, Fingerprint, Activity, AlertTriangle, CheckCircle2, Clock } from "lucide-react"
import { updateAgentSettings } from "../actions"

interface Metrics {
  total_analises: number
  analises_concluidas: number
  analises_erro: number
  total_tokens: number
  custo_total_reais: number
  tempo_medio_ms: number
  ultima_analise: string | null
}

interface Props {
  initialData?: any
  metrics?: Metrics | null
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M"
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K"
  return n.toString()
}

function formatTime(ms: number): string {
  if (ms >= 60_000) return (ms / 60_000).toFixed(1) + "min"
  if (ms >= 1_000) return (ms / 1_000).toFixed(1) + "s"
  return ms + "ms"
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "Nenhuma"
  const d = new Date(dateStr)
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" })
}

export function AgentSettings({ initialData, metrics }: Props) {
  const { toast } = useToast()
  const [isSaving, setIsSaving] = useState(false)

  const [temperature, setTemperature] = useState([initialData?.temperatura ? parseFloat(initialData.temperatura) : 0.7])
  const [maxTokens, setMaxTokens] = useState(initialData?.max_tokens?.toString() || "16384")
  const [systemPrompt, setSystemPrompt] = useState(
    initialData?.prompt_sistema || ""
  )

  const modeloAtual = initialData?.modelo || "claude-sonnet-4-5-20250929"

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    
    const formData = new FormData()
    if (initialData?.id) formData.append("id", initialData.id)
    formData.append("model", modeloAtual)
    formData.append("temperature", temperature[0].toString())
    formData.append("maxTokens", maxTokens)
    formData.append("systemPrompt", systemPrompt)

    const res = await updateAgentSettings(formData)
    
    setIsSaving(false)
    if (res.error) {
      toast({ variant: "destructive", title: "Erro", description: res.error })
    } else {
      toast({ title: "Configurações salvas", description: res.success })
    }
  }

  // Dados reais de métricas
  const m = metrics || {
    total_analises: 0,
    analises_concluidas: 0,
    analises_erro: 0,
    total_tokens: 0,
    custo_total_reais: 0,
    tempo_medio_ms: 0,
    ultima_analise: null,
  }

  const taxaSucesso = m.total_analises > 0
    ? Math.round((m.analises_concluidas / m.total_analises) * 100)
    : 0

  return (
    <form className="grid gap-6 lg:grid-cols-3" onSubmit={handleSave}>
      {/* Coluna Esquerda: Configurações e Prompt */}
      <div className="lg:col-span-2 space-y-6">
        
        {/* Card de Configuração do Modelo */}
        <section className="surface-card rounded-[20px] p-6 soft-stroke pb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,rgb(var(--accent-primary)/0.2),rgb(var(--accent-tertiary)/0.12))] text-primariaapp">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-texto leading-none mb-1">Parâmetros do Modelo (Agno)</h2>
              <p className="text-sm text-secondary">Defina o comportamento do agente inteligente.</p>
            </div>
          </div>

          {/* Info do modelo atual (readonly) */}
          <div className="bg-[var(--surface-highlight)] rounded-xl p-4 mb-6 flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-primariaapp/10 flex items-center justify-center shrink-0">
              <Zap className="h-4 w-4 text-primariaapp" />
            </div>
            <div>
              <p className="text-xs text-secondary">Modelo Ativo (definido no código)</p>
              <p className="text-sm font-semibold text-texto font-mono">{modeloAtual}</p>
            </div>
          </div>

          <div className="grid gap-6">
            <div className="space-y-3">
              <Label htmlFor="max-tokens" className="text-sm font-medium">Máx. Tokens Renderizados</Label>
              <Input 
                id="max-tokens" 
                type="number" 
                value={maxTokens}
                onChange={(e) => setMaxTokens(e.target.value)}
                className="bg-input-app border-app/50 max-w-xs" 
              />
            </div>

            <div className="space-y-4 pt-2">
              <div className="flex justify-between items-center">
                <Label className="text-sm font-medium">Temperatura: <span className="text-primariaapp font-semibold">{temperature[0]}</span></Label>
                <span className="text-xs text-secondary">{temperature[0] < 0.5 ? "Mais Preciso" : temperature[0] > 0.8 ? "Mais Criativo" : "Equilibrado"}</span>
              </div>
              <Slider
                value={temperature}
                onValueChange={setTemperature}
                max={2}
                step={0.1}
                className="py-2"
              />
            </div>
          </div>
        </section>

        {/* Card do Prompt de Sistema */}
        <section className="surface-card rounded-[20px] p-6 soft-stroke">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,rgb(var(--accent-secondary)/0.15),rgb(var(--accent-secondary)/0.05))] text-secondaryaccent">
              <Fingerprint className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-texto leading-none mb-1">Prompt de Sistema</h2>
              <p className="text-sm text-secondary">A instrução basal do agente em todo o aplicativo.</p>
            </div>
          </div>

          <div className="space-y-4">
            <Textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className="min-h-[220px] bg-input-app border-app/50 resize-y leading-relaxed"
              placeholder="Digite as instruções de comportamento do agente..."
            />
            <div className="flex justify-end pt-2">
              <Button
                type="submit"
                disabled={isSaving}
                className="bg-[linear-gradient(135deg,rgb(var(--accent-primary)),rgb(var(--accent-secondary)))] text-white font-semibold shadow-[0_8px_24px_rgba(36,76,255,0.28)] hover:shadow-[0_12px_32px_rgba(36,76,255,0.36)] transition-all hover:-translate-y-0.5 px-6"
              >
                {isSaving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                {isSaving ? "Salvando..." : "Salvar Configurações"}
              </Button>
            </div>
          </div>
        </section>
      </div>

      {/* Coluna Direita: Custos REAIS e Stats */}
      <div className="space-y-6">
        
        {/* Painel de Custos REAIS */}
        <section className="surface-card rounded-[20px] p-6 soft-stroke">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,rgb(var(--accent-tertiary)/0.2),transparent)] text-[rgb(var(--accent-tertiary))]">
              <CircleDollarSign className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-texto leading-none mb-1">Custos Reais</h2>
              <p className="text-sm text-secondary">Dados do banco de dados.</p>
            </div>
          </div>

          <div className="flex flex-col gap-5">
             <div className="bg-input-app/50 rounded-2xl p-5 border border-app border-dashed flex items-center justify-between">
                <div>
                   <p className="ds-eyebrow mb-1">Custo Total (Acumulado)</p>
                   <p className="text-3xl font-bold text-texto">R$ {m.custo_total_reais.toFixed(2)}</p>
                </div>
                <div className="h-10 w-10 rounded-full bg-emerald-500/10 flex items-center justify-center">
                   <Coins className="h-5 w-5 text-emerald-500" />
                </div>
             </div>

             <div className="grid grid-cols-2 gap-3">
                <div className="bg-[var(--surface-highlight)] rounded-xl p-4">
                   <p className="text-[11px] font-semibold tracking-wider text-secondary uppercase mb-1">Tokens Usados</p>
                   <p className="text-lg font-bold text-texto">{formatNumber(m.total_tokens)}</p>
                </div>
                <div className="bg-[var(--surface-highlight)] rounded-xl p-4">
                   <p className="text-[11px] font-semibold tracking-wider text-secondary uppercase mb-1">Tempo Médio</p>
                   <p className="text-lg font-bold text-texto">{formatTime(m.tempo_medio_ms)}</p>
                </div>
             </div>
          </div>
        </section>

        {/* Status de Uso Real */}
        <section className="surface-card rounded-[20px] p-6 soft-stroke">
          <div className="flex items-center gap-3 mb-5">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[linear-gradient(135deg,rgb(var(--accent-primary)/0.12),transparent)] text-primariaapp">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-texto leading-none mb-1">Análises Realizadas</h2>
              <p className="text-sm text-secondary">Dados reais do Agno.</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-app/30">
              <span className="text-sm text-secondary flex items-center gap-2">
                <Activity className="h-3.5 w-3.5" /> Total
              </span>
              <span className="text-sm font-semibold text-texto">{m.total_analises}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-app/30">
              <span className="text-sm text-secondary flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Concluídas
              </span>
              <span className="text-sm font-semibold text-emerald-500">{m.analises_concluidas}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-app/30">
              <span className="text-sm text-secondary flex items-center gap-2">
                <AlertTriangle className="h-3.5 w-3.5 text-amber-500" /> Com Erro
              </span>
              <span className="text-sm font-semibold text-amber-500">{m.analises_erro}</span>
            </div>
            <div className="flex items-center justify-between py-2 border-b border-app/30">
              <span className="text-sm text-secondary flex items-center gap-2">
                <Zap className="h-3.5 w-3.5" /> Taxa de Sucesso
              </span>
              <span className="text-sm font-semibold text-texto">{taxaSucesso}%</span>
            </div>
            <div className="flex items-center justify-between py-2">
              <span className="text-sm text-secondary flex items-center gap-2">
                <Clock className="h-3.5 w-3.5" /> Última Análise
              </span>
              <span className="text-xs font-medium text-texto">{formatDate(m.ultima_analise)}</span>
            </div>
          </div>
        </section>

        {/* Status do Serviço */}
        <section className="surface-card rounded-[20px] p-6 soft-stroke">
           <div className="flex items-start justify-between">
              <div>
                 <p className="font-semibold text-texto mb-1">Status do Serviço</p>
                 <p className="text-sm text-secondary">
                   Modelo: <span className="font-mono text-xs text-texto">{modeloAtual}</span>
                 </p>
                 <p className="text-sm text-secondary mt-1">
                   Provider: <span className="font-semibold text-texto">Anthropic (Claude)</span>
                 </p>
              </div>
              <div className="h-8 w-8 rounded-full bg-emerald-500/10 flex items-center justify-center shrink-0">
                 <Zap className="h-4 w-4 text-emerald-500 fill-emerald-500/20" />
              </div>
           </div>
        </section>

      </div>
    </form>
  )
}
