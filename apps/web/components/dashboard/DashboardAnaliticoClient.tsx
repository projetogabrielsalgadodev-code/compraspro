"use client";

import { useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  AreaChart, Area,
} from "recharts";
import {
  ArrowLeft,
  TrendingUp, TrendingDown, Package, DollarSign, ShoppingCart,
  AlertTriangle, CheckCircle2, Eye, ShieldAlert,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { formatarMoeda, formatarPercentual } from "@/lib/utils";
import type { ItemOferta } from "@/types";

// Cores do design system
const CORES = {
  ouro: "#f59e0b",
  prata: "#94a3b8",
  atencao: "#f97316",
  descartavel: "#ef4444",
  primaria: "#6366f1",
  sucesso: "#34d399",
  info: "#38bdf8",
  roxo: "#a78bfa",
};

const CORES_CLASSIFICACAO = [CORES.ouro, CORES.prata, CORES.atencao, CORES.descartavel];

interface DashboardAnaliticoClientProps {
  analiseId: string;
  fornecedor: string;
  origem: string;
  criadoEm: string;
  itens: ItemOferta[];
}

export function DashboardAnaliticoClient({
  analiseId,
  fornecedor,
  origem,
  criadoEm,
  itens,
}: DashboardAnaliticoClientProps) {
  const router = useRouter();

  // ─── KPIs calculados ─────────────────────────────
  const kpis = useMemo(() => {
    const total = itens.length;
    const ouro = itens.filter((i) => i.classificacao === "ouro").length;
    const prata = itens.filter((i) => i.classificacao === "prata").length;
    const atencao = itens.filter((i) => i.classificacao === "atencao").length;
    const descartavel = itens.filter((i) => i.classificacao === "descartavel").length;

    const investimentoTotal = itens.reduce((sum, i) => {
      const qtde = i.sugestao_pedido ?? 0;
      return sum + (i.preco_oferta ?? 0) * qtde;
    }, 0);

    const economiaPotencial = itens.reduce((sum, i) => {
      if (i.variacao_percentual != null && i.variacao_percentual > 0 && i.menor_historico) {
        const qtde = i.sugestao_pedido ?? 0;
        return sum + (i.menor_historico - (i.preco_oferta ?? 0)) * qtde;
      }
      return sum;
    }, 0);

    const mediaVariacao = itens.length > 0
      ? itens.reduce((sum, i) => sum + (i.variacao_percentual ?? 0), 0) / itens.length
      : 0;

    const comEstoqueCritico = itens.filter((i) => {
      const estoque = i.estoque_item ?? 0;
      const demanda = i.demanda_mes ?? 1;
      return estoque < demanda;
    }).length;

    const taxaAproveitamento = total > 0 ? ((ouro + prata) / total) * 100 : 0;

    return {
      total, ouro, prata, atencao, descartavel,
      investimentoTotal, economiaPotencial, mediaVariacao,
      comEstoqueCritico, taxaAproveitamento,
    };
  }, [itens]);

  // ─── Dados dos gráficos ──────────────────────────
  const dadosPizza = useMemo(() => [
    { name: "Ouro", value: kpis.ouro, fill: CORES.ouro },
    { name: "Prata", value: kpis.prata, fill: CORES.prata },
    { name: "Atenção", value: kpis.atencao, fill: CORES.atencao },
    { name: "Descartável", value: kpis.descartavel, fill: CORES.descartavel },
  ].filter((d) => d.value > 0), [kpis]);

  const dadosBarraPreco = useMemo(() =>
    itens
      .filter((i) => i.menor_historico != null && i.menor_historico > 0)
      .slice(0, 15)
      .map((i) => ({
        nome: (i.descricao_produto ?? i.descricao_original).slice(0, 25),
        oferta: i.preco_oferta,
        historico: i.menor_historico ?? 0,
      })),
    [itens]
  );

  const dadosEstoqueDemanda = useMemo(() =>
    itens
      .filter((i) => (i.estoque_item ?? 0) > 0 || (i.demanda_mes ?? 0) > 0)
      .slice(0, 15)
      .map((i) => ({
        nome: (i.descricao_produto ?? i.descricao_original).slice(0, 25),
        estoque: i.estoque_item ?? 0,
        demanda: i.demanda_mes ?? 0,
        sugestao: i.sugestao_pedido ?? 0,
      })),
    [itens]
  );

  const dadosRadar = useMemo(() => {
    const totalComprar = kpis.ouro + kpis.prata;
    const totalRevisar = kpis.atencao;
    const totalDescartar = kpis.descartavel;
    const avgConfianca = itens.length > 0
      ? (itens.filter((i) => i.confianca_match === "alto").length / itens.length) * 100
      : 0;
    const avgEstoque = itens.length > 0
      ? itens.reduce((s, i) => s + (i.estoque_item ?? 0), 0) / itens.length
      : 0;
    const avgDemanda = itens.length > 0
      ? itens.reduce((s, i) => s + (i.demanda_mes ?? 0), 0) / itens.length
      : 0;

    return [
      { metrica: "Aprovação", valor: kpis.taxaAproveitamento },
      { metrica: "Confiança Match", valor: avgConfianca },
      { metrica: "Reco. Compra", valor: kpis.total > 0 ? (totalComprar / kpis.total) * 100 : 0 },
      { metrica: "Reco. Revisão", valor: kpis.total > 0 ? (totalRevisar / kpis.total) * 100 : 0 },
      { metrica: "Descarte", valor: kpis.total > 0 ? (totalDescartar / kpis.total) * 100 : 0 },
      { metrica: "Cobertura Estoque", valor: avgDemanda > 0 ? Math.min((avgEstoque / avgDemanda) * 100, 100) : 0 },
    ];
  }, [itens, kpis]);

  const dadosAreaVariacao = useMemo(() =>
    itens
      .filter((i) => i.variacao_percentual != null)
      .sort((a, b) => (b.variacao_percentual ?? 0) - (a.variacao_percentual ?? 0))
      .map((i) => ({
        nome: (i.descricao_produto ?? i.descricao_original).slice(0, 20),
        variacao: i.variacao_percentual ?? 0,
      })),
    [itens]
  );

  // Top oportunidades e riscos
  const topOportunidades = useMemo(() =>
    itens
      .filter((i) => i.variacao_percentual != null && i.variacao_percentual > 0)
      .sort((a, b) => (b.variacao_percentual ?? 0) - (a.variacao_percentual ?? 0))
      .slice(0, 5),
    [itens]
  );

  const topRiscos = useMemo(() =>
    itens
      .filter((i) => {
        const estoque = i.estoque_item ?? 0;
        const demanda = i.demanda_mes ?? 0;
        return estoque < demanda && demanda > 0;
      })
      .sort((a, b) => {
        const ratioA = (a.estoque_item ?? 0) / (a.demanda_mes ?? 1);
        const ratioB = (b.estoque_item ?? 0) / (b.demanda_mes ?? 1);
        return ratioA - ratioB;
      })
      .slice(0, 5),
    [itens]
  );

  const tooltipStyle = {
    contentStyle: {
      backgroundColor: "rgb(var(--bg-card))",
      border: "1px solid rgb(var(--border-app) / 0.3)",
      borderRadius: "16px",
      color: "rgb(var(--text-primary))",
      fontSize: "12px",
    },
  };

  // ─── Render ──────────────────────────────────────
  return (
    <div className="space-y-6">
      {/* Voltar para resultado */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          onClick={() => router.push(`/resultado/${analiseId}`)}
          className="gap-2 text-secondary hover:text-texto"
        >
          <ArrowLeft className="h-4 w-4" />
          Voltar ao resultado
        </Button>
        <div className="flex items-center gap-3 text-sm text-secondary">
          <span className="rounded-full bg-surface-subtle px-3 py-1 text-xs font-medium">
            {origem === "arquivo" ? "📄 Arquivo" : "💬 Texto"}
          </span>
          {criadoEm && (
            <span>
              {new Date(criadoEm).toLocaleDateString("pt-BR", {
                day: "2-digit", month: "short", year: "numeric",
                hour: "2-digit", minute: "2-digit",
              })}
            </span>
          )}
        </div>
      </div>

      {/* ═══ LINHA 1: KPIs Principais ═══ */}
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          titulo="Investimento Sugerido"
          valor={formatarMoeda(kpis.investimentoTotal)}
          descricao="Valor total dos pedidos sugeridos"
          icon={<DollarSign className="h-4 w-4" />}
          cor="text-emerald-500"
        />
        <KpiCard
          titulo="Economia Potencial"
          valor={formatarMoeda(kpis.economiaPotencial)}
          descricao="Comparado ao menor preço histórico"
          icon={<TrendingUp className="h-4 w-4" />}
          cor="text-sky-500"
        />
        <KpiCard
          titulo="Variação Média"
          valor={formatarPercentual(kpis.mediaVariacao)}
          descricao="Média de desconto sobre histórico"
          icon={kpis.mediaVariacao > 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
          cor={kpis.mediaVariacao > 0 ? "text-ouro" : "text-rose-500"}
        />
        <KpiCard
          titulo="Estoque Crítico"
          valor={`${kpis.comEstoqueCritico}`}
          descricao="Itens com estoque < demanda mensal"
          icon={<AlertTriangle className="h-4 w-4" />}
          cor="text-orange-500"
        />
      </section>

      {/* ═══ LINHA 2: Pizza de classificação + Radar ═══ */}
      <section className="grid gap-4 lg:grid-cols-2">
        {/* Gráfico de Pizza: Distribuição por Classificação */}
        <Card>
          <CardHeader>
            <div>
              <p className="ds-eyebrow">Distribuição</p>
              <CardTitle className="mt-2 text-lg">Classificação dos Itens</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center" style={{ height: 280 }}>
              {dadosPizza.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={dadosPizza}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={4}
                      dataKey="value"
                      label={({ name, percent }: { name?: string; percent?: number }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                      labelLine={false}
                      fontSize={11}
                    >
                      {dadosPizza.map((entry, index) => (
                        <Cell key={entry.name} fill={CORES_CLASSIFICACAO[index % CORES_CLASSIFICACAO.length]} />
                      ))}
                    </Pie>
                    <Tooltip {...tooltipStyle} />
                    <Legend wrapperStyle={{ fontSize: "12px" }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <p className="text-sm text-secondary">Nenhum item para exibir</p>
              )}
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Taxa de Aproveitamento" value={`${kpis.taxaAproveitamento.toFixed(1)}%`} icon={<CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />} />
              <Metric label="Total de Itens" value={`${kpis.total}`} icon={<Package className="h-3.5 w-3.5 text-sky-500" />} />
            </div>
          </CardContent>
        </Card>

        {/* Gráfico Radar: Perfil da Análise */}
        <Card>
          <CardHeader>
            <div>
              <p className="ds-eyebrow">Perfil</p>
              <CardTitle className="mt-2 text-lg">Radar da Análise</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={dadosRadar}>
                  <PolarGrid stroke="rgb(var(--border-app) / 0.3)" />
                  <PolarAngleAxis dataKey="metrica" tick={{ fontSize: 11, fill: "rgb(var(--text-secondary))" }} />
                  <PolarRadiusAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
                  <Radar
                    dataKey="valor"
                    stroke={CORES.primaria}
                    fill={CORES.primaria}
                    fillOpacity={0.25}
                    strokeWidth={2}
                  />
                  <Tooltip {...tooltipStyle} formatter={(value: any) => [`${Number(value).toFixed(1)}%`, "Valor"]} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="Itens Ouro" value={`${kpis.ouro}`} icon={<span className="inline-block h-3 w-3 rounded-full bg-[#f59e0b]" />} />
              <Metric label="Itens Prata" value={`${kpis.prata}`} icon={<span className="inline-block h-3 w-3 rounded-full bg-[#94a3b8]" />} />
            </div>
          </CardContent>
        </Card>
      </section>

      {/* ═══ LINHA 3: Comparativo de Preços ═══ */}
      {dadosBarraPreco.length > 0 && (
        <Card>
          <CardHeader>
            <div>
              <p className="ds-eyebrow">Comparativo Financeiro</p>
              <CardTitle className="mt-2 text-lg">Preço Oferta vs. Menor Histórico</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div style={{ height: 360 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dadosBarraPreco} layout="vertical" margin={{ left: 20, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border-app) / 0.2)" />
                  <XAxis type="number" tick={{ fontSize: 11, fill: "rgb(var(--text-secondary))" }} tickFormatter={(v) => `R$${v}`} />
                  <YAxis dataKey="nome" type="category" width={160} tick={{ fontSize: 10, fill: "rgb(var(--text-secondary))" }} />
                  <Tooltip {...tooltipStyle} formatter={(value: any) => [formatarMoeda(Number(value)), ""]} />
                  <Legend wrapperStyle={{ fontSize: "12px" }} />
                  <Bar dataKey="oferta" name="Preço Oferta" fill={CORES.primaria} radius={[0, 6, 6, 0]} barSize={14} />
                  <Bar dataKey="historico" name="Menor Histórico" fill={CORES.ouro} radius={[0, 6, 6, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ═══ LINHA 4: Variação de Preço (Área) ═══ */}
      {dadosAreaVariacao.length > 0 && (
        <Card>
          <CardHeader>
            <div>
              <p className="ds-eyebrow">Desempenho de Preço</p>
              <CardTitle className="mt-2 text-lg">Variação Percentual por Produto</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={dadosAreaVariacao} margin={{ left: 10, right: 10 }}>
                  <defs>
                    <linearGradient id="gradientVariacao" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={CORES.sucesso} stopOpacity={0.4} />
                      <stop offset="100%" stopColor={CORES.sucesso} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border-app) / 0.2)" />
                  <XAxis dataKey="nome" tick={{ fontSize: 9, fill: "rgb(var(--text-secondary))" }} angle={-35} textAnchor="end" height={80} />
                  <YAxis tick={{ fontSize: 11, fill: "rgb(var(--text-secondary))" }} tickFormatter={(v) => `${v}%`} />
                  <Tooltip {...tooltipStyle} formatter={(value: any) => [formatarPercentual(Number(value)), "Variação"]} />
                  <Area
                    type="monotone"
                    dataKey="variacao"
                    stroke={CORES.sucesso}
                    fill="url(#gradientVariacao)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ═══ LINHA 5: Estoque vs Demanda ═══ */}
      {dadosEstoqueDemanda.length > 0 && (
        <Card>
          <CardHeader>
            <div>
              <p className="ds-eyebrow">Gestão de Estoque</p>
              <CardTitle className="mt-2 text-lg">Estoque Atual vs. Demanda Mensal</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div style={{ height: 340 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dadosEstoqueDemanda} margin={{ left: 10, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--border-app) / 0.2)" />
                  <XAxis dataKey="nome" tick={{ fontSize: 9, fill: "rgb(var(--text-secondary))" }} angle={-35} textAnchor="end" height={80} />
                  <YAxis tick={{ fontSize: 11, fill: "rgb(var(--text-secondary))" }} />
                  <Tooltip {...tooltipStyle} />
                  <Legend wrapperStyle={{ fontSize: "12px" }} />
                  <Bar dataKey="estoque" name="Estoque Atual" fill={CORES.info} radius={[6, 6, 0, 0]} barSize={16} />
                  <Bar dataKey="demanda" name="Demanda/Mês" fill={CORES.atencao} radius={[6, 6, 0, 0]} barSize={16} />
                  <Bar dataKey="sugestao" name="Sugestão Pedido" fill={CORES.sucesso} radius={[6, 6, 0, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ═══ LINHA 6: Top Oportunidades + Riscos ═══ */}
      <section className="grid gap-4 lg:grid-cols-2">
        {/* Top Oportunidades */}
        <Card>
          <CardHeader>
            <div>
              <p className="ds-eyebrow">Destaques Positivos</p>
              <CardTitle className="mt-2 text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-500" />
                Melhores Oportunidades
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {topOportunidades.length > 0 ? (
              <div className="space-y-3">
                {topOportunidades.map((item, idx) => (
                  <div key={item.ean ?? idx} className="rounded-[16px] border border-app bg-inputapp p-3.5 transition hover:border-emerald-500/30">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-texto">{item.descricao_produto ?? item.descricao_original}</p>
                        <p className="mt-1 text-xs text-secondary">EAN: {item.ean ?? "N/A"}</p>
                      </div>
                      <span className="whitespace-nowrap rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-bold text-emerald-500">
                        {formatarPercentual(item.variacao_percentual)}
                      </span>
                    </div>
                    <div className="mt-2 flex gap-4 text-xs text-secondary">
                      <span>Oferta: <strong className="text-texto">{formatarMoeda(item.preco_oferta)}</strong></span>
                      <span>Histórico: <strong className="text-texto">{formatarMoeda(item.menor_historico)}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-8 text-center text-sm text-secondary">Nenhuma oportunidade com desconto encontrada</p>
            )}
          </CardContent>
        </Card>

        {/* Alertas de Estoque Crítico */}
        <Card>
          <CardHeader>
            <div>
              <p className="ds-eyebrow">Alertas Operacionais</p>
              <CardTitle className="mt-2 text-lg flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-orange-500" />
                Estoque Crítico
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            {topRiscos.length > 0 ? (
              <div className="space-y-3">
                {topRiscos.map((item, idx) => {
                  const estoque = item.estoque_item ?? 0;
                  const demanda = item.demanda_mes ?? 0;
                  const coberturaDias = demanda > 0 ? Math.round((estoque / demanda) * 30) : 0;
                  return (
                    <div key={item.ean ?? idx} className="rounded-[16px] border border-app bg-inputapp p-3.5 transition hover:border-orange-500/30">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-texto">{item.descricao_produto ?? item.descricao_original}</p>
                          <p className="mt-1 text-xs text-secondary">EAN: {item.ean ?? "N/A"}</p>
                        </div>
                        <span className="whitespace-nowrap rounded-full bg-orange-500/15 px-2.5 py-1 text-xs font-bold text-orange-500">
                          {coberturaDias}d cobertura
                        </span>
                      </div>
                      <div className="mt-2 flex gap-4 text-xs text-secondary">
                        <span>Estoque: <strong className="text-texto">{estoque}</strong></span>
                        <span>Demanda/mês: <strong className="text-texto">{demanda}</strong></span>
                        <span>Sugestão: <strong className="text-emerald-500">{item.sugestao_pedido ?? 0}</strong></span>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="py-8 text-center text-sm text-secondary">Nenhum produto com estoque crítico</p>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

// ─── Sub-componentes internos ────────────────────
function KpiCard({ titulo, valor, descricao, icon, cor }: {
  titulo: string;
  valor: string;
  descricao: string;
  icon: React.ReactNode;
  cor: string;
}) {
  return (
    <div className="ds-panel p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="ds-eyebrow">{titulo}</p>
        <span className={`ds-icon-chip ${cor}`}>{icon}</span>
      </div>
      <p className={`mt-4 text-3xl font-semibold tracking-tight text-texto`}>{valor}</p>
      <p className="mt-2 text-sm text-secondary">{descricao}</p>
    </div>
  );
}

function Metric({ label, value, icon }: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-2 rounded-[12px] border border-app bg-inputapp px-3 py-2">
      {icon}
      <div>
        <p className="text-xs text-secondary">{label}</p>
        <p className="text-sm font-semibold text-texto">{value}</p>
      </div>
    </div>
  );
}
