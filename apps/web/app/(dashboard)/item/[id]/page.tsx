import Link from "next/link";
import {
  BarChart3,
  Box,
  ChevronRight,
  Clock,
  Package,
  Tag,
} from "lucide-react";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OfferBadge } from "@/components/oferta/OfferBadge";
import { EquivalentsList } from "@/components/oferta/EquivalentsList";
import { formatarMoeda, formatarPercentual } from "@/lib/utils";
import { createClient } from "@/lib/supabase/server";

/* ── Cores do bloco de decisão por classificação ──────────────── */
const decisaoConfig: Record<string, { bg: string; border: string; label: string; emoji: string }> = {
  ouro: {
    bg: "bg-[linear-gradient(135deg,rgba(22,163,74,0.18),rgba(16,185,129,0.10))]",
    border: "border-ouro/30",
    label: "Recomendação: Comprar agora",
    emoji: "🥇",
  },
  prata: {
    bg: "bg-[linear-gradient(135deg,rgba(217,119,6,0.14),rgba(251,191,36,0.08))]",
    border: "border-prata/30",
    label: "Recomendação: Considerar compra",
    emoji: "🥈",
  },
  atencao: {
    bg: "bg-[linear-gradient(135deg,rgba(217,119,6,0.14),rgba(234,179,8,0.08))]",
    border: "border-atencao/30",
    label: "Recomendação: Avaliar com cuidado",
    emoji: "⚠️",
  },
  descartavel: {
    bg: "bg-[linear-gradient(135deg,rgba(220,38,38,0.14),rgba(248,113,113,0.08))]",
    border: "border-descartavel/30",
    label: "Recomendação: Não comprar",
    emoji: "❌",
  },
};

function DataRow({ label, value, highlight = false, valueClass = "" }: { label: string; value: React.ReactNode; highlight?: boolean; valueClass?: string }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-secondary">{label}</span>
      <span className={`font-medium ${highlight ? "text-primariaapp" : "text-texto"} ${valueClass}`}>
        {value}
      </span>
    </div>
  );
}

export default async function ItemDetalhePage({
  params,
  searchParams,
}: {
  params: { id: string };
  searchParams: { analise?: string };
}) {
  const supabase = await createClient();
  const itemId = params.id;
  const analiseId = searchParams.analise;

  // ── Buscar item da oferta no banco ─────────────────────────────
  const { data: itemDb } = await supabase
    .from("itens_oferta")
    .select("*, analises_oferta(id, fornecedor, created_at)")
    .eq("id", itemId)
    .single();

  if (!itemDb) {
    return (
      <DashboardPage titulo="Item não encontrado" subtitulo="O item solicitado não existe ou foi removido." eyebrow="Erro">
        <div className="py-12 text-center text-secondary">
          <p className="text-lg">Não foi possível localizar o item no banco de dados.</p>
          <Link href="/home" className="mt-4 inline-block text-primariaapp underline">Voltar para a home</Link>
        </div>
      </DashboardPage>
    );
  }

  const json = itemDb.dados_json || {};
  const classificacao = itemDb.classificacao || "atencao";
  const decisao = decisaoConfig[classificacao] || decisaoConfig.atencao;
  const analise = itemDb.analises_oferta as any;
  const fornecedorAnalise = analise?.fornecedor || "Análise";
  const analiseIdReal = analiseId || analise?.id;

  // Montar estrutura do item
  const item = {
    id: itemDb.id,
    ean: itemDb.ean,
    descricao_original: itemDb.descricao_bruta || json.descricao_original || "",
    descricao_produto: json.descricao_produto || null,
    preco_oferta: Number(itemDb.preco_oferta) || 0,
    menor_historico: itemDb.menor_preco_historico ? Number(itemDb.menor_preco_historico) : null,
    origem_menor_historico: itemDb.origem_menor_historico || null,
    variacao_percentual: itemDb.desconto_percentual ? Number(itemDb.desconto_percentual) : null,
    estoque_item: itemDb.estoque_item || 0,
    demanda_mes: itemDb.demanda_mes ? Number(itemDb.demanda_mes) : 0,
    sugestao_pedido: itemDb.sugestao_pedido || 0,
    estoque_equivalentes: itemDb.estoque_equivalentes || 0,
    classificacao: classificacao,
    confianca_match: itemDb.confianca_match || "baixo",
    recomendacao: itemDb.recomendacao || "",
    equivalente_detalhes: json.equivalentes || [],
  };

  // ── Buscar histórico real de preços pelo EAN ───────────────────
  let historicoPrecos: { data: string; preco: number }[] = [];
  if (item.ean) {
    const { data: historico } = await supabase
      .from("historico_precos")
      .select("data_entrada, preco_unitario")
      .eq("ean", item.ean)
      .not("preco_unitario", "is", null)
      .order("data_entrada", { ascending: true })
      .limit(12);

    if (historico && historico.length > 0) {
      historicoPrecos = historico.map((h) => {
        const dateObj = new Date(h.data_entrada);
        const label = new Intl.DateTimeFormat("pt-BR", { month: "short", year: "2-digit" }).format(dateObj);
        return { data: label, preco: Number(h.preco_unitario) };
      });
    }
  }

  const coberturaEstimada = item.demanda_mes && item.estoque_item
    ? Math.round((item.estoque_item / item.demanda_mes) * 30)
    : null;

  // ── SVG chart helpers ──────────────────────────────────────────
  const chartW = 100;
  const chartH = 40;
  let points = "";
  let ofertaY = 0;
  let hasChart = false;

  if (historicoPrecos.length >= 2) {
    hasChart = true;
    const maxPreco = Math.max(...historicoPrecos.map((h) => h.preco), item.preco_oferta);
    const minPreco = Math.min(...historicoPrecos.map((h) => h.preco), item.preco_oferta);
    const range = maxPreco - minPreco || 1;
    points = historicoPrecos.map((h, i) => {
      const x = (i / (historicoPrecos.length - 1)) * chartW;
      const y = chartH - ((h.preco - minPreco) / range) * chartH;
      return `${x},${y}`;
    }).join(" ");
    ofertaY = chartH - ((item.preco_oferta - minPreco) / range) * chartH;
  }

  // ── Data de sincronização ──────────────────────────────────────
  const dataSinc = analise?.created_at
    ? new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(analise.created_at))
    : "—";

  return (
    <DashboardPage
      titulo={item.descricao_produto ?? item.descricao_original}
      subtitulo={`EAN: ${item.ean ?? "Não identificado"} · Item: ${itemId.slice(0, 8)}`}
      eyebrow="Detalhe do item"
    >
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-secondary">
        <Link href="/home" className="hover:text-texto transition-colors">Home</Link>
        <ChevronRight className="h-3.5 w-3.5" />
        {analiseIdReal ? (
          <>
            <Link href={`/resultado/${analiseIdReal}`} className="hover:text-texto transition-colors">
              {fornecedorAnalise}
            </Link>
            <ChevronRight className="h-3.5 w-3.5" />
          </>
        ) : null}
        <span className="font-medium text-texto">{item.descricao_produto ?? item.descricao_original}</span>
      </nav>

      {/* ── Bloco de decisão — colorido por status ────────────── */}
      <Card className={`${decisao.bg} border ${decisao.border}`}>
        <CardContent className="px-6 py-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-4">
              <span className="text-4xl">{decisao.emoji}</span>
              <div>
                <OfferBadge classification={classificacao as any} />
                <p className="mt-2 text-xl font-bold text-texto">{decisao.label}</p>
                <p className="mt-1 max-w-xl text-sm text-secondary">{item.recomendacao}</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs uppercase tracking-wide text-muted-app">Preço da oferta</p>
              <p className="text-3xl font-bold text-texto">{formatarMoeda(item.preco_oferta)}</p>
              <p className={`mt-1 text-sm font-semibold ${
                (item.variacao_percentual ?? 0) > 0 ? "text-ouro" : "text-descartavel"
              }`}>
                {formatarPercentual(item.variacao_percentual)} vs histórico
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Grid de seções ──────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Dados da oferta */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <span className="ds-icon-chip text-primariaapp"><Tag className="h-4 w-4" /></span>
              <div>
                <p className="ds-eyebrow">Oferta</p>
                <CardTitle className="mt-1">Dados da proposta</CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <DataRow label="Descrição original" value={item.descricao_original} />
            <DataRow label="Produto correspondente" value={item.descricao_produto ?? "--"} />
            <DataRow label="EAN" value={item.ean ?? "Não identificado"} />
            <DataRow label="Confiança do match" value={item.confianca_match} />
            <DataRow label="Preço ofertado" value={formatarMoeda(item.preco_oferta)} highlight />
          </CardContent>
        </Card>

        {/* Histórico do item */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <span className="ds-icon-chip text-primariaapp"><BarChart3 className="h-4 w-4" /></span>
              <div>
                <p className="ds-eyebrow">Comparativo</p>
                <CardTitle className="mt-1">Histórico de preços</CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <DataRow label="Menor preço histórico" value={formatarMoeda(item.menor_historico)} />
            <DataRow label="Origem do menor" value={item.origem_menor_historico ?? "--"} />
            <DataRow label="Variação vs menor" value={formatarPercentual(item.variacao_percentual)} />

            {/* Gráfico SVG de linha — dados reais do historico_precos */}
            {hasChart ? (
              <div className="ds-subpanel rounded-[20px] p-4">
                <p className="mb-3 text-xs uppercase tracking-wide text-muted-app">Evolução de preço ({historicoPrecos.length} entradas)</p>
                <svg viewBox={`-4 -4 ${chartW + 8} ${chartH + 16}`} className="h-36 w-full" preserveAspectRatio="none">
                  <polygon
                    points={`0,${chartH} ${points} ${chartW},${chartH}`}
                    fill="rgb(var(--accent-primary) / 0.08)"
                  />
                  <polyline
                    points={points}
                    fill="none"
                    stroke="rgb(var(--accent-primary))"
                    strokeWidth="1.5"
                    strokeLinejoin="round"
                    vectorEffect="non-scaling-stroke"
                  />
                  <line
                    x1="0"
                    y1={ofertaY}
                    x2={chartW}
                    y2={ofertaY}
                    stroke="rgb(var(--accent-secondary))"
                    strokeWidth="1"
                    strokeDasharray="3,3"
                    vectorEffect="non-scaling-stroke"
                  />
                  <text x={chartW + 2} y={ofertaY + 1} fill="rgb(var(--accent-secondary))" fontSize="3" fontWeight="600">Oferta</text>
                </svg>
                <div className="mt-2 flex justify-between text-[10px] text-muted-app">
                  {historicoPrecos.map((h) => (
                    <span key={h.data}>{h.data}</span>
                  ))}
                </div>
              </div>
            ) : (
              <div className="ds-subpanel rounded-[20px] p-4 text-center">
                <p className="text-sm text-secondary">Sem histórico de preços disponível para este EAN.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Estoque e cobertura */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <span className="ds-icon-chip text-primariaapp"><Package className="h-4 w-4" /></span>
              <div>
                <p className="ds-eyebrow">Inventário</p>
                <CardTitle className="mt-1">Estoque e cobertura</CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <DataRow label="Estoque atual" value={`${item.estoque_item ?? 0} unidades`} />
            <DataRow label="Demanda mensal" value={`${item.demanda_mes ?? 0} unidades`} />
            {coberturaEstimada != null && (
              <DataRow
                label="Cobertura estimada"
                value={`${coberturaEstimada} dias`}
                highlight={coberturaEstimada < 30}
              />
            )}
            <DataRow label="Sugestão de pedido" value={`${item.sugestao_pedido ?? 0} unidades`} highlight />
            <DataRow label="Estoque de equivalentes" value={`${item.estoque_equivalentes ?? 0} unidades`} />
            <div className="my-2 h-px bg-app-strong" />
            <div className="flex items-center justify-between text-xs">
              <span className="flex items-center gap-1.5 text-secondary">
                <Clock className="h-3.5 w-3.5" />
                Data da análise
              </span>
              <span className="font-medium text-texto">{dataSinc}</span>
            </div>
          </CardContent>
        </Card>

        {/* Equivalentes */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <span className="ds-icon-chip text-primariaapp"><Box className="h-4 w-4" /></span>
              <div>
                <p className="ds-eyebrow">Produtos similares</p>
                <CardTitle className="mt-1">Equivalentes em estoque</CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <EquivalentsList items={item.equivalente_detalhes} />
          </CardContent>
        </Card>
      </div>
    </DashboardPage>
  );
}
