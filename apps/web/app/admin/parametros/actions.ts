'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { supabaseAdmin } from '@/lib/supabase/admin'

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

/**
 * SEGURANÇA: Verifica se o usuário autenticado é admin.
 */
async function requireAdmin(): Promise<{ userId: string } | { error: string }> {
  const supabase = await getSupabase()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) {
    return { error: 'Não autenticado.' }
  }

  const { data: perfil } = await supabase
    .from('perfis')
    .select('isadmin, papel')
    .eq('id', user.id)
    .single()

  if (!perfil?.isadmin && perfil?.papel !== 'admin') {
    return { error: 'Acesso negado. Apenas administradores.' }
  }

  return { userId: user.id }
}

export async function getEmpresasParaConfig() {
  // SEGURANÇA: Verificar admin antes de listar empresas
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return []

  // Admin precisa ver todas as empresas → supabaseAdmin
  const { data, error } = await supabaseAdmin
    .from('empresas')
    .select('id, nome')
    .order('nome', { ascending: true })

  if (error) return []
  return data
}

export async function getConfiguracao(empresaId: string) {
  // SEGURANÇA: Verificar admin
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return null

  const { data, error } = await supabaseAdmin
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
  // SEGURANÇA: Verificar admin antes de salvar
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return { error: adminCheck.error }

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

  const { error } = await supabaseAdmin
    .from('configuracoes_empresa')
    .upsert(payload, { onConflict: 'empresa_id' })

  if (error) {
    return { error: error.message }
  }

  return { success: 'Configurações salvas com sucesso!' }
}
