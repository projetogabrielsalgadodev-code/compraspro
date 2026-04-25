"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, FileSpreadsheet, FolderUp, X } from "lucide-react";

const FORMATOS_SUPORTADOS = ".csv,.xlsx,.xls,.xml,.txt,.zip";

// Limite de arquivo: 50MB (consistente com o bucket Supabase Storage 'uploads-temp')
const MAX_FILE_SIZE_MB = 50;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

interface BancoDadosUploadProps {
  arquivo: File | null;
  onArquivoChange?: (arquivo: File | null) => void;
  bancoPersistido?: boolean;
  onRemoverBancoPersistido?: () => void;
  titulo?: string;
  descricao?: string;
}

export function BancoDadosUpload({
  arquivo,
  onArquivoChange,
  bancoPersistido = false,
  onRemoverBancoPersistido,
  titulo = "Base do cliente",
  descricao = "Importe a base em CSV, XLSX, XLS, XML, TXT, ZIP ou outros formatos comuns de exportacao."
}: BancoDadosUploadProps) {
  const somenteVisual = !onArquivoChange;
  const [sizeError, setSizeError] = useState<string | null>(null);

  return (
    <div className="ds-subpanel rounded-[24px] p-4 sm:p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="ds-eyebrow">{titulo}</p>
          <p className="mt-2 text-sm text-secondary">{descricao}</p>
        </div>
        <span className="ds-icon-chip shrink-0 text-primariaapp">
          <FileSpreadsheet className="h-5 w-5" />
        </span>
      </div>

      {bancoPersistido && !arquivo ? (
        <div className="mt-4 flex items-center justify-between gap-3 rounded-[20px] border border-app bg-[#0c1a12] px-4 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#122b1c] text-[#34d399]">
              <CheckCircle2 className="h-4 w-4" />
            </span>
            <div>
              <p className="truncate text-sm font-semibold text-[#34d399]">Base Ativa e Sincronizada</p>
              <p className="mt-1 text-xs text-secondary">Utilizando banco de dados processado nesta sessão.</p>
            </div>
          </div>
          {onRemoverBancoPersistido && (
            <button
              type="button"
              onClick={onRemoverBancoPersistido}
              className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-app text-secondary transition hover:border-app-strong hover:text-texto"
              aria-label="Remover banco"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      ) : (
        <>
          <label className="mt-4 block cursor-pointer rounded-[22px] border border-dashed border-[rgb(var(--accent-secondary) / 0.35)] bg-[linear-gradient(180deg,rgba(255,255,255,0.03),rgb(var(--bg-input) / 0.88))] px-4 py-6 text-center shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] transition hover:border-[rgb(var(--accent-secondary) / 0.55)] hover:bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgb(var(--bg-input) / 0.96))]">
            <input
              type="file"
              accept={FORMATOS_SUPORTADOS}
              className="sr-only"
              disabled={somenteVisual}
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                if (file && file.size > MAX_FILE_SIZE_BYTES) {
                  setSizeError(`O arquivo excede o limite de ${MAX_FILE_SIZE_MB}MB. Tamanho: ${(file.size / 1024 / 1024).toFixed(1)}MB.`);
                  event.target.value = "";
                  return;
                }
                setSizeError(null);
                onArquivoChange?.(file);
              }}
            />
            <FolderUp className="mx-auto h-6 w-6 text-primariaapp" />
            <p className="mt-3 text-sm font-semibold text-texto">{somenteVisual ? "Visualizar area de importacao" : "Selecionar arquivo do banco de dados"}</p>
            <p className="mt-1 text-xs text-secondary">Formatos aceitos: CSV, XLSX, XLS, XML, TXT e ZIP. Máx. {MAX_FILE_SIZE_MB}MB.</p>
          </label>

          {sizeError && (
            <div className="mt-3 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3">
              <AlertTriangle className="h-4 w-4 text-red-400 shrink-0" />
              <p className="text-xs text-red-400">{sizeError}</p>
            </div>
          )}

          {arquivo ? (
            <div className="mt-4 flex items-center justify-between gap-3 rounded-[20px] border border-app bg-[linear-gradient(180deg,rgba(255,255,255,0.04),rgb(var(--bg-input) / 0.92))] px-4 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-texto">{arquivo.name}</p>
                <p className="mt-1 text-xs text-secondary">{(arquivo.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              {onArquivoChange ? (
                <button
                  type="button"
                  onClick={() => onArquivoChange(null)}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-app text-secondary transition hover:border-app-strong hover:text-texto"
                  aria-label="Remover arquivo"
                >
                  <X className="h-4 w-4" />
                </button>
              ) : null}
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
