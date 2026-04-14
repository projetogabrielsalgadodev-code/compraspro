import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";
const INTERNAL_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

export async function POST(request: Request) {
  try {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json(
        { error: "Usuário não autenticado." },
        { status: 401 }
      );
    }

    const { data: perfil } = await supabase
      .from('perfis')
      .select('empresa_id')
      .eq('id', user.id)
      .single();

    if (!perfil?.empresa_id) {
      return NextResponse.json(
        { error: "empresa_id não encontrado para este usuário." },
        { status: 403 }
      );
    }

    const payload = await request.json();

    if (!payload.texto_bruto?.trim()) {
      return NextResponse.json(
        { error: "texto_bruto é obrigatório." },
        { status: 400 }
      );
    }

    // Injetar o empresa_id encontrado no banco e o id do usuario responsável
    payload.empresa_id = perfil.empresa_id;
    payload.usuario_id = user.id;

    // Timeout de 120s — a análise Agno com tool calling pode levar tempo
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120_000);

    // Autenticação service-to-service via chave interna
    const response = await fetch(`${FASTAPI_URL}/api/ofertas/analisar`, {
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

    clearTimeout(timeout);

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`[FastAPI] ${response.status}: ${errorBody}`);
      return NextResponse.json(
        { error: "Falha ao processar análise.", detail: errorBody },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    if (err instanceof Error && err.name === "AbortError") {
      return NextResponse.json(
        { error: "Timeout: a análise demorou mais de 120 segundos." },
        { status: 504 }
      );
    }
    console.error("[Route Handler] Erro inesperado:", err);
    return NextResponse.json(
      { error: "Erro interno ao conectar com o backend." },
      { status: 500 }
    );
  }
}
