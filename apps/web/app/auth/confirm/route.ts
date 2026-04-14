import { NextResponse } from 'next/server'
import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'
import type { EmailOtpType } from '@supabase/supabase-js'

/**
 * Server‑side email verification handler for SSR/PKCE flow.
 *
 * The invite email links here instead of Supabase's /auth/v1/verify.
 * This route receives token_hash + type, calls verifyOtp server‑side
 * to create the session, then redirects the user.
 *
 * URL format: /auth/confirm?token_hash=xxx&type=invite&next=/auth/criar-senha
 */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)

  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type') as EmailOtpType | null
  const next = searchParams.get('next') ?? '/home'

  if (!token_hash || !type) {
    console.error('[auth/confirm] Missing token_hash or type')
    return NextResponse.redirect(
      `${origin}/auth/login?error=MissingToken`
    )
  }

  const cookieStore = await cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet: { name: string; value: string; options: CookieOptions }[]) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch (error) {
            // Ignore errors in server components
          }
        },
      },
    }
  )

  // Verify the token server‑side — this creates the session
  const { data, error } = await supabase.auth.verifyOtp({
    token_hash,
    type,
  })

  if (error) {
    console.error('[auth/confirm] verifyOtp error:', error.message)
    return NextResponse.redirect(
      `${origin}/auth/login?error=InvalidToken&detail=${encodeURIComponent(error.message)}`
    )
  }

  // For invite type, always redirect to password creation
  if (type === 'invite') {
    return NextResponse.redirect(`${origin}/auth/criar-senha`)
  }

  // For other types (recovery, email change, etc.) use the next param
  return NextResponse.redirect(`${origin}${next}`)
}
