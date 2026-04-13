import { Metadata } from "next";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { ProdutosListaClient, ProdutoListado } from "@/components/produtos/ProdutosListaClient";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Produtos | Compras PRO",
  description: "Consulte o catálogo de produtos, fabricantes e estoque disponível.",
};

interface ProdutosPageProps {
  searchParams: {
    page?: string;
    query?: string;
    estoque?: string;
  };
}

export default async function ProdutosPage({ searchParams }: ProdutosPageProps) {
  const supabase = await createClient();

  const page = parseInt(searchParams?.page || "1", 10);
  const query = searchParams?.query || "";
  const estoque = searchParams?.estoque || "todos";

  const pageSize = 20;

  // Supabase query builder
  let supabaseQuery = supabase
    .from("produtos")
    .select("*", { count: "exact" });

  if (query) {
    supabaseQuery = supabaseQuery.or(`descricao.ilike.%${query}%,ean.ilike.%${query}%,fabricante.ilike.%${query}%`);
  }

  if (estoque === "com_estoque") {
    supabaseQuery = supabaseQuery.gt("estoque", 0);
  } else if (estoque === "sem_estoque") {
    supabaseQuery = supabaseQuery.lte("estoque", 0);
  }

  const from = (page - 1) * pageSize;
  const to = from + pageSize - 1;

  const { data: produtos, count } = await supabaseQuery
    .order("descricao", { ascending: true })
    .range(from, to);

  const formattedProdutos: ProdutoListado[] = (produtos || []).map((p) => ({
    id: p.id,
    ean: p.ean || "",
    nome: p.descricao || p.ean || "Produto sem descricao",
    ativo: p.principio_ativo || "-",
    fabricante: p.fabricante || p.fabricante_bruto || "-",
    estoque: p.estoque || 0,
  }));

  const totalPages = count ? Math.ceil(count / pageSize) : 1;

  return (
    <DashboardPage
      titulo="Produtos"
      subtitulo="Busque produtos, princípios ativos, fabricantes e estoques."
      eyebrow="Base cadastrada"
    >
      <ProdutosListaClient 
        initialProdutos={formattedProdutos} 
        totalPages={totalPages} 
        currentPage={page} 
      />
    </DashboardPage>
  );
}
