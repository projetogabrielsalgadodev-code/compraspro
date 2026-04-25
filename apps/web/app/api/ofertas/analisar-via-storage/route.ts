import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://127.0.0.1:8000";
const INTERNAL_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

// ─── Vercel Serverless Config ────────────────────────────────────────────────
// Essa rota é leve (só JSON com paths), mas Render pode demorar no cold start
export const maxDuration = 60;
export const dynamic = "force-dynamic";

/**
 * Nova rota de análise via Storage.
 * 
 * Fluxo:
 * 1. Frontend faz upload dos arquivos direto pro Supabase Storage (bucket uploads-temp)
 * 2. Frontend chama essa rota com os paths do Storage
 * 3. Essa rota repassa os paths pro Render (FastAPI)
 * 4. Render baixa os arquivos do Supabase Storage usando service_role
 * 
 * Isso elimina:
 * - Limite de body size da Vercel (4.5 MB)
 * - Timeout da Vercel (arquivos nunca passam por aqui)
 */
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

    const {
      texto_bruto = "",
      fonte_dados = "banco",
      fornecedor_informado = null,
      storage_path_oferta = null,
      storage_path_historico = null,
      nome_arquivo_oferta = null,
      nome_arquivo_historico = null,
    } = payload;

    // Validar: precisa de texto OU arquivo de oferta
    if (!texto_bruto?.trim() && !storage_path_oferta) {
      return NextResponse.json(
        { error: "texto_bruto ou arquivo de oferta é obrigatório." },
        { status: 400 }
      );
    }

    // Montar payload para o FastAPI
    const fastapiPayload = {
      texto_bruto: texto_bruto || "",
      fonte_dados,
      fornecedor_informado,
      usuario_id: user.id,
      // Paths do Supabase Storage para o Render baixar diretamente
      storage_path_oferta,
      storage_path_historico,
      nome_arquivo_oferta,
      nome_arquivo_historico,
    };

    // Timeout: 55s (menor que maxDuration para retornar erro legível)
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55_000);

    const response = await fetch(`${FASTAPI_URL}/api/ofertas/analisar-via-storage`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Key": INTERNAL_KEY,
        "X-Empresa-Id": perfil.empresa_id,
        "X-User-Id": user.id,
      },
      body: JSON.stringify(fastapiPayload),
      cache: "no-store",
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`[FastAPI] analisar-via-storage ${response.status}: ${errorBody}`);
      return NextResponse.json(
        { error: "Falha ao iniciar análise.", detail: errorBody },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    const errMessage = err instanceof Error ? err.message : String(err);
    console.error("[analisar-via-storage] Erro:", errMessage);
    console.error("[analisar-via-storage] FASTAPI_URL:", FASTAPI_URL);
    return NextResponse.json(
      { error: "Erro interno ao conectar com o backend.", detail: errMessage },
      { status: 500 }
    );
  }
}
