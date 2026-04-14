import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  try {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Usuário não autenticado." }, { status: 401 });
    }

    // Obter access_token para repassar ao FastAPI (que agora exige JWT)
    const { data: { session } } = await supabase.auth.getSession();
    if (!session?.access_token) {
      return NextResponse.json({ error: "Sessão expirada. Faça login novamente." }, { status: 401 });
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

    payload.empresa_id = perfil.empresa_id;
    payload.usuario_id = user.id;

    // SEGURANÇA: Forward do Bearer token para o FastAPI (obrigatório após hardening)
    const response = await fetch(`${FASTAPI_URL}/api/ofertas/analisar-async`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${session.access_token}`,
      },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

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
