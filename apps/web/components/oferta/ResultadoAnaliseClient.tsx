"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart3, ClipboardList, ShieldAlert, Trophy, CheckSquare, Loader2,
  AlertTriangle, LayoutDashboard, Clock, Coins, Cpu, Search, ArrowLeft,
  ArrowRight, FileText,
} from "lucide-react";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { OfferCard } from "@/components/oferta/OfferCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatarMoeda, formatarPercentual } from "@/lib/utils";
import type { ClassificacaoOferta, ItemOferta, RespostaAnaliseOferta } from "@/types";
import { updateAnaliseStatus } from "@/app/(dashboard)/resultado/actions";

type FiltroResultado = "todos" | "comprar" | "nao-comprar" | "revisar" | "ouro" | "prata" | "atencao" | "descartavel";

const ITEMS_POR_PAGINA_TABELA = 10;
const ITEMS_POR_PAGINA_CARDS = 5;

const fallback: RespostaAnaliseOferta = {
  analise_id: "local",
  fornecedor: "Fornecedor de exemplo",
  origem: "texto",
  resumo: {
    itens_analisados: 1,
    oportunidades: 1,
    sem_necessidade: 0,
    revisar: 0
  },
  itens: [
    {
      ean: "7891234567890",
      descricao_original: "PARACETAMOL 500MG C/20 - R$ 12,50",
      descricao_produto: "Paracetamol 500mg - 20 comprimidos",
      preco_oferta: 12.5,
      classificacao: "ouro",
      confianca_match: "baixo",
      recomendacao: "Comprar agora. O preço está competitivo e o estoque atual não cobre o horizonte de 3 meses.",
      menor_historico: 15.7,
      origem_menor_historico: "= mesmo produto",
      variacao_percentual: 20.4,
      estoque_item: 34,
      demanda_mes: 28,
      sugestao_pedido: 50,
      estoque_equivalentes: 12,
      equivalente_detalhes: [
        { descricao: "Paracetamol 500mg - EMS", fabricante: "EMS", estoque: 6 },
        { descricao: "Paracetamol 500mg - Medley", fabricante: "Medley", estoque: 6 }
      ]
    },
    {
      ean: "7891234567891",
      descricao_original: "DIPIRONA 1G - OFERTA FLASH",
      descricao_produto: "Dipirona Monoidratada 1g",
      preco_oferta: 4.5,
      classificacao: "prata",
      confianca_match: "alto",
      recomendacao: "Considerar reposição. Ágio leve sobre melhor entrada, mas curva A com baixo estoque.",
      menor_historico: 4.25,
      origem_menor_historico: "= mesmo produto",
      variacao_percentual: -5.8,
      estoque_item: 10,
      demanda_mes: 30,
      sugestao_pedido: 80,
      estoque_equivalentes: 0,
      equivalente_detalhes: []
    }
  ]
};

/* C-28: Cor da variação por status */
function corVariacaoTabela(variacao?: number | null) {
  if (variacao == null) return "";
  if (variacao > 0) return "text-ouro font-semibold";
  if (variacao >= -10) return "text-prata font-semibold";
  return "text-descartavel font-semibold";
}

/* Mapeia classificação → filtro */
function classificacaoParaFiltro(c: ClassificacaoOferta): FiltroResultado {
  if (c === "ouro" || c === "prata") return "comprar";
  if (c === "descartavel") return "nao-comprar";
  return "revisar";
}

/* ─── Componente de paginação reutilizável ─────────────────────────────────── */
function Paginacao({
  paginaAtual,
  totalPaginas,
  onMudarPagina,
}: {
  paginaAtual: number;
  totalPaginas: number;
  onMudarPagina: (page: number) => void;
}) {
  const [pageInput, setPageInput] = useState(paginaAtual.toString());

  useEffect(() => {
    setPageInput(paginaAtual.toString());
  }, [paginaAtual]);

  if (totalPaginas <= 1) return null;

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 border-t border-borderapp pt-4">
      <p className="text-sm text-secondary">
        Página <span className="font-semibold text-texto">{paginaAtual}</span> de <span className="font-semibold text-texto">{totalPaginas}</span>
      </p>
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 mr-2">
          <span className="text-sm text-secondary whitespace-nowrap">Ir para:</span>
          <Input
            type="number"
            min={1}
            max={totalPaginas}
            value={pageInput}
            onChange={(e) => setPageInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                const page = parseInt(pageInput);
                if (!isNaN(page) && page >= 1 && page <= totalPaginas) onMudarPagina(page);
              }
            }}
            onBlur={() => setPageInput(paginaAtual.toString())}
            className="w-16 h-9"
          />
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onMudarPagina(paginaAtual - 1)}
          disabled={paginaAtual === 1}
        >
          <ArrowLeft className="mr-2 h-4 w-4" /> Anterior
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => onMudarPagina(paginaAtual + 1)}
          disabled={paginaAtual === totalPaginas}
        >
          Próxima <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export function ResultadoAnaliseClient({ analiseId, dadosIniciais }: { analiseId: string, dadosIniciais?: RespostaAnaliseOferta | null }) {
  const router = useRouter();
  const [dados, setDados] = useState<RespostaAnaliseOferta>(dadosIniciais || fallback);
  const [filtroAtivo, setFiltroAtivo] = useState<FiltroResultado>("todos");
  const [selecionados, setSelecionados] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSuccessToast, setShowSuccessToast] = useState(false);
  const [erroPedido, setErroPedido] = useState<string | null>(null);

  // Search & pagination state
  const [busca, setBusca] = useState("");
  const [buscaDebounced, setBuscaDebounced] = useState("");
  const [paginaTabela, setPaginaTabela] = useState(1);
  const [paginaCards, setPaginaCards] = useState(1);

  useEffect(() => {
    if (dadosIniciais) return; // If we already have server data, we don't need sessionStorage

    const raw = sessionStorage.getItem(`analise:${analiseId}`);
    if (!raw) return;
    try {
      setDados(JSON.parse(raw) as RespostaAnaliseOferta);
    } catch {
      setDados(fallback);
    }
  }, [analiseId, dadosIniciais]);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setBuscaDebounced(busca);
    }, 300);
    return () => clearTimeout(timer);
  }, [busca]);

  // Reset pagination when filters or search change
  useEffect(() => {
    setPaginaTabela(1);
    setPaginaCards(1);
  }, [filtroAtivo, buscaDebounced]);

  const itens = useMemo(() => dados.itens as ItemOferta[], [dados.itens]);

  /* Filtro por classificação */
  const itensFiltradosPorTipo = useMemo(() => {
    if (filtroAtivo === "todos") return itens;
    // Filtros por classificação direta
    if (["ouro", "prata", "atencao", "descartavel"].includes(filtroAtivo)) {
      return itens.filter((item) => item.classificacao === filtroAtivo);
    }
    // Filtros por ação (comprar, nao-comprar, revisar)
    return itens.filter((item) => classificacaoParaFiltro(item.classificacao) === filtroAtivo);
  }, [itens, filtroAtivo]);

  /* Filtro por busca textual */
  const itensFiltrados = useMemo(() => {
    if (!buscaDebounced.trim()) return itensFiltradosPorTipo;
    const termos = buscaDebounced.toLowerCase().trim().split(/\s+/);
    return itensFiltradosPorTipo.filter((item) => {
      const textoItem = [
        item.ean,
        item.descricao_original,
        item.descricao_produto,
        item.recomendacao,
        item.classificacao,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return termos.every((t) => textoItem.includes(t));
    });
  }, [itensFiltradosPorTipo, buscaDebounced]);

  /* Paginação da tabela */
  const totalPaginasTabela = Math.max(1, Math.ceil(itensFiltrados.length / ITEMS_POR_PAGINA_TABELA));
  const itensTabela = useMemo(() => {
    const start = (paginaTabela - 1) * ITEMS_POR_PAGINA_TABELA;
    return itensFiltrados.slice(start, start + ITEMS_POR_PAGINA_TABELA);
  }, [itensFiltrados, paginaTabela]);

  /* Paginação dos cards */
  const totalPaginasCards = Math.max(1, Math.ceil(itensFiltrados.length / ITEMS_POR_PAGINA_CARDS));
  const itensCards = useMemo(() => {
    const start = (paginaCards - 1) * ITEMS_POR_PAGINA_CARDS;
    return itensFiltrados.slice(start, start + ITEMS_POR_PAGINA_CARDS);
  }, [itensFiltrados, paginaCards]);

  const toggleSelecionado = (id: string) => {
    setSelecionados((prev) => prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]);
  };

  const toggleTodos = () => {
    const todosIds = itensFiltrados.map((i) => i.ean ?? i.descricao_original);
    if (selecionados.length === todosIds.length && todosIds.length > 0) {
      setSelecionados([]);
    } else {
      setSelecionados(todosIds);
    }
  };

  const handleGerarPedidos = async () => {
    setIsGenerating(true);
    setErroPedido(null);

    try {
       const itensDetalhados = itens.filter(i => selecionados.includes(i.ean ?? i.descricao_original));

       if (itensDetalhados.length === 0) return;

       let mensagem = "Olá, gostaria de confirmar o pedido dos seguintes itens da oferta:\n\n";
       
       itensDetalhados.forEach(item => {
           const nome = item.descricao_produto ?? item.descricao_original;
           // If suggestion is 0 but user selected it, default to 1 so order makes sense
           const qtde = item.sugestao_pedido && item.sugestao_pedido > 0 ? item.sugestao_pedido : 1;
           const preco = formatarMoeda(item.preco_oferta);
           mensagem += `- ${nome} | Qtd: ${qtde} | Preço: ${preco}\n`;
       });
       
       mensagem += "\nAguardo confirmação. Obrigado!";

       // Copiar para o clipboard
       await navigator.clipboard.writeText(mensagem);

       // Show success feedback and clear selection
       setShowSuccessToast(true);
       setSelecionados([]);
       setTimeout(() => setShowSuccessToast(false), 3000);
    } catch (e) {
       setErroPedido(e instanceof Error ? e.message : "Falha ao gerar texto do pedido.");
       setTimeout(() => setErroPedido(null), 5000);
    } finally {
       setIsGenerating(false);
    }
  };

  const filtros: { key: FiltroResultado; label: string; count: number }[] = [
    { key: "todos", label: "Todos", count: itens.length },
    { key: "comprar", label: "Comprar", count: itens.filter((i) => classificacaoParaFiltro(i.classificacao) === "comprar").length },
    { key: "nao-comprar", label: "Não comprar", count: itens.filter((i) => classificacaoParaFiltro(i.classificacao) === "nao-comprar").length },
    { key: "revisar", label: "Revisar", count: itens.filter((i) => classificacaoParaFiltro(i.classificacao) === "revisar").length },
  ];

  const filtrosClassificacao: { key: FiltroResultado; label: string; count: number; color: string }[] = [
    { key: "ouro", label: "🥇 Ouro", count: itens.filter((i) => i.classificacao === "ouro").length, color: "text-ouro" },
    { key: "prata", label: "🥈 Prata", count: itens.filter((i) => i.classificacao === "prata").length, color: "text-prata" },
    { key: "atencao", label: "⚠️ Atenção", count: itens.filter((i) => i.classificacao === "atencao").length, color: "text-atencao" },
    { key: "descartavel", label: "❌ Descartável", count: itens.filter((i) => i.classificacao === "descartavel").length, color: "text-descartavel" },
  ];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard eyebrow="Itens analisados" value={String(dados.resumo.itens_analisados)} description="Produtos lidos no processamento" icon={<ClipboardList className="h-4 w-4" />} />
        <MetricCard eyebrow="Boas oportunidades" value={String(dados.resumo.oportunidades)} description="Itens ouro ou prata" icon={<Trophy className="h-4 w-4" />} />
        <MetricCard eyebrow="Sem necessidade" value={String(dados.resumo.sem_necessidade)} description="Compras não recomendadas" icon={<BarChart3 className="h-4 w-4" />} />
        <MetricCard eyebrow="Revisar" value={String(dados.resumo.revisar)} description="Validações manuais pendentes" icon={<ShieldAlert className="h-4 w-4" />} />
      </section>

      {/* Métricas de processamento da IA */}
      {(dados.tempo_processamento_ms || dados.tokens_utilizados || dados.custo_reais) && (
        <div className="ds-subpanel flex flex-wrap items-center gap-6 rounded-2xl px-5 py-3">
          {dados.tempo_processamento_ms != null && dados.tempo_processamento_ms > 0 && (
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-primariaapp" />
              <span className="text-sm text-secondary">Tempo de processamento:</span>
              <span className="text-sm font-semibold text-texto">
                {dados.tempo_processamento_ms >= 1000
                  ? `${(dados.tempo_processamento_ms / 1000).toFixed(1)}s`
                  : `${dados.tempo_processamento_ms}ms`}
              </span>
            </div>
          )}
          {dados.tokens_utilizados != null && dados.tokens_utilizados > 0 && (
            <div className="flex items-center gap-2">
              <Cpu className="h-4 w-4 text-primariaapp" />
              <span className="text-sm text-secondary">Tokens utilizados:</span>
              <span className="text-sm font-semibold text-texto">
                {dados.tokens_utilizados.toLocaleString("pt-BR")}
              </span>
            </div>
          )}
          {dados.custo_reais != null && dados.custo_reais > 0 && (
            <div className="flex items-center gap-2">
              <Coins className="h-4 w-4 text-primariaapp" />
              <span className="text-sm text-secondary">Custo da análise:</span>
              <span className="text-sm font-semibold text-texto">
                {dados.custo_reais.toLocaleString("pt-BR", { style: "currency", currency: "BRL" })}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Controles: Status e Dashboard analítico */}
      <div className="flex flex-col sm:flex-row items-end sm:items-center justify-end gap-4">
        <div className="w-[200px]">
          <Select 
            value={dados.status || "pendente"} 
            onValueChange={async (val) => {
              const previousStatus = dados.status;
              setDados(prev => ({ ...prev, status: val }));
              const res = await updateAnaliseStatus(analiseId, val);
              if (res && res.error) {
                setDados(prev => ({ ...prev, status: previousStatus }));
              }
            }}
          >
            <SelectTrigger className={`border-none text-white font-semibold flex items-center gap-2 ${
               (dados.status || "pendente") === 'pendente' ? 'bg-red-500 hover:bg-red-600' :
               (dados.status || "pendente") === 'em andamento' ? 'bg-blue-500 hover:bg-blue-600' :
               'bg-green-500 hover:bg-green-600'
            }`}>
              <SelectValue placeholder="Status da Análise" />
            </SelectTrigger>
            <SelectContent className="bg-inputapp">
              <SelectItem value="pendente" className="text-red-500 font-medium">Pendente</SelectItem>
              <SelectItem value="em andamento" className="text-blue-500 font-medium">Em Andamento</SelectItem>
              <SelectItem value="concluida" className="text-green-500 font-medium">Concluída</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button
          onClick={() => router.push(`/resultado/${analiseId}/inputs`)}
          variant="secondary"
          className="gap-2 rounded-[8px]"
        >
          <FileText className="h-4 w-4" />
          Ver Inputs da Análise
        </Button>

        <Button
          onClick={() => router.push(`/dashboard/${analiseId}`)}
          className="gap-2 rounded-[8px] border-none bg-primaria px-6 py-3 font-semibold text-white shadow-primario transition-all hover:shadow-lg hover:brightness-110"
        >
          <LayoutDashboard className="h-4 w-4" />
          Ver Dashboard Analítico
        </Button>
      </div>

      {/* ─── Barra de busca + Filtros ─────────────────────────────────────────── */}
      <Card>
        <CardContent className="grid gap-4 p-5 md:grid-cols-[1fr_220px]">
          <div className="space-y-2">
            <p className="ds-eyebrow">Buscar item</p>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary" />
              <Input
                placeholder="EAN, descrição, recomendação..."
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="space-y-2">
            <p className="ds-eyebrow">Classificação</p>
            <Select
              value={filtroAtivo}
              onValueChange={(val) => setFiltroAtivo(val as FiltroResultado)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filtrar por tipo" />
              </SelectTrigger>
              <SelectContent className="bg-inputapp">
                <div className="px-2 py-1.5 text-xs font-semibold text-secondary">Por Ação</div>
                {filtros.map((f) => (
                  <SelectItem key={f.key} value={f.key}>
                    {f.label} ({f.count})
                  </SelectItem>
                ))}
                <div className="px-2 py-1.5 text-xs font-semibold text-secondary border-t border-borderapp mt-1 pt-2">Por Classificação</div>
                {filtrosClassificacao.map((f) => (
                  <SelectItem key={f.key} value={f.key}>
                    {f.label} ({f.count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Contagem de resultados */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-secondary">
          <span className="font-semibold text-texto">{itensFiltrados.length}</span>{" "}
          {itensFiltrados.length === 1 ? "item encontrado" : "itens encontrados"}
          {buscaDebounced && (
            <span> para &ldquo;<span className="text-primariaapp">{buscaDebounced}</span>&rdquo;</span>
          )}
        </p>
      </div>

      {/* ─── Resumo executivo (tabela paginada) ──────────────────────────────── */}
      <Card>
        <CardHeader>
          <div>
            <p className="ds-eyebrow">Prioridade operacional</p>
            <CardTitle className="mt-2 text-2xl">Resumo executivo</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="ds-subpanel overflow-x-auto rounded-[24px] p-4">
          {/* C-22: Tabela com caption e scope nos headers */}
          <table className="min-w-full text-left text-sm">
            <caption className="sr-only">Resumo executivo da análise de oferta — classificação e recomendação por item</caption>
            <thead className="text-secondary">
              <tr>
                <th scope="col" className="pb-3 pr-4 w-10">
                  <input type="checkbox" title="Selecionar todos" className="h-4 w-4 rounded border-[#2e3439] bg-transparent text-[#34d399] transition focus:ring-[#34d399] checked:bg-[#34d399] checked:border-transparent outline-none cursor-pointer" checked={itensFiltrados.length > 0 && selecionados.length === itensFiltrados.length} onChange={toggleTodos} />
                </th>
                <th scope="col" className="pb-3 pr-4">Cód. Barras</th>
                <th scope="col" className="pb-3 pr-4">Produto</th>
                <th scope="col" className="pb-3 pr-4">Preço oferta</th>
                <th scope="col" className="pb-3 pr-4">Menor histórico</th>
                <th scope="col" className="pb-3 pr-4">Var.%</th>
                <th scope="col" className="pb-3 pr-4">Estoque</th>
                <th scope="col" className="pb-3 pr-4">Demanda mês</th>
                <th scope="col" className="pb-3 pr-4">Sugestão pedido</th>
                <th scope="col" className="pb-3 pr-4">Estoque equivalentes</th>
                <th scope="col" className="pb-3 pr-4">Recomendação</th>
              </tr>
            </thead>
            <tbody>
              {itensTabela.length > 0 ? (
                itensTabela.map((item) => {
                  const idStr = item.ean ?? item.descricao_original;
                  return (
                  <tr key={`${item.ean}-${item.descricao_original}`} className="border-t border-app text-texto transition-colors hover:bg-white/5">
                    <td className="py-3 pr-4">
                      <input type="checkbox" title="Selecionar item" className="h-4 w-4 rounded border-[#2e3439] bg-transparent text-[#34d399] transition focus:ring-[#34d399] checked:bg-[#34d399] checked:border-transparent outline-none cursor-pointer" checked={selecionados.includes(idStr)} onChange={() => toggleSelecionado(idStr)} />
                    </td>
                    <td className="py-3 pr-4">{item.ean ?? "--"}</td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                         {item.descricao_produto ?? item.descricao_original}
                         {item.confianca_match === "baixo" && (
                           <span title="Confiança baixa na correspondência do EAN. Sugerimos validar." className="flex h-5 w-5 items-center justify-center rounded-full bg-orange-500/20 text-orange-500">
                             <AlertTriangle className="h-3.5 w-3.5" />
                           </span>
                         )}
                      </div>
                    </td>
                    <td className="py-3 pr-4">{formatarMoeda(item.preco_oferta)}</td>
                    <td className="py-3 pr-4">{item.menor_historico ? formatarMoeda(item.menor_historico) : "--"} {item.origem_menor_historico ?? ""}</td>
                    {/* C-28: Variação colorida por status */}
                    <td className={`py-3 pr-4 ${corVariacaoTabela(item.variacao_percentual)}`}>{formatarPercentual(item.variacao_percentual)}</td>
                    <td className="py-3 pr-4">{item.estoque_item ?? 0}</td>
                    <td className="py-3 pr-4">{item.demanda_mes ?? 0}</td>
                    <td className="py-3 pr-4">{item.sugestao_pedido ?? 0}</td>
                    <td className="py-3 pr-4">{item.estoque_equivalentes ?? 0}</td>
                    {/* C-29: Recomendação textual em vez de classificação crua */}
                    <td className="max-w-[200px] py-3 pr-4 text-xs">{item.recomendacao}</td>
                  </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={11} className="py-8 text-center text-secondary">
                    <Search className="h-8 w-8 mx-auto mb-2 text-secondary/30" />
                    <p className="font-medium text-texto">Nenhum item encontrado</p>
                    <p className="text-sm">Tente ajustar a busca ou os filtros.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          </div>

          <Paginacao
            paginaAtual={paginaTabela}
            totalPaginas={totalPaginasTabela}
            onMudarPagina={setPaginaTabela}
          />
        </CardContent>
      </Card>

      {/* C-19: Chips de filtro — Todos / Comprar / Não comprar / Revisar */}
      <div className="flex flex-wrap gap-2">
        {filtros.map((filtro) => (
          <button
            key={filtro.key}
            type="button"
            onClick={() => setFiltroAtivo(filtro.key)}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo ${
              filtroAtivo === filtro.key
                ? "bg-primaria text-white shadow-primario"
                : "border border-app bg-inputapp text-secondary hover:border-app-strong hover:text-texto"
            }`}
          >
            {filtro.label}
            <span className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-bold ${
              filtroAtivo === filtro.key ? "bg-white/20 text-white" : "bg-surface-subtle text-muted-app"
            }`}>
              {filtro.count}
            </span>
          </button>
        ))}
      </div>

      {/* ─── Cards detalhados (paginados) ─────────────────────────────────────── */}
      <section className="space-y-4">
        {itensCards.length > 0 ? (
          itensCards.map((item) => (
            <OfferCard key={`${item.ean}-${item.descricao_original}`} item={item} analiseId={analiseId} />
          ))
        ) : (
          <Card className="py-12 text-center">
            <Search className="h-10 w-10 mx-auto mb-3 text-secondary/30" />
            <p className="font-medium text-texto">Nenhum item encontrado</p>
            <p className="text-sm text-secondary">Tente ajustar a busca ou os filtros.</p>
          </Card>
        )}
      </section>

      <Paginacao
        paginaAtual={paginaCards}
        totalPaginas={totalPaginasCards}
        onMudarPagina={setPaginaCards}
      />

      {/* Float Action Bar */}
      {selecionados.length > 0 && !showSuccessToast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex animate-in slide-in-from-bottom-5 items-center gap-4 rounded-full border border-[rgba(52,211,153,0.3)] bg-[#0c1a12]/95 px-6 py-3 shadow-2xl backdrop-blur-md">
          <span className="text-sm font-medium text-[#c0ecd8]">
            <strong className="text-[#34d399]">{selecionados.length}</strong> {selecionados.length === 1 ? "item selecionado" : "itens selecionados"}
          </span>
          <Button 
            size="sm" 
            className="h-9 gap-2 rounded-full border-none bg-[#34d399] font-bold text-[#0c1a12] transition-colors hover:bg-[#10b981]"
            onClick={handleGerarPedidos}
            disabled={isGenerating}
          >
            {isGenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckSquare className="h-4 w-4" />}
            {isGenerating ? "Processando..." : "Gerar Pedido Aprovado"}
          </Button>
          {erroPedido && (
             <span className="text-sm font-semibold text-rose-500">{erroPedido}</span>
          )}
        </div>
      )}

      {/* Success Feedback Overlay */}
      {showSuccessToast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex animate-in slide-in-from-bottom-5 items-center gap-3 rounded-full border border-emerald-500/30 bg-[#0c1a12]/95 px-6 py-3 text-emerald-400 shadow-xl backdrop-blur-md">
          <CheckSquare className="h-5 w-5" />
          <span className="text-sm font-semibold">Mensagem copiada para a área de transferência!</span>
        </div>
      )}
    </div>
  );
}
