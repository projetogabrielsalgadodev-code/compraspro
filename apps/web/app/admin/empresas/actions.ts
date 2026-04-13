'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

// Como as operações de empresa são feitas por Admins logados, a RLS permite acesso,
// podemos usar a chave ANON pois o middleware já validou que o usuário é admin via role
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

  // Busca tbm a contagem de usuários por empresa pra exibir na grid
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
  const id = formData.get('id') as string // Se vazio, é criação
  const nome = formData.get('nome') as string
  const cnpj = formData.get('cnpj') as string

  if (!nome || !cnpj) {
    return { error: 'Nome e CNPJ são obrigatórios.' }
  }

  const supabase = getSupabase()

  // Evita enviar strings vazias como IDs (Supabase ignora upsert sem id válido ou crasha)
  const payload: any = { nome, cnpj }
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
  return { success: 'Empresa desativada/removida com sucesso!' }
}
