"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { Boxes, PackageSearch, Plus, ArrowLeft, ArrowRight, Pencil, Upload } from "lucide-react";
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
import { ProdutoModal } from "./ProdutoModal";
import { CsvImportModal } from "./CsvImportModal";

export interface ProdutoListado {
  id: string;
  ean: string;
  nome: string;
  ativo: string;
  fabricante: string;
  estoque: number;
}

interface ProdutosListaClientProps {
  initialProdutos: ProdutoListado[];
  totalPages: number;
  currentPage: number;
}

export function ProdutosListaClient({
  initialProdutos,
  totalPages,
  currentPage,
}: ProdutosListaClientProps) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const [busca, setBusca] = useState(searchParams.get("query") || "");
  const [modalOpen, setModalOpen] = useState(false);
  const [csvModalOpen, setCsvModalOpen] = useState(false);
  const [produtoEditando, setProdutoEditando] = useState<ProdutoListado | null>(null);
  const [pageInput, setPageInput] = useState(currentPage.toString());

  useEffect(() => {
    setPageInput(currentPage.toString());
  }, [currentPage]);

  // Debounce effect for search
  useEffect(() => {
    const timeOutId = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      const currentQuery = searchParams.get("query") || "";

      // Se a string buscada localmente é igual à que está na url, não faz nada 
      // (evita loop ao clicar em próxima página que mudava o searchParams)
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

  const handleEstoqueChange = (value: string) => {
    const params = new URLSearchParams(searchParams.toString());
    if (value && value !== "todos") {
      params.set("estoque", value);
    } else {
      params.delete("estoque");
    }
    params.set("page", "1");
    router.replace(`${pathname}?${params.toString()}`);
  };

  const currentEstoqueFilter = searchParams.get("estoque") || "todos";

  const changePage = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages) return;
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", newPage.toString());
    router.push(`${pathname}?${params.toString()}`);
  };

  const handleAddProduto = () => {
    setProdutoEditando(null);
    setModalOpen(true);
  };

  const handleEditProduto = (produto: ProdutoListado) => {
    setProdutoEditando(produto);
    setModalOpen(true);
  };

  return (
    <>
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-texto">Catálogo de Produtos</h2>
          <p className="text-sm text-secondary">
            Busque produtos, veja estoques e edite informações cadastradas.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setCsvModalOpen(true)} className="gap-2">
            <Upload className="h-4 w-4" />
            Importar CSV
          </Button>
          <Button onClick={handleAddProduto}>
            <Plus className="mr-2 h-4 w-4" />
            Adicionar Produto
          </Button>
        </div>
      </div>

      <Card className="mb-6">
        <CardContent className="grid gap-4 p-5 md:grid-cols-[1fr_200px]">
          <div className="space-y-2">
            <p className="ds-eyebrow">Pesquisar produto</p>
            <Input
              placeholder="EAN, Produto, Ativo ou Fabricante..."
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <p className="ds-eyebrow">Status do Estoque</p>
            <Select value={currentEstoqueFilter} onValueChange={handleEstoqueChange}>
              <SelectTrigger>
                <SelectValue placeholder="Selecione o filtro" />
              </SelectTrigger>
              <SelectContent className="bg-inputapp">
                <SelectItem value="todos">Todos</SelectItem>
                <SelectItem value="com_estoque">Em Estoque</SelectItem>
                <SelectItem value="sem_estoque">Sem Estoque (Zeradinho)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {initialProdutos.length > 0 ? (
          initialProdutos.map((produto) => (
            <Card key={produto.id} className="group relative">
              <CardHeader className="pb-3 border-b border-borderapp">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="ds-icon-chip text-primariaapp">
                      <Boxes className="h-4 w-4" />
                    </span>
                    <CardTitle className="leading-tight break-words">
                      {produto.nome}
                      <span className="block text-xs font-normal text-secondary mt-1">EAN: {produto.ean}</span>
                    </CardTitle>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={() => handleEditProduto(produto)}
                    title="Editar produto"
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-4 grid grid-cols-2 gap-y-4 gap-x-2 text-sm text-secondary">
                <div>
                  <p className="ds-eyebrow">Princípio ativo</p>
                  <p className="font-medium text-texto line-clamp-1" title={produto.ativo}>{produto.ativo}</p>
                </div>
                <div>
                  <p className="ds-eyebrow">Fabricante</p>
                  <p className="font-medium text-texto line-clamp-1" title={produto.fabricante}>{produto.fabricante}</p>
                </div>
                <div className="col-span-2">
                  <p className="ds-eyebrow">Estoque Disponível</p>
                  <p className="text-lg font-bold text-primariaapp">
                    {produto.estoque} <span className="text-sm font-normal text-secondary">unidades</span>
                  </p>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <div className="col-span-1 md:col-span-2 py-12 text-center">
            <PackageSearch className="h-12 w-12 text-secondary/30 mx-auto mb-4" />
            <p className="text-base font-semibold text-texto mb-1">
              Nenhum produto encontrado
            </p>
            <p className="text-sm text-secondary">
              Tente utilizar outros filtros ou criar um novo registro clicando em Adicionar Produto.
            </p>
          </div>
        )}
      </div>

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

      <ProdutoModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        produtoToEdit={produtoEditando}
      />

      <CsvImportModal
        open={csvModalOpen}
        onOpenChange={setCsvModalOpen}
        onImportComplete={() => {
          router.refresh();
        }}
      />
    </>
  );
}
