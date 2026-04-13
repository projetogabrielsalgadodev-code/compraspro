'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

const getSupabase = () => {
  const cookieStore = cookies()
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

export async function getEmpresasParaConfig() {
  const supabase = getSupabase()
  const { data, error } = await supabase
    .from('empresas')
    .select('id, nome')
    .order('nome', { ascending: true })

  if (error) return []
  return data
}

export async function getConfiguracao(empresaId: string) {
  const supabase = getSupabase()
  const { data, error } = await supabase
    .from('configuracoes_empresa')
    .select('*')
    .eq('empresa_id', empresaId)
    .single()

  if (error && error.code !== 'PGRST116') { // PGRST116 is "No rows returned"
    console.error('Erro ao buscar configuração:', error)
  }

  return data || null
}

export async function saveConfiguracao(formData: FormData) {
  const empresa_id = formData.get('empresa_id') as string
  const margem_lucro_padrao = parseFloat(formData.get('margem_lucro_padrao') as string)
  const ignorar_historico_acima_dias = parseInt(formData.get('ignorar_historico_acima_dias') as string, 10)
  const percentual_variacao_alerta = parseFloat(formData.get('percentual_variacao_alerta') as string)

  if (!empresa_id) {
    return { error: 'Empresa não selecionada.' }
  }

  const payload = {
    empresa_id,
    margem_lucro_padrao: isNaN(margem_lucro_padrao) ? 30.00 : margem_lucro_padrao,
    ignorar_historico_acima_dias: isNaN(ignorar_historico_acima_dias) ? 90 : ignorar_historico_acima_dias,
    percentual_variacao_alerta: isNaN(percentual_variacao_alerta) ? 15.00 : percentual_variacao_alerta
  }

  const supabase = getSupabase()
  const { error } = await supabase
    .from('configuracoes_empresa')
    .upsert(payload, { onConflict: 'empresa_id' })

  if (error) {
    return { error: error.message }
  }

  return { success: 'Configurações salvas com sucesso!' }
}
