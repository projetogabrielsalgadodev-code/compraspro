import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, Database, FileSpreadsheet, FileText, Clock, User, Building2 } from "lucide-react";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = {
  title: "Inputs da Análise | Compras PRO",
  description: "Visualize os dados de entrada fornecidos para esta análise.",
};

function formatBytes(bytes: number | null): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default async function InputsPage({ params }: { params: { id: string } }) {
  const analiseId = params.id;
  const supabase = await createClient();

  const { data: analise, error } = await supabase
    .from("analises_oferta")
    .select("id, entrada_bruta, fonte_dados, nome_arquivo_historico, tamanho_arquivo_historico, fornecedor, origem, created_at, status, usuario_id, perfis(nome, email)")
    .eq("id", analiseId)
    .single();

  if (error || !analise) {
    return (
      <DashboardPage titulo="Inputs da Análise" subtitulo="Dados de entrada não encontrados." eyebrow="Visualização">
        <Card className="py-16 text-center">
          <p className="text-lg font-semibold text-texto mb-2">Análise não encontrada</p>
          <p className="text-sm text-secondary mb-6">O ID informado não corresponde a nenhuma análise registrada.</p>
          <Button asChild variant="secondary">
            <Link href="/historico">Voltar ao Histórico</Link>
          </Button>
        </Card>
      </DashboardPage>
    );
  }

  const dataFormatada = analise.created_at
    ? new Intl.DateTimeFormat("pt-BR", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
        timeZone: "America/Sao_Paulo",
      }).format(new Date(analise.created_at))
    : "—";

  const fonteDados = analise.fonte_dados || analise.origem || "banco";
  const isArquivo = fonteDados === "arquivo";
  const perfilRaw = analise.perfis as unknown;
  const perfil = Array.isArray(perfilRaw) ? (perfilRaw[0] as { nome: string; email: string } | undefined) ?? null : (perfilRaw as { nome: string; email: string } | null);

  return (
    <DashboardPage
      titulo="Inputs da Análise"
      subtitulo={`Dados de entrada fornecidos para a análise ${analiseId.substring(0, 8)}...`}
      eyebrow="Rastreabilidade"
    >
      <div className="space-y-6">
        {/* Botões de navegação */}
        <div className="flex flex-wrap gap-3">
          <Button asChild variant="secondary" className="gap-2">
            <Link href={`/resultado/${analiseId}`}>
              <ArrowLeft className="h-4 w-4" />
              Voltar ao Resultado
            </Link>
          </Button>
        </div>

        {/* Metadados em grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* Fonte de Dados */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <span className="ds-icon-chip text-primariaapp">
                  {isArquivo ? <FileSpreadsheet className="h-4 w-4" /> : <Database className="h-4 w-4" />}
                </span>
                <p className="ds-eyebrow">Fonte de dados</p>
              </div>
              <p className="text-lg font-semibold text-texto">
                {isArquivo ? "Arquivo enviado" : "Banco de dados"}
              </p>
              <p className="text-xs text-secondary mt-1">
                {isArquivo
                  ? "Histórico via planilha do usuário"
                  : "Histórico do banco interno do sistema"}
              </p>
            </CardContent>
          </Card>

          {/* Fornecedor */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <span className="ds-icon-chip text-primariaapp">
                  <Building2 className="h-4 w-4" />
                </span>
                <p className="ds-eyebrow">Fornecedor</p>
              </div>
              <p className="text-lg font-semibold text-texto">
                {analise.fornecedor || "Não informado"}
              </p>
            </CardContent>
          </Card>

          {/* Data */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <span className="ds-icon-chip text-primariaapp">
                  <Clock className="h-4 w-4" />
                </span>
                <p className="ds-eyebrow">Data da análise</p>
              </div>
              <p className="text-lg font-semibold text-texto">{dataFormatada}</p>
            </CardContent>
          </Card>

          {/* Usuário */}
          <Card>
            <CardContent className="p-5">
              <div className="flex items-center gap-3 mb-3">
                <span className="ds-icon-chip text-primariaapp">
                  <User className="h-4 w-4" />
                </span>
                <p className="ds-eyebrow">Usuário</p>
              </div>
              <p className="text-lg font-semibold text-texto">
                {perfil?.nome || "—"}
              </p>
              <p className="text-xs text-secondary mt-1">{perfil?.email || ""}</p>
            </CardContent>
          </Card>
        </div>

        {/* Arquivo histórico (se aplicável) */}
        {isArquivo && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <span className="ds-icon-chip text-primariaapp">
                  <FileSpreadsheet className="h-4 w-4" />
                </span>
                <div>
                  <p className="ds-eyebrow">Arquivo de histórico enviado</p>
                  <CardTitle className="mt-1 text-xl">
                    {analise.nome_arquivo_historico || "Arquivo não registrado"}
                  </CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="ds-subpanel rounded-2xl p-4 flex items-center gap-6">
                <div>
                  <p className="text-xs text-secondary">Nome do arquivo</p>
                  <p className="font-medium text-texto">{analise.nome_arquivo_historico || "—"}</p>
                </div>
                <div>
                  <p className="text-xs text-secondary">Tamanho</p>
                  <p className="font-medium text-texto">{formatBytes(analise.tamanho_arquivo_historico)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Texto da oferta */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <span className="ds-icon-chip text-primariaapp">
                <FileText className="h-4 w-4" />
              </span>
              <div>
                <p className="ds-eyebrow">Texto da oferta (entrada bruta)</p>
                <CardTitle className="mt-1 text-xl">Conteúdo enviado para análise</CardTitle>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="ds-subpanel rounded-2xl p-5 max-h-[600px] overflow-y-auto">
              {analise.entrada_bruta ? (
                <pre className="whitespace-pre-wrap break-words text-sm text-texto font-mono leading-relaxed">
                  {analise.entrada_bruta}
                </pre>
              ) : (
                <p className="text-secondary text-sm italic">Nenhum texto de oferta registrado para esta análise.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardPage>
  );
}
