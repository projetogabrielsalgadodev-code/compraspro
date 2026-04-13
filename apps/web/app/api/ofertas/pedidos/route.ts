import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

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

    if (!payload.eans || !Array.isArray(payload.eans) || payload.eans.length === 0) {
      return NextResponse.json(
        { error: "Informe os itens aprovados para gerar o pedido (array de eans)." },
        { status: 400 }
      );
    }

    // Load items for the EANs (or use the JSON sent from client directly). We will just use the payload exactly.
    // Assuming client just sends { analise_id, eans, itens_detalhes }
    // Actually we can just save it as JSON.
    const itensParaSalvar = payload.itens_detalhes || payload.eans;

    const insertData = {
      empresa_id: perfil.empresa_id,
      usuario_id: user.id,
      analise_id: payload.analise_id !== "local" ? payload.analise_id : null,
      itens_aprovados: itensParaSalvar,
      status: "pendente"
    };

    const { error, data } = await supabase
      .from("pedido_compras_sugestao")
      .insert(insertData)
      .select()
      .single();

    if (error) {
      console.error("[Route Handler] Erro ao criar pedido de compras:", error);
      return NextResponse.json(
        { error: "Falha ao criar o pedido de compras." },
        { status: 500 }
      );
    }

    return NextResponse.json({ success: true, pedido_id: data.id }, { status: 200 });
  } catch (err) {
    console.error("[Route Handler] Erro inesperado:", err);
    return NextResponse.json(
      { error: "Erro interno no servidor." },
      { status: 500 }
    );
  }
}
