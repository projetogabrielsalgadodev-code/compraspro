import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://127.0.0.1:8000";
const INTERNAL_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY ?? "";

// ─── Vercel Serverless Config ────────────────────────────────────────────────
// maxDuration: Hobby=10s, Pro=60s. Aumentar para comportar upload + cold start do Render.
export const maxDuration = 60;

// Desabilitar o body parser padrão do Next.js (limite de 1MB) para aceitar uploads grandes.
// O formData() do Web API não tem esse limite.
export const dynamic = "force-dynamic";

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

    // Ler o FormData do request
    const formData = await request.formData();
    const textoBruto = formData.get("texto_bruto") as string;
    const fonteDados = formData.get("fonte_dados") as string || "banco";
    const fornecedorInformado = formData.get("fornecedor_informado") as string | null;
    const arquivo = formData.get("arquivo") as File | null;
    const arquivoOferta = formData.get("arquivo_oferta") as File | null;

    // Validate: need at least texto_bruto or arquivo_oferta
    if (!textoBruto?.trim() && !arquivoOferta) {
      return NextResponse.json({ error: "texto_bruto ou arquivo_oferta é obrigatório." }, { status: 400 });
    }

    // Montar FormData para o FastAPI
    const fastapiFormData = new FormData();
    fastapiFormData.append("texto_bruto", textoBruto || "");
    fastapiFormData.append("fonte_dados", fonteDados);
    fastapiFormData.append("usuario_id", user.id);
    if (fornecedorInformado) {
      fastapiFormData.append("fornecedor_informado", fornecedorInformado);
    }
    if (arquivo) {
      fastapiFormData.append("arquivo", arquivo, arquivo.name);
    }
    if (arquivoOferta) {
      fastapiFormData.append("arquivo_oferta", arquivoOferta, arquivoOferta.name);
    }

    // Timeout: 55s — deve ser menor que maxDuration (60s) para retornar erro legível
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55_000);

    const response = await fetch(`${FASTAPI_URL}/api/ofertas/analisar-async-file`, {
      method: "POST",
      headers: {
        "X-Internal-Key": INTERNAL_KEY,
        "X-Empresa-Id": perfil.empresa_id,
        "X-User-Id": user.id,
        // NÃO setar Content-Type — o fetch API seta automaticamente com boundary
      },
      body: fastapiFormData,
      cache: "no-store",
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`[FastAPI] analisar-async-file ${response.status}: ${errorBody}`);
      return NextResponse.json(
        { error: "Falha ao iniciar análise.", detail: errorBody },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    const errMessage = err instanceof Error ? err.message : String(err);
    console.error("[analisar-async-file] Erro:", errMessage);
    console.error("[analisar-async-file] FASTAPI_URL:", FASTAPI_URL);
    return NextResponse.json({ error: "Erro interno ao conectar com o backend.", detail: errMessage }, { status: 500 });
  }
}
