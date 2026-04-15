import { Metadata } from "next";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { HistoricoListaClient, AnaliseListada } from "@/components/historico/HistoricoListaClient";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Histórico de Análises | Compras PRO",
  description: "Acesse o histórico de leituras, auditorias operacionais e análises anteriories.",
};

// Garante que router.refresh() sempre busque dados atualizados do servidor
export const dynamic = "force-dynamic";


interface HistoricoPageProps {
  searchParams: {
    page?: string;
    query?: string;
    status?: string;
  };
}

export default async function HistoricoPage({ searchParams }: HistoricoPageProps) {
  const supabase = await createClient();

  const page = parseInt(searchParams?.page || "1", 10);
  const query = searchParams?.query || "";
  const status = searchParams?.status || "todos";

  const pageSize = 10;

  // Supabase query builder
  let supabaseQuery = supabase
    .from("analises_oferta")
    .select("*, itens_oferta(id, classificacao)", { count: "exact" });

  if (query) {
    supabaseQuery = supabaseQuery.or(`fornecedor.ilike.%${query}%,origem.ilike.%${query}%`);
  }

  if (status !== "todos") {
    supabaseQuery = supabaseQuery.eq("status", status);
  }

  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;

  const { data: analises, count } = await supabaseQuery
    .order("created_at", { ascending: false })
    .range(from, to);

  const analisesFormatadas: AnaliseListada[] = (analises || []).map((analise) => {
    const totalItens = analise.itens_oferta ? analise.itens_oferta.length : 0;
    const oportunidades = analise.itens_oferta
      ? analise.itens_oferta.filter((i: any) => i.classificacao === 'ouro' || i.classificacao === 'prata').length
      : 0;

    const dateObj = new Date(analise.created_at);
    const dataFormatada = new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "America/Sao_Paulo",
    }).format(dateObj);

    return {
      id: analise.id,
      fornecedor: analise.fornecedor || "Fornecedor Sem Nome",
      itens: totalItens.toString(),
      oportunidades: oportunidades.toString(),
      horario: dataFormatada,
      status: analise.status || "pendente",
    };
  });

  const totalPages = count ? Math.ceil(count / pageSize) : 1;

  return (
    <DashboardPage 
      titulo="Historico" 
      subtitulo="Consulte analises anteriores por data, fornecedor e origem." 
      eyebrow="Auditoria operacional">
      <HistoricoListaClient
        initialAnalises={analisesFormatadas}
        totalPages={totalPages}
        currentPage={page}
      />
    </DashboardPage>
  );
}

