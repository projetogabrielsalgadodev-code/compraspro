'use server'

import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function requestPasswordReset(formData: FormData) {
  const email = formData.get('email') as string

  if (!email) {
    return { error: 'O e-mail é obrigatório.' }
  }

  const cookieStore = cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet: any[]) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch (error) {}
        },
      },
    }
  )

  // O redirectTo aponta para a rota de callback para realizar o exchange do PKCE code
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000'}/auth/callback?next=/auth/atualizar-senha`,
  })

  if (error) {
    return { error: error.message }
  }

  return { success: 'Um link de recuperação foi enviado para o seu e-mail!' }
}
