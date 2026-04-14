import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: Request) {
  try {
    // SEGURANÇA: Verificar autenticação
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Não autenticado." }, { status: 401 });
    }

    // Obter empresa_id do perfil do usuário (não do query param)
    const { data: perfil } = await supabase
      .from("perfis")
      .select("empresa_id")
      .eq("id", user.id)
      .single();

    if (!perfil?.empresa_id) {
      return NextResponse.json({ error: "Usuário sem empresa vinculada." }, { status: 403 });
    }

    // Buscar configuração usando empresa_id do perfil do usuário autenticado
    const { data: config, error } = await supabase
      .from("configuracoes_empresa")
      .select("*")
      .eq("empresa_id", perfil.empresa_id)
      .single();

    if (error && error.code !== "PGRST116") {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    if (!config) {
      return NextResponse.json({ error: "Configuração não encontrada." }, { status: 404 });
    }

    return NextResponse.json(config, { status: 200 });
  } catch (err) {
    console.error("[configuracoes/empresa GET] Erro:", err);
    return NextResponse.json({ error: "Erro interno." }, { status: 500 });
  }
}

export async function PUT(request: Request) {
  try {
    // SEGURANÇA: Verificar autenticação
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();

    if (!user) {
      return NextResponse.json({ error: "Não autenticado." }, { status: 401 });
    }

    // Obter empresa_id do perfil do usuário (não do payload)
    const { data: perfil } = await supabase
      .from("perfis")
      .select("empresa_id")
      .eq("id", user.id)
      .single();

    if (!perfil?.empresa_id) {
      return NextResponse.json({ error: "Usuário sem empresa vinculada." }, { status: 403 });
    }

    const payload = await request.json();

    // Forçar empresa_id do perfil autenticado (ignorar qualquer empresa_id do payload)
    payload.empresa_id = perfil.empresa_id;

    const { data: config, error } = await supabase
      .from("configuracoes_empresa")
      .upsert(payload, { onConflict: "empresa_id" })
      .select()
      .single();

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    return NextResponse.json(config, { status: 200 });
  } catch (err) {
    console.error("[configuracoes/empresa PUT] Erro:", err);
    return NextResponse.json({ error: "Erro interno." }, { status: 500 });
  }
}
