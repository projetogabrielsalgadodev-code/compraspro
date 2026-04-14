'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { supabaseAdmin } from '@/lib/supabase/admin'
import { revalidatePath } from 'next/cache'

// Função utilitária básica para obter o supabase_client da requisição
const getSupabase = async () => {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll() {} // Server actions shouldn't generally set auth cookies without a request context if they aren't logging in
      },
    }
  )
}

/**
 * SEGURANÇA: Verifica se o usuário autenticado é admin.
 * Deve ser chamado em TODAS as server actions que usam supabaseAdmin.
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

  // Verificar isadmin ou papel = 'admin'
  if (!perfil?.isadmin && perfil?.papel !== 'admin') {
    return { error: 'Acesso negado. Apenas administradores podem executar esta ação.' }
  }

  return { userId: user.id }
}

export async function getUsers(empresaId?: string) {
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return []

  // Admin requires cross-tenant visibility → use supabaseAdmin
  let query = supabaseAdmin
    .from('perfis')
    .select(`
      id, 
      nome, 
      papel, 
      empresa_id,
      created_at, 
      empresas ( id, nome )
    `)
    .order('created_at', { ascending: false })

  if (empresaId) {
    query = query.eq('empresa_id', empresaId)
  }

  const { data, error } = await query

  if (error) {
    console.error('Erro ao buscar usuários:', error)
    return []
  }

  // Preencher email porque na tabela perfis não tem email nativamente (Supabase auth users tem)
  // Mas para ver os emails dos outros no painel de admin, precisamos usar a service_role.
  const { data: authUsers } = await supabaseAdmin.auth.admin.listUsers()
  
  const usuariosComEmail = data.map(perfil => {
     const authUser = authUsers?.users.find(u => u.id === perfil.id)
     return {
        ...perfil,
        email: authUser?.email || 'N/A'
     }
  })

  return usuariosComEmail
}

export async function getEmpresasList() {
  // Admin requires cross-tenant visibility
  const { data, error } = await supabaseAdmin
    .from('empresas')
    .select('id, nome')
    .eq('ativo', true)
    .order('nome')

  if (error) {
    console.error('Erro ao buscar empresas:', error)
    return []
  }
  return data
}

export async function getEmpresaById(id: string) {
  const { data, error } = await supabaseAdmin
    .from('empresas')
    .select('id, nome')
    .eq('id', id)
    .single()

  if (error) return null
  return data
}

export async function inviteUser(formData: FormData) {
  // SEGURANÇA: Verificar admin antes de usar supabaseAdmin
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return { error: adminCheck.error }

  const email = formData.get('email') as string
  const nome = formData.get('nome') as string
  const papel = formData.get('papel') as string
  const empresaId = formData.get('empresa_id') as string

  if (!email || !nome) {
    return { error: 'E-mail e nome são obrigatórios' }
  }

  if (!empresaId) {
    return { error: 'Selecione uma empresa para vincular este usuário.' }
  }

  // 1. Invitar o usuário via Supabase Auth Admin
  const appUrl = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'
  const { data: inviteData, error: inviteError } = await supabaseAdmin.auth.admin.inviteUserByEmail(email, {
     data: {
        nome: nome,
     },
     redirectTo: `${appUrl}/auth/callback?next=/auth/criar-senha`,
  })

  if (inviteError) {
    return { error: inviteError.message }
  }

  const userId = inviteData.user.id

  // 2. Criar ou Atualizar no public.perfis
  const updateData: any = {
     id: userId,
     nome: nome,
     papel: papel || 'funcionario',
     empresa_id: empresaId,
  }

  const { error: profileError } = await supabaseAdmin
    .from('perfis')
    .upsert(updateData)

  if (profileError) {
     return { error: 'Usuário convidado, mas houve erro ao definir a permissão: ' + profileError.message }
  }

  revalidatePath('/admin/usuarios')
  return { success: `Convite enviado com sucesso para ${email}` }
}

export async function updateUser(formData: FormData) {
  // SEGURANÇA: Verificar admin antes de usar supabaseAdmin
  const adminCheck = await requireAdmin()
  if ('error' in adminCheck) return { error: adminCheck.error }

  const id = formData.get('id') as string // User ID
  const nome = formData.get('nome') as string
  const papel = formData.get('papel') as string
  const empresaId = formData.get('empresa_id') as string

  if (!id || !nome || !empresaId) {
    return { error: 'Campos obrigatórios faltando' }
  }

  // 1. Atualizar metadata no auth
  const { error: authError } = await supabaseAdmin.auth.admin.updateUserById(id, {
     user_metadata: { nome }
  })

  // Permissão falha não interrompe porque o principal é a tabela perfil
  if (authError) {
     console.error("Erro ao atualizar auth user:", authError)
  }

  // 2. Atualizar no public.perfis
  const updateData = {
     nome: nome,
     papel: papel || 'funcionario',
     empresa_id: empresaId,
  }

  const { error: profileError } = await supabaseAdmin
    .from('perfis')
    .update(updateData)
    .eq('id', id)

  if (profileError) {
     return { error: 'Erro ao atualizar o perfil: ' + profileError.message }
  }

  revalidatePath('/admin/usuarios')
  return { success: 'Usuário atualizado com sucesso!' }
}

export async function updateRole(userId: string, newRole: string) {
   // SEGURANÇA: Verificar admin
   const adminCheck = await requireAdmin()
   if ('error' in adminCheck) return { error: adminCheck.error }

   const { error } = await supabaseAdmin
     .from('perfis')
     .update({ papel: newRole })
     .eq('id', userId)

   if (error) {
     return { error: error.message }
   }
   
   revalidatePath('/admin/usuarios')
   return { success: 'Permissão atualizada com sucesso!' }
}

export async function updateUserEmpresa(userId: string, empresaId: string) {
   // SEGURANÇA: Verificar admin
   const adminCheck = await requireAdmin()
   if ('error' in adminCheck) return { error: adminCheck.error }

   const { error } = await supabaseAdmin
     .from('perfis')
     .update({ empresa_id: empresaId || null })
     .eq('id', userId)

   if (error) {
     return { error: error.message }
   }
   
   revalidatePath('/admin/usuarios')
   return { success: 'Empresa atualizada com sucesso!' }
}

export async function deleteUser(userId: string) {
   // SEGURANÇA: Verificar admin antes de deletar
   const adminCheck = await requireAdmin()
   if ('error' in adminCheck) return { error: adminCheck.error }

   // Remove o auth
   const { error: authError } = await supabaseAdmin.auth.admin.deleteUser(userId)
   if (authError) return { error: authError.message }

   revalidatePath('/admin/usuarios')
   return { success: 'Usuário removido com sucesso!' }
}
