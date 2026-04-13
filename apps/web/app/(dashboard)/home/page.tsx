import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, Clock3, Waves } from "lucide-react";

export const metadata: Metadata = { title: "Central de Análise" };
import { OfertaComposer } from "@/components/oferta/OfertaComposer";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/server";

export default async function HomePage() {
  const supabase = await createClient();

  const { count: ofertasPendentes } = await supabase
    .from("analises_oferta")
    .select("*", { count: "exact", head: true })
    .eq("status", "pendente");

  const { count: oportunidades } = await supabase
    .from("itens_oferta")
    .select("*", { count: "exact", head: true })
    .in("classificacao", ["ouro", "prata"]);

  const { count: estoqueCritico } = await supabase
    .from("produtos")
    .select("*", { count: "exact", head: true })
    .lte("estoque", 0);

  const metricas = [
    { titulo: "Ofertas pendentes", valor: (ofertasPendentes || 0).toString().padStart(2, "0"), detalhe: "Aguardando leitura estruturada" },
    { titulo: "Oportunidades ativas", valor: (oportunidades || 0).toString().padStart(2, "0"), detalhe: "Itens classificados como ouro ou prata" },
    { titulo: "Estoque critico", valor: (estoqueCritico || 0).toString().padStart(2, "0"), detalhe: "Produtos abaixo ou igual a zero" }
  ];

  const { data: analises } = await supabase
    .from("analises_oferta")
    .select("*, itens_oferta(id, classificacao)")
    .order("created_at", { ascending: false })
    .limit(3);

  const analisesRecentes = (analises || []).map((analise) => {
    const totalItens = analise.itens_oferta ? analise.itens_oferta.length : 0;
    const opps = analise.itens_oferta
      ? analise.itens_oferta.filter((i: any) => i.classificacao === 'ouro' || i.classificacao === 'prata').length
      : 0;

    const dateObj = new Date(analise.created_at);
    const dataFormatada = new Intl.DateTimeFormat("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(dateObj);

    return {
      id: analise.id,
      fornecedor: analise.fornecedor || "Fornecedor Sem Nome",
      itens: `${totalItens} itens`,
      oportunidades: `${opps} oportunidades`,
      horario: dataFormatada,
    };
  });

  return (
    <DashboardPage titulo="Central de analise de ofertas" subtitulo="Receba mensagens, extraia itens, compare com historico e tome decisao com contexto de estoque em segundos." eyebrow="Fila comercial">
        <OfertaComposer eyebrow="Nova analise" titulo="Cole uma mensagem e gere o resumo executivo" badge="Decisao antes de dados" compact />

        <section className="grid gap-4 sm:grid-cols-3">
          {metricas.map((metrica) => (
            <Card key={metrica.titulo}>
              <CardContent className="p-5">
                <div className="flex items-center justify-between gap-3">
                  <p className="ds-eyebrow">{metrica.titulo}</p>
                  <span className="ds-icon-chip text-primariaapp"><Waves className="h-4 w-4" /></span>
                </div>
                <p className="mt-4 text-4xl font-semibold tracking-tight text-texto">{metrica.valor}</p>
                <p className="mt-2 text-sm text-secondary">{metrica.detalhe}</p>
              </CardContent>
            </Card>
          ))}
        </section>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="ds-eyebrow">Historico recente</p>
                <CardTitle className="mt-2 text-2xl">Ultimas analises processadas</CardTitle>
              </div>
              <Button asChild variant="secondary">
                <Link href="/historico">
                  Ver historico
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {analisesRecentes.length > 0 ? analisesRecentes.map(({ id, fornecedor, itens, oportunidades, horario }) => (
              <Link key={id} href={`/resultado/${id}`} className="block">
                <div className="ds-subpanel flex flex-col gap-3 rounded-[24px] px-4 py-4 md:flex-row md:items-center md:justify-between hover:border-app-strong transition-colors">
                  <div>
                    <p className="text-base font-semibold text-texto">{fornecedor}</p>
                    <div className="mt-1 flex flex-wrap gap-3 text-sm text-secondary">
                      <span>{itens}</span>
                      <span>{oportunidades}</span>
                    </div>
                  </div>
                  <div className="inline-flex items-center gap-2 text-sm text-secondary">
                    <Clock3 className="h-4 w-4" />
                    {horario}
                  </div>
                </div>
              </Link>
            )) : (
              <p className="text-sm text-secondary py-4">Nenhuma analise encontrada no historico recente.</p>
            )}
          </CardContent>
        </Card>
    </DashboardPage>
  );
}
