import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

export async function GET(
  _request: Request,
  { params }: { params: { analise_id: string } }
) {
  try {
    // SEGURANÇA: Verificar autenticação
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Não autenticado." }, { status: 401 });
    }

    // Verificar que o usuário tem empresa vinculada
    const { data: perfil } = await supabase
      .from("perfis")
      .select("empresa_id")
      .eq("id", user.id)
      .single();

    if (!perfil?.empresa_id) {
      return NextResponse.json({ error: "Usuário sem empresa vinculada." }, { status: 403 });
    }

    const { analise_id } = params;

    // Buscar a análise e verificar que pertence à empresa do usuário
    const { data: analise } = await supabase
      .from("analises_oferta")
      .select("id, status, resultado_json, created_at, empresa_id")
      .eq("id", analise_id)
      .single();

    if (!analise) {
      return NextResponse.json({ error: "Análise não encontrada." }, { status: 404 });
    }

    if (analise.empresa_id !== perfil.empresa_id) {
      return NextResponse.json({ error: "Acesso negado a esta análise." }, { status: 403 });
    }

    return NextResponse.json({
      analise_id: analise.id,
      status: analise.status,
      resultado: analise.resultado_json,
      created_at: analise.created_at,
    }, { status: 200 });
  } catch (err) {
    console.error("[status] Erro:", err);
    return NextResponse.json({ error: "Erro ao consultar status." }, { status: 500 });
  }
}
