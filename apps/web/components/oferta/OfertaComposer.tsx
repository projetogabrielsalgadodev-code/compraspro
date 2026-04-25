"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  Database,
  FileSpreadsheet,
  FileUp,
  Loader2,
  Sparkles,
  XCircle,
  Zap,
} from "lucide-react";
import { BancoDadosUpload } from "@/components/oferta/BancoDadosUpload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const EMPRESA_ID_PADRAO = process.env.NEXT_PUBLIC_EMPRESA_ID_PADRAO ?? null;

// Limite de arquivo: 50MB (consistente com o bucket Supabase Storage 'uploads-temp')
const MAX_FILE_SIZE_MB = 50;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

type FonteDados = "banco" | "arquivo";

interface OfertaComposerProps {
  eyebrow: string;
  titulo: string;
  descricao?: string;
  badge?: string;
  compact?: boolean;
}

type ModalState = "sucesso" | "erro" | null;

// ─── Modal de confirmação de análise iniciada ────────────────────────────────
function AnaliseIniciadaModal({
  open,
  erroMsg,
  onClose,
  onVerHistorico,
}: {
  open: ModalState;
  erroMsg?: string;
  onClose: () => void;
  onVerHistorico: () => void;
}) {
  // Fechar com ESC
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  const isSucesso = open === "sucesso";

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(0,0,0,0.55)", backdropFilter: "blur(6px)" }}
      onClick={onClose}
    >
      {/* Card do modal */}
      <div
        className="relative w-full max-w-md overflow-hidden rounded-[32px] border border-app-strong bg-[rgb(var(--bg-card))] shadow-[0_32px_80px_rgba(0,0,0,0.4)]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Gradiente decorativo no topo */}
        <div
          className="pointer-events-none absolute inset-x-0 top-0 h-40"
          style={{
            background: isSucesso
              ? "radial-gradient(ellipse at 50% 0%, rgba(34,197,94,0.18) 0%, transparent 70%)"
              : "radial-gradient(ellipse at 50% 0%, rgba(239,68,68,0.18) 0%, transparent 70%)",
          }}
        />

        <div className="relative flex flex-col items-center gap-6 px-8 pb-8 pt-10 text-center">
          {/* Ícone central */}
          <div
            className={`flex h-20 w-20 items-center justify-center rounded-[24px] shadow-[0_12px_32px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.1)] ${
              isSucesso
                ? "bg-[linear-gradient(135deg,rgba(34,197,94,0.25),rgba(34,197,94,0.08))] border border-green-500/30"
                : "bg-[linear-gradient(135deg,rgba(239,68,68,0.25),rgba(239,68,68,0.08))] border border-red-500/30"
            }`}
          >
            {isSucesso ? (
              <CheckCircle2 className="h-10 w-10 text-green-400" />
            ) : (
              <XCircle className="h-10 w-10 text-red-400" />
            )}
          </div>

          {/* Título */}
          <div className="space-y-2">
            <h2 className="text-xl font-bold tracking-tight text-texto">
              {isSucesso ? "Análise iniciada com sucesso!" : "Não foi possível iniciar"}
            </h2>
            <p className="text-sm leading-relaxed text-secondary">
              {isSucesso
                ? "Seu pedido foi recebido e está sendo processado pela IA. Você pode acompanhar o andamento em tempo real no histórico de análises."
                : (erroMsg ?? "Ocorreu um erro inesperado ao enviar a oferta. Verifique sua conexão e tente novamente.")}
            </p>
          </div>

          {/* Info cards (só no sucesso) */}
          {isSucesso && (
            <div className="grid w-full grid-cols-2 gap-3">
              <div className="flex flex-col items-center gap-2 rounded-2xl border border-app bg-[rgb(var(--bg-card-strong))] p-3 shadow-[inset_0_1px_0_var(--surface-inset)]">
                <Zap className="h-5 w-5 text-primariaapp" />
                <p className="text-xs font-semibold text-texto">Processamento</p>
                <p className="text-[11px] text-secondary">Análise em background</p>
              </div>
              <div className="flex flex-col items-center gap-2 rounded-2xl border border-app bg-[rgb(var(--bg-card-strong))] p-3 shadow-[inset_0_1px_0_var(--surface-inset)]">
                <ClipboardList className="h-5 w-5 text-primariaapp" />
                <p className="text-xs font-semibold text-texto">Resultado</p>
                <p className="text-[11px] text-secondary">Disponível no histórico</p>
              </div>
            </div>
          )}

          {/* Ações */}
          <div className={`flex w-full gap-3 ${isSucesso ? "flex-col" : "flex-row"}`}>
            {isSucesso ? (
              <>
                <Button
                  className="h-12 w-full gap-2 rounded-2xl text-sm"
                  onClick={onVerHistorico}
                >
                  <ClipboardList className="h-4 w-4" />
                  Ver histórico de análises
                  <ArrowRight className="h-4 w-4" />
                </Button>
                <button
                  type="button"
                  onClick={onClose}
                  className="text-xs text-secondary hover:text-texto transition"
                >
                  Fazer nova análise
                </button>
              </>
            ) : (
              <>
                <Button
                  variant="secondary"
                  className="h-11 flex-1 rounded-2xl text-sm"
                  onClick={onClose}
                >
                  Tentar novamente
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Componente principal ────────────────────────────────────────────────────
export function OfertaComposer({ eyebrow, titulo, descricao, badge, compact = false }: OfertaComposerProps) {
  const router = useRouter();
  const [textoBruto, setTextoBruto] = useState("");
  const [fornecedor, setFornecedor] = useState("");
  const [arquivoBanco, setArquivoBanco] = useState<File | null>(null);
  const [arquivoOferta, setArquivoOferta] = useState<File | null>(null);
  const [bancoPersistido, setBancoPersistido] = useState(false);
  const [fonteDados, setFonteDados] = useState<FonteDados>("banco");
  const [isLoading, setIsLoading] = useState(false);
  const [modal, setModal] = useState<ModalState>(null);
  const [erroMsg, setErroMsg] = useState<string | undefined>(undefined);
  const redirectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (sessionStorage.getItem("banco_cliente_importado")) {
      setBancoPersistido(true);
    }
  }, []);

  useEffect(() => {
    return () => {
      if (redirectTimerRef.current) clearTimeout(redirectTimerRef.current);
    };
  }, []);

  const irParaHistorico = () => {
    setModal(null);
    router.push("/historico");
  };

  const onSubmit = async () => {
    setIsLoading(true);
    setModal(null);
    setErroMsg(undefined);

    try {
      if (arquivoBanco) {
        sessionStorage.setItem("banco_cliente_importado", "true");
        setBancoPersistido(true);
      }

      let analiseId: string | null = null;

      // Verifica se há algum arquivo para enviar
      const hasFiles = !!arquivoOferta || fonteDados === "arquivo";

      if (hasFiles) {
        // ─── Novo fluxo via Supabase Storage ─────────────────────────────
        // 1. Upload dos arquivos direto pro Supabase Storage (sem passar pela Vercel)
        // 2. Chama API leve com os paths do Storage
        // Isso elimina os limites de body size (4.5MB) e timeout da Vercel

        const { createClient } = await import("@/lib/supabase/client");
        const supabase = createClient();

        // Gerar ID único para este upload
        const { data: { user } } = await supabase.auth.getUser();
        if (!user) throw new Error("Usuário não autenticado.");

        const uploadId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
        let storagePaths: {
          storage_path_oferta?: string;
          storage_path_historico?: string;
          nome_arquivo_oferta?: string;
          nome_arquivo_historico?: string;
        } = {};

        // Upload arquivo de OFERTA para o Storage
        if (arquivoOferta) {
          if (arquivoOferta.size > MAX_FILE_SIZE_BYTES) {
            throw new Error(`O arquivo de oferta excede o limite de ${MAX_FILE_SIZE_MB}MB. Tamanho: ${(arquivoOferta.size / 1024 / 1024).toFixed(1)}MB.`);
          }
          const ext = arquivoOferta.name.split(".").pop() || "xlsx";
          const storagePath = `${user.id}/${uploadId}/oferta.${ext}`;
          const { error: uploadErr } = await supabase.storage
            .from("uploads-temp")
            .upload(storagePath, arquivoOferta, {
              cacheControl: "300",
              upsert: false,
            });
          if (uploadErr) {
            throw new Error(`Erro ao enviar arquivo de oferta: ${uploadErr.message}`);
          }
          storagePaths.storage_path_oferta = storagePath;
          storagePaths.nome_arquivo_oferta = arquivoOferta.name;
        }

        // Upload arquivo de HISTÓRICO (banco) para o Storage
        if (arquivoBanco && fonteDados === "arquivo") {
          if (arquivoBanco.size > MAX_FILE_SIZE_BYTES) {
            throw new Error(`O arquivo de histórico excede o limite de ${MAX_FILE_SIZE_MB}MB. Tamanho: ${(arquivoBanco.size / 1024 / 1024).toFixed(1)}MB.`);
          }
          const ext = arquivoBanco.name.split(".").pop() || "xlsx";
          const storagePath = `${user.id}/${uploadId}/historico.${ext}`;
          const { error: uploadErr } = await supabase.storage
            .from("uploads-temp")
            .upload(storagePath, arquivoBanco, {
              cacheControl: "300",
              upsert: false,
            });
          if (uploadErr) {
            throw new Error(`Erro ao enviar arquivo de histórico: ${uploadErr.message}`);
          }
          storagePaths.storage_path_historico = storagePath;
          storagePaths.nome_arquivo_historico = arquivoBanco.name;
        }

        // 2. Chamar API leve (JSON, sem arquivos) com os paths do Storage
        const payload = {
          texto_bruto: textoBruto || "",
          fonte_dados: fonteDados,
          fornecedor_informado: fornecedor.trim() || null,
          ...storagePaths,
        };

        const response = await fetch("/api/ofertas/analisar-via-storage", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          const detail = (body as any)?.detail ? ` (${(body as any).detail})` : '';
          throw new Error(((body as { error?: string })?.error ?? "Não foi possível iniciar a análise.") + detail);
        }

        const result = await response.json();
        analiseId = result.analise_id;
      } else {
        // ─── Modo BANCO DE DADOS sem arquivo: enviar via JSON ───────
        if (!textoBruto.trim()) {
          throw new Error("Cole o texto da oferta ou envie um arquivo de oferta.");
        }

        const payload: Record<string, unknown> = {
          texto_bruto: textoBruto,
          empresa_id: EMPRESA_ID_PADRAO,
        };
        if (fornecedor.trim()) {
          payload.fornecedor_informado = fornecedor.trim();
        }

        const response = await fetch("/api/ofertas/analisar-async", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          const detail = (body as any)?.detail ? ` (${(body as any).detail})` : '';
          throw new Error(((body as { error?: string })?.error ?? "Não foi possível iniciar a análise.") + detail);
        }

        const result = await response.json();
        analiseId = result.analise_id;
      }

      // Sucesso — limpar formulário e redirecionar para processamento com polling
      setTextoBruto("");
      setFornecedor("");
      setArquivoOferta(null);

      if (analiseId) {
        // Redirecionar imediatamente para a página de processamento com polling
        router.push(`/processando?id=${analiseId}`);
      } else {
        // Fallback caso não retorne ID
        setModal("sucesso");
        redirectTimerRef.current = setTimeout(irParaHistorico, 5000);
      }
    } catch (error) {
      setErroMsg(error instanceof Error ? error.message : "Falha inesperada. Tente novamente.");
      setModal("erro");
    } finally {
      setIsLoading(false);
    }
  };

  const podeSubmeter = (() => {
    const hasText = !!textoBruto.trim();
    const hasOfferFile = !!arquivoOferta;
    const hasInput = hasText || hasOfferFile;
    if (!hasInput) return false;
    if (fonteDados === "arquivo" && !arquivoBanco) return false;
    return true;
  })();

  return (
    <>
      {/* Modal de confirmação / erro */}
      <AnaliseIniciadaModal
        open={modal}
        erroMsg={erroMsg}
        onClose={() => {
          setModal(null);
          if (redirectTimerRef.current) clearTimeout(redirectTimerRef.current);
        }}
        onVerHistorico={irParaHistorico}
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="ds-eyebrow">{eyebrow}</p>
              <CardTitle className="mt-2 text-2xl">{titulo}</CardTitle>
              {descricao ? <p className="mt-2 max-w-3xl text-sm text-secondary">{descricao}</p> : null}
            </div>
            {badge ? (
              <div className="rounded-full border border-app bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgb(var(--bg-input) / 0.88))] px-4 py-2 text-xs font-medium text-secondary shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]">
                {badge}
              </div>
            ) : null}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* ─── Dropdown: Fonte de dados ─────────────────────────────────── */}
          <div className="ds-subpanel rounded-[24px] p-4 sm:p-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <p className="ds-eyebrow">Fonte de dados para análise</p>
                <p className="mt-1 text-sm text-secondary">
                  Escolha se a IA deve comparar a oferta com o banco de dados interno ou com os dados do arquivo enviado.
                </p>
              </div>
              <span className="ds-icon-chip shrink-0 text-primariaapp">
                {fonteDados === "banco" ? (
                  <Database className="h-5 w-5" />
                ) : (
                  <FileSpreadsheet className="h-5 w-5" />
                )}
              </span>
            </div>
            <div className="mt-3">
              <Select
                value={fonteDados}
                onValueChange={(val: FonteDados) => setFonteDados(val)}
              >
                <SelectTrigger
                  id="fonte-dados-select"
                  className="h-12 rounded-2xl border-app bg-[rgb(var(--bg-input))] text-sm font-medium text-texto"
                >
                  <SelectValue placeholder="Selecione a fonte de dados" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="banco">
                    <span className="flex items-center gap-2">
                      <Database className="h-4 w-4 text-primariaapp" />
                      Usar banco de dados
                    </span>
                  </SelectItem>
                  <SelectItem value="arquivo">
                    <span className="flex items-center gap-2">
                      <FileSpreadsheet className="h-4 w-4 text-primariaapp" />
                      Usar dados do arquivo enviado
                    </span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Descrição contextual */}
            <div className="mt-3 rounded-xl border border-app bg-[rgb(var(--bg-card-strong))] px-4 py-3">
              {fonteDados === "banco" ? (
                <p className="text-xs text-secondary leading-relaxed">
                  <span className="font-semibold text-texto">Modo Banco de Dados:</span>{" "}
                  A IA consultará o catálogo de produtos, histórico de preços e estoque cadastrados no sistema para comparar com a oferta.
                </p>
              ) : (
                <p className="text-xs text-secondary leading-relaxed">
                  <span className="font-semibold text-texto">Modo Arquivo:</span>{" "}
                  A IA utilizará os dados do arquivo enviado (CSV, XLSX) como referência histórica de preços. Ideal para comparar com uma base própria ou atualizada do cliente.
                  {!arquivoBanco && (
                    <span className="block mt-1 text-amber-400/80 font-medium">
                      ⚠ Selecione um arquivo abaixo para usar este modo.
                    </span>
                  )}
                </p>
              )}
            </div>
          </div>

          <div className={fonteDados === "arquivo" ? "grid gap-4 xl:grid-cols-[1.45fr_1fr]" : "grid gap-4 grid-cols-1"}>
            <div className="space-y-4">
              <div>
                <div className="mb-2">
                  <p className="ds-eyebrow">Nome do fornecedor</p>
                  <p className="mt-1 text-sm text-secondary">
                    Identifique a origem da oferta para buscas futuras (opcional).
                  </p>
                </div>
                <Input
                  value={fornecedor}
                  onChange={(event) => setFornecedor(event.target.value)}
                  placeholder="Ex.: Distribuidora XYZ"
                />
              </div>
              <div>
                <div className="mb-2 mt-4">
                  <p className="ds-eyebrow">Oferta do fornecedor</p>
                  <p className="mt-1 text-sm text-secondary">
                    Cole a mensagem recebida do fornecedor (WhatsApp, e-mail, tabela copiada) ou envie um arquivo de oferta (XLSX, CSV).
                  </p>
                </div>
                <Textarea
                  className={compact ? "min-h-[160px]" : "min-h-[220px]"}
                  value={textoBruto}
                  onChange={(event) => setTextoBruto(event.target.value)}
                  placeholder={arquivoOferta ? "(Opcional — o arquivo de oferta será usado como entrada principal)" : "Ex.: PARACETAMOL 500MG C/20 R$ 12,50"}
                />

                {/* Upload de arquivo de oferta */}
                <div className="mt-3 ds-subpanel rounded-[20px] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold text-texto">Arquivo de oferta (XLSX, CSV)</p>
                      <p className="mt-1 text-xs text-secondary">Envie a oferta em formato planilha. O sistema extrairá automaticamente os produtos e preços.</p>
                    </div>
                    <span className="ds-icon-chip shrink-0 text-primariaapp">
                      <FileUp className="h-4 w-4" />
                    </span>
                  </div>
                  {arquivoOferta ? (
                    <div className="mt-3 flex items-center justify-between gap-3 rounded-[16px] border border-app bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgb(var(--bg-input) / 0.92))] px-4 py-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-texto">{arquivoOferta.name}</p>
                        <p className="mt-1 text-xs text-secondary">{(arquivoOferta.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setArquivoOferta(null)}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-app text-secondary transition hover:border-app-strong hover:text-texto"
                        aria-label="Remover arquivo de oferta"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <label className="mt-3 block cursor-pointer rounded-[16px] border border-dashed border-[rgb(var(--accent-secondary) / 0.35)] bg-[linear-gradient(180deg,rgba(255,255,255,0.02),rgb(var(--bg-input) / 0.85))] px-4 py-4 text-center transition hover:border-[rgb(var(--accent-secondary) / 0.55)]">
                      <input
                        type="file"
                        accept=".csv,.xlsx,.xls"
                        className="sr-only"
                        onChange={(event) => {
                          const file = event.target.files?.[0] ?? null;
                          if (file && file.size > MAX_FILE_SIZE_BYTES) {
                            setErroMsg(`O arquivo de oferta excede o limite de ${MAX_FILE_SIZE_MB}MB. Tamanho: ${(file.size / 1024 / 1024).toFixed(1)}MB.`);
                            setModal("erro");
                            event.target.value = "";
                            return;
                          }
                          setArquivoOferta(file);
                        }}
                      />
                      <FileUp className="mx-auto h-5 w-5 text-primariaapp" />
                      <p className="mt-2 text-xs font-medium text-texto">Selecionar arquivo de oferta</p>
                      <p className="mt-1 text-[10px] text-secondary">XLSX, CSV — Máx. {MAX_FILE_SIZE_MB}MB</p>
                    </label>
                  )}
                </div>
              </div>
            </div>
            {fonteDados === "arquivo" && (
              <BancoDadosUpload
                arquivo={arquivoBanco}
                onArquivoChange={setArquivoBanco}
                bancoPersistido={bancoPersistido}
                onRemoverBancoPersistido={() => {
                  sessionStorage.removeItem("banco_cliente_importado");
                  setBancoPersistido(false);
                }}
                titulo="Arquivo de Entradas (Obrigatório)"
                descricao="Importe sua planilha de Entradas (CSV ou XLSX) contendo histórico do recebimento e preços pagos. A IA usará esses dados como referência para a comparação."
              />
            )}
          </div>

          <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
            <p className="text-sm text-secondary">
              {fonteDados === "arquivo"
                ? "A análise comparará o preço ofertado com os dados do arquivo enviado, complementando com estoque e equivalentes do catálogo."
                : "A analise compara preco ofertado, menor historico, estoque atual, equivalentes e sugestao de pedido."}{" "}
              {EMPRESA_ID_PADRAO
                ? "As configuracoes da empresa conectada tambem entram na classificacao."
                : "Defina `NEXT_PUBLIC_EMPRESA_ID_PADRAO` para usar configuracoes reais da empresa na classificacao."}
            </p>
            <div className="sticky bottom-3 z-10 rounded-[24px] bg-[linear-gradient(180deg,rgb(var(--bg-card) / 0.82),rgb(var(--bg-card-strong) / 0.94))] p-2 backdrop-blur md:static md:bg-none md:p-0 md:backdrop-blur-0">
              <Button
                className="h-14 w-full gap-2 rounded-2xl text-base px-6 md:min-w-[220px] md:w-auto"
                disabled={!podeSubmeter || isLoading}
                onClick={onSubmit}
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Sparkles className="h-4 w-4" />
                )}
                {isLoading ? "Iniciando análise..." : "Analisar agora"}
                {!isLoading && <ArrowRight className="h-4 w-4" />}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </>
  );
}
