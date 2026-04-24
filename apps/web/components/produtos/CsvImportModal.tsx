"use client";

import { useState, useRef } from "react";
import { Upload, Download, FileSpreadsheet, CheckCircle2, AlertTriangle, Loader2, X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface ImportResult {
  sucesso: boolean;
  linhas_processadas: number;
  inseridos: number;
  atualizados: number;
  erros_count: number;
  erros: { linha: string; erro: string }[];
}

interface CsvImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImportComplete: () => void;
}

const CSV_TEMPLATE = `ean,descricao,fabricante,principio_ativo,estoque,demanda_mes,custo_medio,preco_venda,curva_abc,grupo
7891234567890,PARACETAMOL 500MG C/20,MEDLEY,PARACETAMOL,150,45,8.50,12.90,A,ANALGESICOS
7894561230000,DIPIRONA 1G C/10,EMS,DIPIRONA,200,80,5.20,8.50,A,ANALGESICOS
7891111222333,AMOXICILINA 500MG C/21,EUROFARMA,AMOXICILINA,50,15,22.00,35.90,B,ANTIBIOTICOS`;

export function CsvImportModal({ open, onOpenChange, onImportComplete }: CsvImportModalProps) {
  const [arquivo, setArquivo] = useState<File | null>(null);
  const [preview, setPreview] = useState<string[][] | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [resultado, setResultado] = useState<ImportResult | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDownloadTemplate = () => {
    const blob = new Blob([CSV_TEMPLATE], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "modelo_produtos_compraspro.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setArquivo(file);
    setResultado(null);
    setErro(null);

    // Parse preview
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      const lines = text.split("\n").filter(l => l.trim());
      const previewLines = lines.slice(0, 6).map(line => {
        // Simple CSV split (handles basic cases)
        return line.split(/[,;]/).map(c => c.trim().replace(/^"|"$/g, ""));
      });
      setPreview(previewLines);
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    if (!arquivo) return;

    setIsUploading(true);
    setErro(null);
    setResultado(null);

    try {
      const formData = new FormData();
      formData.append("arquivo", arquivo, arquivo.name);

      const response = await fetch("/api/produtos/importar-csv", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || data?.error || "Erro ao importar CSV.");
      }

      setResultado(data as ImportResult);
      onImportComplete();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Erro inesperado ao importar.");
    } finally {
      setIsUploading(false);
    }
  };

  const reset = () => {
    setArquivo(null);
    setPreview(null);
    setResultado(null);
    setErro(null);
    if (inputRef.current) inputRef.current.value = "";
  };

  const handleClose = (open: boolean) => {
    if (!open) reset();
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[640px] border-app-strong bg-[rgb(var(--bg-card))]">
        <DialogHeader>
          <DialogTitle className="text-texto flex items-center gap-2">
            <FileSpreadsheet className="h-5 w-5 text-primariaapp" />
            Importar Produtos via CSV
          </DialogTitle>
          <DialogDescription className="text-secondary">
            Faça upload de um arquivo CSV com seus produtos para cadastro em massa no sistema.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Download template */}
          <div className="ds-subpanel rounded-2xl p-4 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-texto">Modelo CSV</p>
              <p className="text-xs text-secondary mt-0.5">
                Baixe o modelo e preencha com seus dados. Colunas obrigatórias: <strong>ean</strong> e <strong>descricao</strong>.
              </p>
            </div>
            <Button variant="secondary" size="sm" onClick={handleDownloadTemplate} className="shrink-0 gap-2">
              <Download className="h-4 w-4" />
              Baixar modelo
            </Button>
          </div>

          {/* Upload area */}
          {!resultado && (
            <div
              className={`relative border-2 border-dashed rounded-2xl p-8 text-center transition-colors cursor-pointer ${
                arquivo
                  ? "border-primariaapp/40 bg-[rgb(var(--accent-primary) / 0.05)]"
                  : "border-app hover:border-app-strong"
              }`}
              onClick={() => inputRef.current?.click()}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
              {arquivo ? (
                <div className="space-y-2">
                  <FileSpreadsheet className="h-8 w-8 text-primariaapp mx-auto" />
                  <p className="text-sm font-semibold text-texto">{arquivo.name}</p>
                  <p className="text-xs text-secondary">
                    {(arquivo.size / 1024).toFixed(1)} KB — Clique para trocar
                  </p>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      reset();
                    }}
                  >
                    <X className="h-3 w-3 mr-1" /> Remover
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="h-8 w-8 text-secondary/40 mx-auto" />
                  <p className="text-sm font-medium text-texto">Arraste ou clique para selecionar</p>
                  <p className="text-xs text-secondary">Aceita apenas arquivos .csv</p>
                </div>
              )}
            </div>
          )}

          {/* Preview */}
          {preview && preview.length > 0 && !resultado && (
            <div className="overflow-x-auto">
              <p className="ds-eyebrow mb-2">Pré-visualização ({preview.length - 1} linhas de dados)</p>
              <table className="w-full text-xs">
                <thead>
                  <tr>
                    {preview[0]?.map((col, i) => (
                      <th key={i} className="px-2 py-1.5 text-left font-semibold text-texto border-b border-borderapp uppercase tracking-wider">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.slice(1, 6).map((row, i) => (
                    <tr key={i} className="hover:bg-[var(--surface-highlight)]">
                      {row.map((cell, j) => (
                        <td key={j} className="px-2 py-1.5 text-secondary border-b border-borderapp/50 truncate max-w-[120px]">
                          {cell || "—"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Error */}
          {erro && (
            <div className="flex items-start gap-3 p-4 rounded-2xl bg-descartavel/10 border border-descartavel/20">
              <AlertTriangle className="h-5 w-5 text-descartavel shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-texto">Erro na importação</p>
                <p className="text-xs text-secondary mt-1">{erro}</p>
              </div>
            </div>
          )}

          {/* Result */}
          {resultado && (
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-4 rounded-2xl bg-ouro/10 border border-ouro/20">
                <CheckCircle2 className="h-5 w-5 text-ouro shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-texto">Importação concluída!</p>
                  <p className="text-xs text-secondary mt-1">
                    {resultado.linhas_processadas} linhas processadas
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="bg-[var(--surface-highlight)] rounded-xl px-4 py-3 text-center">
                  <p className="text-[10px] uppercase tracking-wider text-secondary">Inseridos</p>
                  <p className="text-lg font-bold text-ouro">{resultado.inseridos}</p>
                </div>
                <div className="bg-[var(--surface-highlight)] rounded-xl px-4 py-3 text-center">
                  <p className="text-[10px] uppercase tracking-wider text-secondary">Atualizados</p>
                  <p className="text-lg font-bold text-primariaapp">{resultado.atualizados}</p>
                </div>
                <div className="bg-[var(--surface-highlight)] rounded-xl px-4 py-3 text-center">
                  <p className="text-[10px] uppercase tracking-wider text-secondary">Erros</p>
                  <p className={`text-lg font-bold ${resultado.erros_count > 0 ? "text-descartavel" : "text-texto"}`}>
                    {resultado.erros_count}
                  </p>
                </div>
              </div>

              {resultado.erros.length > 0 && (
                <div className="max-h-[120px] overflow-y-auto">
                  <p className="ds-eyebrow mb-1">Detalhes dos erros:</p>
                  {resultado.erros.map((e, i) => (
                    <p key={i} className="text-xs text-secondary">
                      Linha {e.linha}: {e.erro}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="ghost"
            onClick={() => handleClose(false)}
            className="text-secondary"
          >
            {resultado ? "Fechar" : "Cancelar"}
          </Button>
          {!resultado && (
            <Button
              onClick={handleImport}
              disabled={!arquivo || isUploading}
              className="bg-[linear-gradient(135deg,rgb(var(--accent-primary)),rgb(var(--accent-secondary)))] text-white font-semibold"
            >
              {isUploading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              {isUploading ? "Importando..." : "Importar CSV"}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
