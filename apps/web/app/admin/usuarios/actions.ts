'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { supabaseAdmin } from '@/lib/supabase/admin'
import { revalidatePath } from 'next/cache'

// Função utilitária básica para obter o supabase_client da requisição
const getSupabase = () => {
  const cookieStore = cookies()
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

export async function getUsers() {
  const supabase = getSupabase()
  const { data, error } = await supabase
    .from('perfis')
    .select(`
      id, 
      nome, 
      papel, 
      created_at, 
      empresas ( id, nome )
    `)
    .order('created_at', { ascending: false })

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

export async function inviteUser(formData: FormData) {
  const email = formData.get('email') as string
  const nome = formData.get('nome') as string
  const papel = formData.get('papel') as string // 'admin' ou 'funcionario'
  const empresaId = formData.get('empresa_id') as string // opcional, caso estritamente funcionário de uma. Por enquanto null.

  if (!email || !nome) {
    return { error: 'E-mail e nome são obrigatórios' }
  }

  // 1. Invitar o usuário via Supabase Auth Admin
  const { data: inviteData, error: inviteError } = await supabaseAdmin.auth.admin.inviteUserByEmail(email, {
     data: {
        nome: nome,
     }
  })

  if (inviteError) {
    return { error: inviteError.message }
  }

  const userId = inviteData.user.id

  // 2. Criar ou Atualizar no public.perfis
  // (A trigger do BD pode já ter criado o perfil pelo JWT raw_user_meta_data.nome,
  // então fazemos um upsert para garantir a Role)
  
  const updateData: any = {
     id: userId,
     nome: nome,
     papel: papel || 'funcionario'
  }

  if (empresaId) {
     updateData.empresa_id = empresaId
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

export async function updateRole(userId: string, newRole: string) {
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

export async function deleteUser(userId: string) {
   // Remove o auth
   const { error: authError } = await supabaseAdmin.auth.admin.deleteUser(userId)
   if (authError) return { error: authError.message }

   revalidatePath('/admin/usuarios')
   return { success: 'Usuário removido com sucesso!' }
}
