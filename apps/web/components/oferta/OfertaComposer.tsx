"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  Loader2,
  Sparkles,
  XCircle,
  Zap,
} from "lucide-react";
import { BancoDadosUpload } from "@/components/oferta/BancoDadosUpload";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const EMPRESA_ID_PADRAO = process.env.NEXT_PUBLIC_EMPRESA_ID_PADRAO ?? null;

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
  const [bancoPersistido, setBancoPersistido] = useState(false);
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

      // Sucesso — limpar formulário e mostrar modal
      setTextoBruto("");
      setFornecedor("");
      setModal("sucesso");

      // Redirecionar automaticamente após 5s se o usuário não fechar
      redirectTimerRef.current = setTimeout(irParaHistorico, 5000);
    } catch (error) {
      setErroMsg(error instanceof Error ? error.message : "Falha inesperada. Tente novamente.");
      setModal("erro");
    } finally {
      setIsLoading(false);
    }
  };

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
          <div className="grid gap-4 xl:grid-cols-[1.45fr_1fr]">
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
                  <p className="ds-eyebrow">Oferta do WhatsApp</p>
                  <p className="mt-1 text-sm text-secondary">
                    Cole a mensagem recebida do fornecedor, com lista, promocao, imagem convertida em texto ou tabela copiada.
                  </p>
                </div>
                <Textarea
                  className={compact ? "min-h-[160px]" : "min-h-[220px]"}
                  value={textoBruto}
                  onChange={(event) => setTextoBruto(event.target.value)}
                  placeholder="Ex.: PARACETAMOL 500MG C/20 R$ 12,50"
                />
              </div>
            </div>
            <BancoDadosUpload
              arquivo={arquivoBanco}
              onArquivoChange={setArquivoBanco}
              bancoPersistido={bancoPersistido}
              onRemoverBancoPersistido={() => {
                sessionStorage.removeItem("banco_cliente_importado");
                setBancoPersistido(false);
              }}
              titulo="Banco do cliente"
              descricao="Importe CSV, XLSX, XLS, XML, TXT, ZIP e outras exportacoes comuns para enriquecer a analise."
            />
          </div>

          <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
            <p className="text-sm text-secondary">
              A analise compara preco ofertado, menor historico, estoque atual, equivalentes e sugestao de pedido.{" "}
              {EMPRESA_ID_PADRAO
                ? "As configuracoes da empresa conectada tambem entram na classificacao."
                : "Defina `NEXT_PUBLIC_EMPRESA_ID_PADRAO` para usar configuracoes reais da empresa na classificacao."}
            </p>
            <div className="sticky bottom-3 z-10 rounded-[24px] bg-[linear-gradient(180deg,rgb(var(--bg-card) / 0.82),rgb(var(--bg-card-strong) / 0.94))] p-2 backdrop-blur md:static md:bg-none md:p-0 md:backdrop-blur-0">
              <Button
                className="h-14 w-full gap-2 rounded-2xl text-base px-6 md:min-w-[220px] md:w-auto"
                disabled={!textoBruto.trim() || isLoading}
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
