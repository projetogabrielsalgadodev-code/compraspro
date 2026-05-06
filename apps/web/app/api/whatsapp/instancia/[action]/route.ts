import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://127.0.0.1:8000";
const INTERNAL_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

export const dynamic = "force-dynamic";

async function proxyPost(endpoint: string) {
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

  const response = await fetch(`${FASTAPI_URL}/api/whatsapp/instancia/${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Internal-Key": INTERNAL_KEY,
      "X-Empresa-Id": perfil.empresa_id,
      "X-User-Id": user.id,
    },
    body: JSON.stringify({}),
    cache: "no-store",
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ action: string }> }
) {
  try {
    const { action } = await params;

    if (!["desconectar", "reconectar", "analisar"].includes(action)) {
      return NextResponse.json({ error: "Ação inválida." }, { status: 400 });
    }

    return await proxyPost(action);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[whatsapp/instancia/action] POST erro:", msg);
    return NextResponse.json({ error: "Erro interno.", detail: msg }, { status: 500 });
  }
}
