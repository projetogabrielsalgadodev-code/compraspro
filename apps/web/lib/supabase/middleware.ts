import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet: { name: string; value: string; options?: Record<string, unknown> }[]) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options as Parameters<typeof supabaseResponse.cookies.set>[2])
          )
        },
      },
    }
  )

  // Refresh session (obrigatório para Server Components)
  const {
    data: { user },
  } = await supabase.auth.getUser()

  const { pathname } = request.nextUrl

  const isAuthRoute = pathname.startsWith("/auth")
  const isApiRoute = pathname.startsWith("/api")
  const isPublicAsset =
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon")

  // ─── Rotas protegidas (tudo que NÃO é /auth, /api ou assets) ─────────────
  const isProtectedRoute = !isAuthRoute && !isApiRoute && !isPublicAsset

  if (!user && isProtectedRoute) {
    // Não autenticado → redireciona para login, preservando destino original
    const url = request.nextUrl.clone()
    url.pathname = "/auth/login"
    url.searchParams.set("next", pathname)
    return NextResponse.redirect(url)
  }

  if (user && isAuthRoute) {
    // Já autenticado → não precisa ver login, vai para home
    const url = request.nextUrl.clone()
    url.pathname = "/home"
    return NextResponse.redirect(url)
  }

  // ─── Proteção de rotas /admin → exige isadmin = true ──────────────────────
  const isAdminRoute = pathname.startsWith("/admin")

  if (user && isAdminRoute) {
    const { data: perfil } = await supabase
      .from("perfis")
      .select("isadmin")
      .eq("id", user.id)
      .single()

    if (!perfil || !perfil.isadmin) {
      const url = request.nextUrl.clone()
      url.pathname = "/home"
      return NextResponse.redirect(url)
    }
  }

  return supabaseResponse
}
