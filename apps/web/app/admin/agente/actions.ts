"use server"

import { cookies } from "next/headers"
import { createServerClient } from "@supabase/ssr"
import { revalidatePath } from "next/cache"
import { supabaseAdmin } from "@/lib/supabase/admin"

const getSupabase = async () => {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll() {} 
      },
    }
  )
}

export async function getAgentSettings() {
  const supabase = await getSupabase()

  const { data, error } = await supabase
    .from("parametros_agente")
    .select("*")
    .limit(1)
    .single()

  if (error && error.code !== 'PGRST116') {
    console.error("Erro ao carregar configurações do agente:", error)
  }

  return data
}

export async function updateAgentSettings(formData: FormData) {
  const supabase = await getSupabase()

  // Verify auth again
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { error: "Não autenticado." }

  const verifyAdmin = await supabase.from('perfis').select('isadmin').eq('id', user.id).single()
  if (!verifyAdmin.data?.isadmin) return { error: "Sem permissão." }

  const id = formData.get("id") as string
  const model = formData.get("model") as string
  const temperature = parseFloat(formData.get("temperature") as string)
  const maxTokens = parseInt(formData.get("maxTokens") as string, 10)
  const systemPrompt = formData.get("systemPrompt") as string

  if (!model || !systemPrompt) return { error: "Parâmetros inválidos." }

  const updatePayload = {
    modelo: model,
    temperatura: isNaN(temperature) ? 0.7 : temperature,
    max_tokens: isNaN(maxTokens) ? 4000 : maxTokens,
    prompt_sistema: systemPrompt,
    updated_at: new Date().toISOString()
  }

  let error;
  if (id) {
    // Update existing
    const res = await supabaseAdmin
      .from("parametros_agente")
      .update(updatePayload)
      .eq("id", id)
    error = res.error
  } else {
    // Insert new
    const res = await supabaseAdmin
      .from("parametros_agente")
      .insert(updatePayload)
    error = res.error
  }

  if (error) {
    return { error: "Erro ao salvar as configurações: " + error.message }
  }

  revalidatePath("/admin/agente")
  return { success: "Configurações atualizadas." }
}

export async function getAgentMetrics() {
  // Busca métricas REAIS da tabela analises_oferta (onde o Agno salva resultados)
  const { data: analises, error } = await supabaseAdmin
    .from("analises_oferta")
    .select("status, tokens_utilizados, custo_reais, tempo_processamento_ms, created_at")
    .order("created_at", { ascending: false })

  if (error) {
    console.error("Erro ao buscar métricas:", error)
    return null
  }

  if (!analises || analises.length === 0) {
    return {
      total_analises: 0,
      analises_concluidas: 0,
      analises_erro: 0,
      total_tokens: 0,
      custo_total_reais: 0,
      tempo_medio_ms: 0,
      ultima_analise: null,
    }
  }

  const concluidas = analises.filter(a => a.status === "concluida")
  const erros = analises.filter(a => a.status === "erro")

  const totalTokens = concluidas.reduce((sum, a) => sum + (a.tokens_utilizados || 0), 0)
  const custoTotal = concluidas.reduce((sum, a) => sum + (parseFloat(a.custo_reais) || 0), 0)
  const tempoTotal = concluidas.reduce((sum, a) => sum + (a.tempo_processamento_ms || 0), 0)
  const tempoMedio = concluidas.length > 0 ? Math.round(tempoTotal / concluidas.length) : 0

  return {
    total_analises: analises.length,
    analises_concluidas: concluidas.length,
    analises_erro: erros.length,
    total_tokens: totalTokens,
    custo_total_reais: parseFloat(custoTotal.toFixed(4)),
    tempo_medio_ms: tempoMedio,
    ultima_analise: analises[0]?.created_at || null,
  }
}
