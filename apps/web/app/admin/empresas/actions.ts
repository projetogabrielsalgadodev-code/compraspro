'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

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

export async function getEmpresas() {
  const supabase = getSupabase()
  const { data, error } = await supabase
    .from('empresas')
    .select('*')
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Erro ao buscar empresas:', error)
    return []
  }

  // Busca a contagem de usuários por empresa pra exibir no card
  const { data: users } = await supabase.from('perfis').select('empresa_id')
  
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

  const supabase = getSupabase()

  const payload: any = { nome, cnpj, razao_social, telefone, email, endereco, ativo }
  if (id) {
    payload.id = id
  }

  const { error } = await supabase.from('empresas').upsert(payload)

  if (error) {
    return { error: error.message }
  }

  revalidatePath('/admin/empresas')
  return { success: id ? 'Empresa atualizada!' : 'Empresa cadastrada com sucesso!' }
}

export async function deleteEmpresa(id: string) {
  const supabase = getSupabase()
  const { error } = await supabase.from('empresas').delete().eq('id', id)

  if (error) {
    return { error: error.message }
  }

  revalidatePath('/admin/empresas')
  return { success: 'Empresa removida com sucesso!' }
}

export async function toggleEmpresaAtivo(id: string, ativo: boolean) {
  const supabase = getSupabase()
  const { error } = await supabase
    .from('empresas')
    .update({ ativo })
    .eq('id', id)

  if (error) {
    return { error: error.message }
  }

  revalidatePath('/admin/empresas')
  return { success: ativo ? 'Empresa reativada!' : 'Empresa desativada!' }
}
