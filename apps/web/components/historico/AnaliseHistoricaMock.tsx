import { ArrowDownRight, ArrowUpRight, BadgeAlert, CircleDollarSign, type LucideIcon, Medal, ShieldAlert, Sparkles, TrendingUp, WalletCards } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const classificacoes = [
  { label: "Ouro", valor: 8, color: "bg-emerald-500", text: "text-emerald-600", fill: "from-emerald-500/30 to-emerald-400/10" },
  { label: "Prata", valor: 5, color: "bg-amber-500", text: "text-amber-600", fill: "from-amber-500/30 to-amber-400/10" },
  { label: "Atencao", valor: 4, color: "bg-orange-500", text: "text-orange-600", fill: "from-orange-500/30 to-orange-400/10" },
  { label: "Descartavel", valor: 7, color: "bg-rose-500", text: "text-rose-600", fill: "from-rose-500/28 to-rose-400/10" }
];

const oportunidades = [
  {
    titulo: "Paracetamol 500mg c/20",
    fornecedor: "Distribuidora XYZ",
    classificacao: "Ouro",
    economia: "23% abaixo do menor historico",
    estoque: "34 un",
    sugestao: "Comprar 50 un",
    cor: "emerald"
  },
  {
    titulo: "Omeprazol 20mg c/28",
    fornecedor: "Fornecedor ABC",
    classificacao: "Prata",
    economia: "11% abaixo da media historica",
    estoque: "18 un",
    sugestao: "Comprar 32 un",
    cor: "amber"
  },
  {
    titulo: "Dipirona gotas 10ml",
    fornecedor: "Distribuidora XYZ",
    classificacao: "Atencao",
    economia: "Preco competitivo, mas ha equivalentes em estoque",
    estoque: "96 un equivalentes",
    sugestao: "Revisar antes da compra",
    cor: "orange"
  }
];

const comparativoFornecedores = [
  { nome: "Distribuidora XYZ", desconto: 18, itens: 15 },
  { nome: "Fornecedor ABC", desconto: 11, itens: 10 },
  { nome: "Farmaceutica DEF", desconto: 7, itens: 8 }
];

const tendencia = [42, 38, 56, 63, 58, 72, 84];
const coberturaDias = [16, 24, 38, 52, 21];
const economiaBuckets = [
  { faixa: ">20%", itens: 8, cor: "from-emerald-500 to-emerald-400" },
  { faixa: "10-20%", itens: 5, cor: "from-cyan-500 to-sky-400" },
  { faixa: "1-9%", itens: 4, cor: "from-amber-500 to-yellow-400" },
  { faixa: "<=0%", itens: 7, cor: "from-rose-500 to-pink-400" }
];
const mixCurva = [
  { curva: "A", percentual: 46, valor: "46%" },
  { curva: "B", percentual: 34, valor: "34%" },
  { curva: "C", percentual: 20, valor: "20%" }
];

export function AnaliseHistoricaMock({ analiseId }: { analiseId: string }) {
  const maxTendencia = Math.max(...tendencia);
  const trendPoints = tendencia
    .map((valor, index) => {
      const x = 28 + (index * (100 - 56)) / (tendencia.length - 1);
      const y = 84 - (valor / maxTendencia) * 62;
      return `${x},${y}`;
    })
    .join(" ");
  const trendArea = `${trendPoints} 72,92 28,92`;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">
        <Card className="overflow-hidden">
          <CardHeader className="pb-3">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p className="ds-eyebrow">Analise consolidada</p>
                <CardTitle className="mt-2 text-3xl">Painel executivo da analise {analiseId}</CardTitle>
                <p className="mt-3 max-w-3xl text-sm text-secondary">
                  Distribuidora XYZ enviou 24 itens. O motor destacou oportunidades com maior desconto real, risco de excesso de estoque e margem de ganho por reposicao.
                </p>
              </div>
              <div className="rounded-[24px] border border-app bg-[linear-gradient(180deg,rgb(var(--bg-card-strong) / 1),rgb(var(--bg-input) / 0.96))] px-4 py-3 text-sm text-secondary">
                <p className="font-semibold text-texto">Insight principal</p>
                <p className="mt-1">Priorize itens ouro e prata com ruptura curta; segure os produtos com equivalente forte no estoque.</p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <KpiCard icon={CircleDollarSign} label="Economia potencial" value="R$ 6.420" detail="Capturando as melhores ofertas da lista" />
            <KpiCard icon={Medal} label="Itens prioritarios" value="13" detail="Ouro e prata com maior impacto" />
            <KpiCard icon={ShieldAlert} label="Itens para revisar" value="4" detail="Dependem de estoque equivalente" />
            <KpiCard icon={BadgeAlert} label="Descartados" value="7" detail="Acima da referencia ou sem ganho real" />
          </CardContent>
        </Card>

        <Card className="surface-accent overflow-hidden">
          <CardHeader className="pb-3">
            <p className="ds-eyebrow">Janela ideal</p>
            <CardTitle className="mt-2 text-2xl">Comprar agora os 8 itens ouro</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-[22px] border border-white/10 bg-[rgba(255,255,255,0.08)] p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-texto">Desconto medio capturado</p>
                  <p className="mt-1 text-sm text-secondary">Melhor equilibrio entre historico, cobertura e sugestao de pedido.</p>
                </div>
                <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-white/10 text-white">
                  <Sparkles className="h-5 w-5" />
                </span>
              </div>
              <div className="mt-4 flex items-end gap-2">
                <span className="text-4xl font-bold text-texto">18%</span>
                <span className="mb-1 inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2 py-1 text-xs font-semibold text-emerald-600">
                  <ArrowDownRight className="h-3.5 w-3.5" />
                  abaixo do historico
                </span>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <MiniSignal label="Sugestao de pedido" value="198 un" detail="Reposicao para 3 meses" />
              <MiniSignal label="Margem protegida" value="Alta" detail="Itens mais sensiveis cobertos" />
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <p className="ds-eyebrow">Distribuicao da analise</p>
            <CardTitle className="mt-2">Classificacao por qualidade da oferta</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex h-4 overflow-hidden rounded-full bg-[rgb(var(--bg-input) / 0.85)]">
              {classificacoes.map((item) => (
                <div
                  key={item.label}
                  className={cn(item.color, "h-full")}
                  style={{ width: `${(item.valor / 24) * 100}%` }}
                />
              ))}
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {classificacoes.map((item) => (
                <div key={item.label} className={cn("rounded-[22px] border border-app bg-gradient-to-br p-4", item.fill)}>
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-texto">{item.label}</p>
                    <span className={cn("text-xs font-semibold", item.text)}>{Math.round((item.valor / 24) * 100)}%</span>
                  </div>
                  <p className="mt-3 text-3xl font-bold text-texto">{item.valor}</p>
                  <p className="mt-1 text-sm text-secondary">Itens nessa faixa de decisao</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="ds-eyebrow">Tendencia da rodada</p>
                <CardTitle className="mt-2">Evolucao do ganho potencial por bloco analisado</CardTitle>
              </div>
              <span className="inline-flex items-center gap-2 rounded-full border border-app px-3 py-1 text-xs font-semibold text-secondary">
                <TrendingUp className="h-3.5 w-3.5 text-primariaapp" />
                leitura acumulada
              </span>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-[26px] border border-app bg-[radial-gradient(circle_at_top_left,rgb(var(--accent-primary) / 0.12),transparent_28%),linear-gradient(180deg,rgb(var(--bg-card-strong) / 0.98),rgb(var(--bg-input) / 0.88))] p-4 sm:p-5">
              <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-[24px] border border-app bg-[rgb(var(--bg-card) / 0.72)] p-4">
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-texto">Curva acumulada de ganho</p>
                      <p className="text-sm text-secondary">A leitura melhora conforme os blocos de itens ganham contexto historico.</p>
                    </div>
                    <div className="rounded-full bg-[rgb(var(--accent-primary) / 0.12)] px-3 py-1 text-xs font-semibold text-primariaapp">+42 pts</div>
                  </div>
                  <div className="relative h-[260px] overflow-hidden rounded-[22px] border border-app bg-[linear-gradient(180deg,rgb(var(--bg-input) / 0.64),rgb(var(--bg-card-strong) / 0.78))] p-4">
                    <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:100%_25%,14.285%_100%] opacity-60" />
                    <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
                      <defs>
                        <linearGradient id="trendFill" x1="0" x2="0" y1="0" y2="1">
                          <stop offset="0%" stopColor="rgba(59,130,246,0.34)" />
                          <stop offset="100%" stopColor="rgba(59,130,246,0.02)" />
                        </linearGradient>
                        <linearGradient id="trendStroke" x1="0" x2="1" y1="0" y2="0">
                          <stop offset="0%" stopColor="rgba(14,165,233,0.92)" />
                          <stop offset="100%" stopColor="rgba(59,130,246,1)" />
                        </linearGradient>
                      </defs>
                      <polygon points={trendArea} fill="url(#trendFill)" />
                      <polyline
                        points={trendPoints}
                        fill="none"
                        stroke="url(#trendStroke)"
                        strokeWidth="2.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                      {tendencia.map((valor, index) => {
                        const x = 28 + (index * (100 - 56)) / (tendencia.length - 1);
                        const y = 84 - (valor / maxTendencia) * 62;
                        return (
                          <g key={index}>
                            <circle cx={x} cy={y} r="3.2" fill="rgba(255,255,255,0.95)" />
                            <circle cx={x} cy={y} r="1.8" fill="rgba(59,130,246,1)" />
                          </g>
                        );
                      })}
                    </svg>
                    <div className="absolute inset-x-4 bottom-4 grid grid-cols-7 gap-2">
                      {tendencia.map((valor, index) => (
                        <div key={index} className="text-center">
                          <p className="text-sm font-semibold text-texto">{valor}%</p>
                          <p className="mt-1 text-[11px] uppercase tracking-[0.2em] text-secondary">B{index + 1}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="grid gap-4">
                  <div className="rounded-[24px] border border-app bg-[rgb(var(--bg-card) / 0.74)] p-4">
                    <p className="ds-eyebrow">Leitura por faixa</p>
                    <div className="mt-4 space-y-3">
                      {economiaBuckets.map((bucket) => (
                        <div key={bucket.faixa}>
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-semibold text-texto">{bucket.faixa}</span>
                            <span className="text-secondary">{bucket.itens} itens</span>
                          </div>
                          <div className="mt-2 h-2.5 rounded-full bg-[rgb(var(--bg-input) / 0.92)]">
                            <div className={cn("h-full rounded-full bg-gradient-to-r", bucket.cor)} style={{ width: `${(bucket.itens / 24) * 100}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[24px] border border-app bg-[rgb(var(--bg-card) / 0.74)] p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="ds-eyebrow">Aproveitamento</p>
                        <p className="mt-2 text-3xl font-bold text-texto">71%</p>
                      </div>
                      <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[rgb(var(--accent-secondary) / 0.12)] text-primariaapp">
                        <WalletCards className="h-5 w-5" />
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-secondary">Percentual da rodada que gerou oportunidade valida ou exigiu revisao qualificada.</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <Card>
          <CardHeader>
            <p className="ds-eyebrow">Cobertura de estoque</p>
            <CardTitle className="mt-2">Dias de cobertura dos itens mais sensiveis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 rounded-[24px] border border-app bg-[linear-gradient(180deg,rgb(var(--bg-card-strong) / 0.96),rgb(var(--bg-input) / 0.9))] p-4">
              {[
                ["Paracetamol 500mg", coberturaDias[0], "meta 30d"],
                ["Omeprazol 20mg", coberturaDias[1], "meta 30d"],
                ["Losartana 50mg", coberturaDias[2], "meta 30d"],
                ["Dipirona 1g", coberturaDias[3], "meta 15d"],
                ["Amoxicilina 500mg", coberturaDias[4], "meta 30d"]
              ].map(([nome, dias, meta]) => (
                <div key={nome as string} className="space-y-2 rounded-[20px] border border-app bg-[rgb(var(--bg-card) / 0.7)] p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-texto">{nome}</p>
                      <p className="text-xs text-secondary">{meta}</p>
                    </div>
                    <span className={cn(
                      "rounded-full px-2.5 py-1 text-xs font-semibold",
                      Number(dias) < 20 ? "bg-rose-500/12 text-rose-600" : Number(dias) < 35 ? "bg-amber-500/12 text-amber-600" : "bg-emerald-500/12 text-emerald-600"
                    )}>
                      {dias} dias
                    </span>
                  </div>
                  <div className="h-2.5 rounded-full bg-[rgb(var(--bg-input) / 0.9)]">
                    <div
                      className={cn(
                        "h-full rounded-full",
                        Number(dias) < 20 ? "bg-[linear-gradient(90deg,#fb7185,#f43f5e)]" : Number(dias) < 35 ? "bg-[linear-gradient(90deg,#f59e0b,#facc15)]" : "bg-[linear-gradient(90deg,#10b981,#34d399)]"
                      )}
                      style={{ width: `${Math.min((Number(dias) / 60) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <p className="ds-eyebrow">Mix estrategico</p>
            <CardTitle className="mt-2">Impacto por curva ABC e potencial financeiro</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 lg:grid-cols-[0.8fr_1.2fr]">
              <div className="rounded-[24px] border border-app bg-[linear-gradient(180deg,rgb(var(--bg-card-strong) / 0.96),rgb(var(--bg-input) / 0.9))] p-4">
                <p className="text-sm font-semibold text-texto">Participacao das curvas</p>
                <div className="mt-4 space-y-4">
                  {mixCurva.map((item) => (
                    <div key={item.curva}>
                      <div className="flex items-center justify-between text-sm">
                        <span className="font-semibold text-texto">Curva {item.curva}</span>
                        <span className="text-secondary">{item.valor}</span>
                      </div>
                      <div className="mt-2 h-3 rounded-full bg-[rgb(var(--bg-input) / 0.9)]">
                        <div
                          className={cn(
                            "h-full rounded-full",
                            item.curva === "A" && "bg-[linear-gradient(90deg,#2563eb,#38bdf8)]",
                            item.curva === "B" && "bg-[linear-gradient(90deg,#8b5cf6,#a78bfa)]",
                            item.curva === "C" && "bg-[linear-gradient(90deg,#f59e0b,#fbbf24)]"
                          )}
                          style={{ width: `${item.percentual}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-[24px] border border-app bg-[linear-gradient(180deg,rgb(var(--bg-card-strong) / 0.96),rgb(var(--bg-input) / 0.9))] p-4">
                <div className="mb-4 flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-texto">Economia projetada por prioridade</p>
                    <p className="text-sm text-secondary">Faixas com maior impacto no caixa e na reposicao imediata.</p>
                  </div>
                  <span className="rounded-full bg-[rgb(var(--accent-primary) / 0.12)] px-3 py-1 text-xs font-semibold text-primariaapp">R$ 6.420 total</span>
                </div>
                <div className="grid h-[220px] grid-cols-4 items-end gap-4">
                  {[
                    { label: "Ouro", valor: 4200, classe: "from-emerald-500 to-emerald-400" },
                    { label: "Prata", valor: 1480, classe: "from-cyan-500 to-sky-400" },
                    { label: "Atencao", valor: 560, classe: "from-amber-500 to-yellow-400" },
                    { label: "Desc.", valor: 180, classe: "from-slate-400 to-slate-300" }
                  ].map((item) => (
                    <div key={item.label} className="flex h-full flex-col justify-end gap-3">
                      <div className="relative flex-1 rounded-t-[22px] rounded-b-[10px] bg-[rgb(var(--bg-input) / 0.92)]">
                        <div
                          className={cn("absolute inset-x-0 bottom-0 rounded-t-[22px] rounded-b-[10px] bg-gradient-to-t shadow-[0_10px_24px_rgba(15,23,42,0.12)]", item.classe)}
                          style={{ height: `${(item.valor / 4200) * 100}%` }}
                        />
                      </div>
                      <div className="text-center">
                        <p className="text-sm font-semibold text-texto">R$ {item.valor.toLocaleString("pt-BR")}</p>
                        <p className="mt-1 text-[11px] uppercase tracking-[0.18em] text-secondary">{item.label}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 2xl:grid-cols-[1.05fr_0.95fr]">
        <Card>
          <CardHeader>
            <p className="ds-eyebrow">Boas ofertas</p>
            <CardTitle className="mt-2">Itens recomendados para compra ou revisao</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {oportunidades.map((item) => (
              <div key={item.titulo} className="rounded-[24px] border border-app bg-[linear-gradient(180deg,rgb(var(--bg-card) / 1),rgb(var(--bg-card-strong) / 0.94))] p-4 shadow-[0_12px_32px_rgba(15,23,42,0.06)]">
                <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-lg font-semibold text-texto">{item.titulo}</p>
                      <span className={cn(
                        "inline-flex rounded-full px-3 py-1 text-xs font-semibold",
                        item.cor === "emerald" && "bg-emerald-500/12 text-emerald-600",
                        item.cor === "amber" && "bg-amber-500/14 text-amber-600",
                        item.cor === "orange" && "bg-orange-500/14 text-orange-600"
                      )}>
                        {item.classificacao}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-secondary">{item.fornecedor}</p>
                  </div>
                  <div className="grid gap-2 text-sm text-secondary sm:grid-cols-3 xl:min-w-[420px]">
                    <DataPill label="Leitura de preco" value={item.economia} />
                    <DataPill label="Cobertura atual" value={item.estoque} />
                    <DataPill label="Acao" value={item.sugestao} />
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <p className="ds-eyebrow">Comparativo por fornecedor</p>
              <CardTitle className="mt-2">Quem trouxe o melhor pacote de desconto</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {comparativoFornecedores.map((item, index) => (
                <div key={item.nome} className="space-y-2">
                  <div className="flex items-center justify-between gap-3 text-sm">
                    <div>
                      <p className="font-semibold text-texto">{item.nome}</p>
                      <p className="text-secondary">{item.itens} itens aproveitaveis</p>
                    </div>
                    <span className="inline-flex items-center gap-1 rounded-full bg-[rgb(var(--accent-primary) / 0.1)] px-2 py-1 text-xs font-semibold text-primariaapp">
                      <ArrowUpRight className="h-3.5 w-3.5" />
                      {item.desconto}% ganho medio
                    </span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-full bg-[rgb(var(--bg-input) / 0.92)]">
                    <div
                      className={cn(
                        "h-full rounded-full",
                        index === 0 && "bg-[linear-gradient(90deg,rgba(16,185,129,0.95),rgba(34,197,94,0.82))]",
                        index === 1 && "bg-[linear-gradient(90deg,rgba(245,158,11,0.95),rgba(250,204,21,0.82))]",
                        index === 2 && "bg-[linear-gradient(90deg,rgba(59,130,246,0.95),rgba(14,165,233,0.82))]"
                      )}
                      style={{ width: `${Math.min(item.desconto * 4.5, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <p className="ds-eyebrow">Resumo de acao</p>
              <CardTitle className="mt-2">O que comprar agora</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                "Comprar imediatamente os 8 itens ouro para capturar o menor preco da rodada.",
                "Negociar volume dos 5 itens prata para ampliar a margem e reduzir ruptura.",
                "Revisar os 4 itens atencao com base no estoque de equivalentes antes de aprovar pedido.",
                "Ignorar os 7 descartaveis, pois o preco esta acima da referencia util."
              ].map((insight) => (
                <div key={insight} className="rounded-[20px] border border-app bg-[linear-gradient(180deg,rgb(var(--bg-card-strong) / 0.95),rgb(var(--bg-input) / 0.9))] px-4 py-3 text-sm text-secondary">
                  {insight}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}

function KpiCard({ icon: Icon, label, value, detail }: { icon: LucideIcon; label: string; value: string; detail: string }) {
  return (
    <div className="rounded-[24px] border border-app bg-[linear-gradient(180deg,rgb(var(--bg-card-strong) / 0.95),rgb(var(--bg-input) / 0.92))] p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="ds-eyebrow">{label}</p>
        <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-[rgb(var(--accent-primary) / 0.12)] text-primariaapp">
          <Icon className="h-4 w-4" />
        </span>
      </div>
      <p className="mt-4 text-3xl font-bold text-texto">{value}</p>
      <p className="mt-2 text-sm text-secondary">{detail}</p>
    </div>
  );
}

function MiniSignal({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-[20px] border border-app bg-[rgba(255,255,255,0.06)] px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-secondary">{label}</p>
      <p className="mt-2 text-2xl font-bold text-texto">{value}</p>
      <p className="mt-1 text-sm text-secondary">{detail}</p>
    </div>
  );
}

function DataPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[18px] border border-app bg-[rgb(var(--bg-input) / 0.72)] px-3 py-2">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-secondary">{label}</p>
      <p className="mt-1 font-semibold text-texto">{value}</p>
    </div>
  );
}
