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

// ─── Dados do usuário logado ────────────────────────────────────────────────

export async function getCurrentUserData() {
  const supabase = await getSupabase()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return null

  const { data: perfil } = await supabase
    .from("perfis")
    .select("*, empresas(id, nome, cnpj, razao_social, telefone, email, endereco, ativo)")
    .eq("id", user.id)
    .single()

  return perfil
}

// ─── Update Empresa ─────────────────────────────────────────────────────────

export async function updateEmpresa(formData: FormData) {
  const supabase = await getSupabase()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { error: "Não autenticado." }

  const empresaId = formData.get("empresa_id") as string
  if (!empresaId) return { error: "Empresa não identificada." }

  const payload = {
    nome: formData.get("nome") as string,
    razao_social: formData.get("razao_social") as string || null,
    cnpj: formData.get("cnpj") as string || null,
    telefone: formData.get("telefone") as string || null,
    email: formData.get("email") as string || null,
    endereco: formData.get("endereco") as string || null,
  }

  if (!payload.nome) return { error: "Nome da empresa é obrigatório." }

  const { error } = await supabaseAdmin
    .from("empresas")
    .update(payload)
    .eq("id", empresaId)

  if (error) return { error: "Erro ao salvar: " + error.message }

  revalidatePath("/configuracoes")
  return { success: "Dados da empresa atualizados." }
}

// ─── Update Perfil ──────────────────────────────────────────────────────────

export async function updatePerfil(formData: FormData) {
  const supabase = await getSupabase()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { error: "Não autenticado." }

  const payload: Record<string, any> = {
    nome: formData.get("nome") as string,
    telefone: formData.get("telefone") as string || null,
  }

  const avatarUrl = formData.get("avatar_url") as string
  if (avatarUrl) {
    payload.avatar_url = avatarUrl
  }

  if (!payload.nome) return { error: "Nome é obrigatório." }

  const { error } = await supabaseAdmin
    .from("perfis")
    .update(payload)
    .eq("id", user.id)

  if (error) return { error: "Erro ao salvar: " + error.message }

  revalidatePath("/configuracoes")
  return { success: "Perfil atualizado." }
}

// ─── Upload Avatar ──────────────────────────────────────────────────────────

export async function uploadAvatar(formData: FormData) {
  const supabase = await getSupabase()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return { error: "Não autenticado." }

  const file = formData.get("file") as File
  if (!file) return { error: "Nenhum arquivo enviado." }

  const ext = file.name.split(".").pop()
  const fileName = `${user.id}.${ext}`

  // Upload via admin para garantir permissão
  const { error: uploadError } = await supabaseAdmin.storage
    .from("avatars")
    .upload(fileName, file, { upsert: true })

  if (uploadError) return { error: "Erro no upload: " + uploadError.message }

  const { data: urlData } = supabaseAdmin.storage
    .from("avatars")
    .getPublicUrl(fileName)

  // Salvar URL no perfil
  await supabaseAdmin
    .from("perfis")
    .update({ avatar_url: urlData.publicUrl })
    .eq("id", user.id)

  revalidatePath("/configuracoes")
  return { success: "Avatar atualizado.", url: urlData.publicUrl }
}
