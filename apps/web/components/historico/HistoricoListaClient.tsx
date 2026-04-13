"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Clock3, History, Loader2, SearchX } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowLeft } from "lucide-react";
import { SyncIndicator } from "@/components/historico/SyncIndicator";

export interface AnaliseListada {
  id: string;
  fornecedor: string;
  itens: string;
  oportunidades: string;
  horario: string;
  status: string;
}

interface HistoricoListaClientProps {
  initialAnalises: AnaliseListada[];
  totalPages: number;
  currentPage: number;
}

export function HistoricoListaClient({
  initialAnalises,
  totalPages,
  currentPage,
}: HistoricoListaClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [busca, setBusca] = useState(searchParams.get("query") || "");
  const [pageInput, setPageInput] = useState(currentPage.toString());

  // Auto-refresh enquanto houver análises processando
  const temProcessando = initialAnalises.some((a) => a.status === "processando");

  const refreshPage = useCallback(() => {
    router.refresh();
  }, [router]);

  useEffect(() => {
    if (!temProcessando) return;
    const interval = setInterval(refreshPage, 8000);
    return () => clearInterval(interval);
  }, [temProcessando, refreshPage]);

  useEffect(() => {
    setPageInput(currentPage.toString());
  }, [currentPage]);

  // Debounce effect for search
  useEffect(() => {
    const timeOutId = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      const currentQuery = searchParams.get("query") || "";

      if (busca === currentQuery) return;

      if (busca) {
        params.set("query", busca);
      } else {
        params.delete("query");
      }
      params.set("page", "1"); // reset to page 1 on search
      router.replace(`${pathname}?${params.toString()}`);
    }, 400);

    return () => clearTimeout(timeOutId);
  }, [busca, pathname, router, searchParams]);

  const handleStatusChange = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value && value !== "todos") {
      params.set("status", value);
    } else {
      params.delete("status");
    }
    params.set("page", "1");
    router.replace(`${pathname}?${params.toString()}`);
  };

  const currentStatusFilter = searchParams.get("status") || "todos";

  const changePage = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages) return;
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", newPage.toString());
    router.push(`${pathname}?${params.toString()}`);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'processando':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 text-xs font-medium">
            <Loader2 className="h-3 w-3 animate-spin" />
            Processando
          </span>
        );
      case 'concluida':
        return <span className="px-2 py-0.5 rounded-full bg-green-500/10 text-green-500 text-xs font-medium">Concluída</span>;
      case 'erro':
        return <span className="px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 text-xs font-medium">Erro</span>;
      default:
        return <span className="px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-500 text-xs font-medium">Pendente</span>;
    }
  };

  return (
    <>
      {/* Banner quando há análises em processamento */}
      {temProcessando && (
        <div className="mb-4 flex items-center gap-3 rounded-2xl border border-blue-500/20 bg-blue-500/8 px-5 py-3 text-blue-400">
          <Loader2 className="h-4 w-4 animate-spin shrink-0" />
          <p className="text-sm">
            <span className="font-semibold">Análise em andamento.</span>{" "}
            Esta página será atualizada automaticamente quando o resultado estiver pronto.
          </p>
        </div>
      )}



      <Card className="mb-6">
        <CardContent className="grid gap-4 p-5 md:grid-cols-[1fr_200px]">
          <div className="space-y-2">
            <p className="ds-eyebrow">Busca geral</p>
            <Input
              placeholder="Buscar por fornecedor ou origem..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <p className="ds-eyebrow">Status da Análise</p>
            <Select value={currentStatusFilter} onValueChange={handleStatusChange}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione o filtro" />
              </SelectTrigger>
              <SelectContent className="bg-inputapp">
                <SelectItem value="todos">Todos</SelectItem>
                <SelectItem value="pendente" className="text-red-500">Pendente</SelectItem>
                <SelectItem value="em andamento" className="text-blue-500">Em Andamento</SelectItem>
                <SelectItem value="concluida" className="text-green-500">Concluída</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <span className="ds-icon-chip text-primariaapp">
              <History className="h-4 w-4" />
            </span>
            <div>
              <p className="ds-eyebrow">Análises recentes</p>
              <CardTitle className="mt-2">Último processamento</CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {initialAnalises.length > 0 ? (
            initialAnalises.map(({ id, fornecedor, itens, oportunidades, horario, status }) => {
              const isProcessando = status === "processando";
              const card = (
                <div className={`ds-subpanel flex flex-col gap-3 rounded-[24px] px-4 py-4 transition md:flex-row md:items-center md:justify-between ${
                  isProcessando
                    ? "border-blue-500/20 opacity-80"
                    : "hover:border-app-strong hover:shadow-[0_14px_32px_rgba(15,23,42,0.08)]"
                }`}>
                  <div>
                    <div className="flex items-center gap-3">
                      <p className="text-base font-semibold text-texto">{fornecedor || "Fornecedor"}</p>
                      {getStatusBadge(status)}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-3 text-sm text-secondary">
                      {itens && <span>{itens} itens</span>}
                      {oportunidades && <span>{oportunidades} oportunidades</span>}
                      {isProcessando && <span className="text-blue-400">Análise em progresso...</span>}
                    </div>
                  </div>
                  <div className="flex items-center justify-between gap-3 md:min-w-[220px] md:justify-end">
                    <div className="inline-flex items-center gap-2 text-sm text-secondary">
                      <Clock3 className="h-4 w-4" />
                      {horario}
                    </div>
                    {!isProcessando && (
                      <span className="inline-flex items-center gap-1 text-sm font-semibold text-primariaapp">
                        Ver painel
                        <ArrowRight className="h-4 w-4" />
                      </span>
                    )}
                  </div>
                </div>
              );

              return isProcessando ? (
                <div key={id}>{card}</div>
              ) : (
                <Link key={id} href={`/resultado/${id}`} className="block">
                  {card}
                </Link>
              );
            })
          ) : (
            <div className="py-12 text-center">
              <SearchX className="h-12 w-12 text-secondary/30 mx-auto mb-4" />
              <p className="text-base font-semibold text-texto mb-1">
                Nenhuma análise encontrada
              </p>
              <p className="text-sm text-secondary">
                Tente utilizar outros filtros para buscar as análises.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-8 border-t border-borderapp pt-6">
          <p className="text-sm text-secondary">
            Página <span className="font-semibold text-texto">{currentPage}</span> de <span className="font-semibold text-texto">{totalPages}</span>
          </p>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 mr-2">
              <span className="text-sm text-secondary whitespace-nowrap">Ir para:</span>
              <Input
                type="number"
                min={1}
                max={totalPages}
                value={pageInput}
                onChange={(e) => setPageInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    const page = parseInt(pageInput);
                    if (!isNaN(page)) changePage(page);
                  }
                }}
                onBlur={() => {
                  setPageInput(currentPage.toString());
                }}
                className="w-16 h-9"
              />
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => changePage(currentPage - 1)}
              disabled={currentPage === 1}
            >
              <ArrowLeft className="mr-2 h-4 w-4" /> Anterior
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => changePage(currentPage + 1)}
              disabled={currentPage === totalPages}
            >
              Próxima <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </>
  );
}
