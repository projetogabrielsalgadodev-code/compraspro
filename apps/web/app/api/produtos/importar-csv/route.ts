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

    // Ler o FormData do request
    const formData = await request.formData();
    const arquivo = formData.get("arquivo") as File | null;

    if (!arquivo) {
      return NextResponse.json({ error: "Nenhum arquivo enviado." }, { status: 400 });
    }

    // Montar FormData para o FastAPI
    const fastapiFormData = new FormData();
    fastapiFormData.append("arquivo", arquivo, arquivo.name);

    const response = await fetch(`${FASTAPI_URL}/api/produtos/importar-csv`, {
      method: "POST",
      headers: {
        "X-Internal-Key": INTERNAL_KEY,
        "X-Empresa-Id": perfil.empresa_id,
        "X-User-Id": user.id,
      },
      body: fastapiFormData,
      cache: "no-store",
    });

    if (!response.ok) {
      const errorBody = await response.text();
      console.error(`[FastAPI] importar-csv ${response.status}: ${errorBody}`);
      return NextResponse.json(
        { error: "Falha ao importar CSV.", detail: errorBody },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    const errMessage = err instanceof Error ? err.message : String(err);
    console.error("[importar-csv] Erro:", errMessage);
    return NextResponse.json({ error: "Erro interno ao conectar com o backend.", detail: errMessage }, { status: 500 });
  }
}
