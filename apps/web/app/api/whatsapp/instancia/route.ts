import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://127.0.0.1:8000";
const INTERNAL_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

export const maxDuration = 60;
export const dynamic = "force-dynamic";

/**
 * Proxy genérico para as rotas WhatsApp do FastAPI.
 * Todas as chamadas passam autenticação JWT do Supabase e injetam empresa_id/user_id.
 */
async function getAuthContext() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    return { error: NextResponse.json({ error: "Usuário não autenticado." }, { status: 401 }) };
  }

  const { data: perfil } = await supabase
    .from("perfis")
    .select("empresa_id")
    .eq("id", user.id)
    .single();

  if (!perfil?.empresa_id) {
    return { error: NextResponse.json({ error: "empresa_id não encontrado." }, { status: 403 }) };
  }

  return { user, empresaId: perfil.empresa_id };
}

function buildHeaders(empresaId: string, userId: string) {
  return {
    "Content-Type": "application/json",
    "X-Internal-Key": INTERNAL_KEY,
    "X-Empresa-Id": empresaId,
    "X-User-Id": userId,
  };
}

// ─── POST /api/whatsapp/instancia → Criar instância ─────────────────────────

export async function POST() {
  try {
    const auth = await getAuthContext();
    if ("error" in auth) return auth.error;

    const response = await fetch(`${FASTAPI_URL}/api/whatsapp/instancia/criar`, {
      method: "POST",
      headers: buildHeaders(auth.empresaId, auth.user.id),
      body: JSON.stringify({}),
      cache: "no-store",
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[whatsapp/instancia] POST erro:", msg);
    return NextResponse.json({ error: "Erro ao criar instância.", detail: msg }, { status: 500 });
  }
}

// ─── GET /api/whatsapp/instancia → Consultar instância ──────────────────────

export async function GET() {
  try {
    const auth = await getAuthContext();
    if ("error" in auth) return auth.error;

    const response = await fetch(`${FASTAPI_URL}/api/whatsapp/instancia`, {
      method: "GET",
      headers: buildHeaders(auth.empresaId, auth.user.id),
      cache: "no-store",
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[whatsapp/instancia] GET erro:", msg);
    return NextResponse.json({ error: "Erro ao consultar instância.", detail: msg }, { status: 500 });
  }
}
