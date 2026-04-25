import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://127.0.0.1:8000";
const INTERNAL_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

export async function POST(request: Request) {
  try {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Usuário não autenticado." }, { status: 401 });
    }

    const { data: perfil } = await supabase
      .from("perfis")
      .select("empresa_id")
      .eq("id", user.id)
      .single();

    if (!perfil?.empresa_id) {
      return NextResponse.json({ error: "empresa_id não encontrado." }, { status: 403 });
    }

    const payload = await request.json();

    if (!payload.texto_bruto?.trim()) {
      return NextResponse.json({ error: "texto_bruto é obrigatório." }, { status: 400 });
    }

    // Injetar dados validados do banco (NÃO do client-side)
    payload.empresa_id = perfil.empresa_id;
    payload.usuario_id = user.id;

    // Timeout: 30s to avoid hanging if FastAPI is slow
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30_000);

    // Autenticação service-to-service: chave interna + empresa_id/user_id via headers
    const response = await fetch(`${FASTAPI_URL}/api/ofertas/analisar-async`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Key": INTERNAL_KEY,
        "X-Empresa-Id": perfil.empresa_id,
        "X-User-Id": user.id,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`[FastAPI] analisar-async ${response.status}: ${errorBody}`);
      return NextResponse.json(
        { error: "Falha ao iniciar análise.", detail: errorBody },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    const errMessage = err instanceof Error ? err.message : String(err);
    console.error("[analisar-async] Erro:", errMessage);
    console.error("[analisar-async] FASTAPI_URL:", FASTAPI_URL);
    return NextResponse.json({ error: "Erro interno ao conectar com o backend.", detail: errMessage }, { status: 500 });
  }
}
