import { createServerClient } from "@supabase/ssr"
import { NextResponse, type NextRequest } from "next/server"

// Rotas /auth que devem permanecer acessíveis mesmo com sessão ativa
// (ex: usuário convidado precisa criar senha, ou token verification)
const AUTH_ROUTES_ALLOW_AUTHENTICATED = [
  "/auth/criar-senha",
  "/auth/atualizar-senha",
  "/auth/confirm",
  "/auth/callback",
]

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

  const { pathname } = request.nextUrl

  const isAuthRoute = pathname.startsWith("/auth")
  const isApiRoute = pathname.startsWith("/api")
  const isPublicAsset =
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.includes(".")

  // Otimização de performance: Não chamar getUser (network request) para assets ou APIs
  // APIs cuidam da própria autenticação internamente.
  if (isPublicAsset || isApiRoute) {
    return supabaseResponse
  }

  // Refresh session (obrigatório para Server Components) e validação segura
  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Verifica se é uma rota /auth que permite usuários autenticados
  const isAuthRouteAllowAuthenticated = AUTH_ROUTES_ALLOW_AUTHENTICATED.some(
    route => pathname.startsWith(route)
  )

  // ─── Rotas protegidas (tudo que NÃO é /auth, /api ou assets) ─────────────
  const isProtectedRoute = !isAuthRoute && !isApiRoute && !isPublicAsset

  if (!user && isProtectedRoute) {
    // Não autenticado → redireciona para login, preservando destino original
    const url = request.nextUrl.clone()
    url.pathname = "/auth/login"
    url.searchParams.set("next", pathname)
    return NextResponse.redirect(url)
  }

  if (user && isAuthRoute && !isAuthRouteAllowAuthenticated) {
    // Já autenticado em rota /auth que NÃO é exceção → vai para home
    // (callback, criar-senha e atualizar-senha são permitidos mesmo autenticado)
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
