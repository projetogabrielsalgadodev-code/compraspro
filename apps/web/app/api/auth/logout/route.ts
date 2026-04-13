import { createClient } from "@/lib/supabase/server";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const supabase = await createClient();

  // Sign out — limpa os cookies de sessão SSR no servidor
  await supabase.auth.signOut();

  // Determinar URL base para o redirect
  const requestUrl = new URL(request.url);
  const origin = requestUrl.origin;

  const response = NextResponse.redirect(`${origin}/auth/login`, { status: 302 });

  // Forçar expiração dos cookies de sessão do Supabase
  // (o signOut() acima já faz isso, mas garantimos aqui como fallback)
  response.cookies.set("sb-access-token", "", { maxAge: 0, path: "/" });
  response.cookies.set("sb-refresh-token", "", { maxAge: 0, path: "/" });

  return response;
}
