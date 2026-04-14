import { NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

// Rota para manipular o callback do Supabase com o ?code=xxx
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  
  // se existe um `next` param, senão default p/ root
  const next = searchParams.get('next') ?? '/home'

  if (code) {
    const cookieStore = await cookies()
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
            } catch (error) {
              // Ignore errors if called from server actions/components
            }
          },
        },
      }
    )

    // Troca o auth code pela sessão real
    const { data, error } = await supabase.auth.exchangeCodeForSession(code)
    
    if (!error) {
      // Se o destino já é criar-senha, respeitar
      if (next.includes('criar-senha')) {
        return NextResponse.redirect(`${origin}${next}`)
      }

      // Detectar se o usuário é convidado e nunca logou antes
      // Usuários convidados pelo inviteUserByEmail têm invited_at preenchido
      // e se nunca definiram senha, last_sign_in_at será nulo ou igual a agora  
      const user = data?.user
      if (user) {
        const invitedAt = user.invited_at
        const lastSignIn = user.last_sign_in_at
        const confirmedAt = user.confirmed_at

        // É um invite se: tem invited_at E é a primeira vez fazendo sign in
        // (confirmed_at muito próximo de agora indica aceitação recente do convite)
        if (invitedAt) {
          const confirmedTime = confirmedAt ? new Date(confirmedAt).getTime() : 0
          const now = Date.now()
          const isRecentConfirmation = (now - confirmedTime) < 60000 // 1 minuto

          if (isRecentConfirmation) {
            return NextResponse.redirect(`${origin}/auth/criar-senha`)
          }
        }
      }

      return NextResponse.redirect(`${origin}${next}`)
    }
  }

  // Falha na troca do code
  return NextResponse.redirect(`${origin}/auth/login?error=InvalidToken`)
}
