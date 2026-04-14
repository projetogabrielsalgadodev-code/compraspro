'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'
import { validarCNPJ, validarTelefone } from '@/lib/validators'
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
 * Deve ser chamado em TODAS as server actions de escrita no admin.
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
    return { error: 'Acesso negado. Apenas administradores podem executar esta ação.' }
  }

  return { userId: user.id }
}

export async function getEmpresas() {
  // Leitura: requireAdmin para listar empresas no painel admin
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return []

  // Admin precisa ver TODAS as empresas → usa supabaseAdmin (bypassa RLS)
  const { data, error } = await supabaseAdmin
    .from('empresas')
    .select('*')
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Erro ao buscar empresas:', error)
    return []
  }

  // Busca a contagem de usuários por empresa (também via admin p/ ver todos)
  const { data: users } = await supabaseAdmin.from('perfis').select('empresa_id')
  
  const empresasComConta = data.map(empresa => {
     const qtdeUsuarios = users?.filter(u => u.empresa_id === empresa.id).length || 0;
     return {
        ...empresa,
        qtdeUsuarios
     }
  })

  return empresasComConta
}

export async function upsertEmpresa(formData: FormData) {
  // SEGURANÇA: Verificar admin antes de criar/editar empresa
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return { error: adminCheck.error }

  const id = formData.get('id') as string
  const nome = formData.get('nome') as string
  const cnpj = formData.get('cnpj') as string
  const razao_social = formData.get('razao_social') as string
  const telefone = formData.get('telefone') as string
  const email = formData.get('email') as string
  const endereco = formData.get('endereco') as string
  const ativo = formData.get('ativo') !== 'false'

  if (!nome || !cnpj) {
    return { error: 'Nome e CNPJ são obrigatórios.' }
  }

  if (!validarCNPJ(cnpj)) {
    return { error: 'CNPJ inválido.' }
  }

  if (telefone && !validarTelefone(telefone)) {
    return { error: 'Telefone inválido.' }
  }

  // Admin gerencia empresas via supabaseAdmin (RLS agora filtra por empresa)
  const payload: any = { nome, cnpj, razao_social, telefone, email, endereco, ativo }
  if (id) {
    payload.id = id
  }

  const { error } = await supabaseAdmin.from('empresas').upsert(payload)

  if (error) {
    return { error: error.message }
  }

  revalidatePath('/admin/empresas')
  return { success: id ? 'Empresa atualizada!' : 'Empresa cadastrada com sucesso!' }
}

export async function deleteEmpresa(id: string) {
  // SEGURANÇA: Verificar admin
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return { error: adminCheck.error }

  const { error } = await supabaseAdmin.from('empresas').delete().eq('id', id)

  if (error) {
    return { error: error.message }
  }

  revalidatePath('/admin/empresas')
  return { success: 'Empresa removida com sucesso!' }
}

export async function toggleEmpresaAtivo(id: string, ativo: boolean) {
  // SEGURANÇA: Verificar admin
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return { error: adminCheck.error }

  const { error } = await supabaseAdmin
    .from('empresas')
    .update({ ativo })
    .eq('id', id)

  if (error) {
    return { error: error.message }
  }

  revalidatePath('/admin/empresas')
  return { success: ativo ? 'Empresa reativada!' : 'Empresa desativada!' }
}
