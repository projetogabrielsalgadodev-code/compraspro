"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { upsertProduto } from "@/app/(dashboard)/produtos/actions";
import { ProdutoListado } from "./ProdutosListaClient";

const formSchema = z.object({
  ean: z.string().min(1, "EAN é obrigatório"),
  descricao: z.string().min(1, "Descrição é obrigatória"),
  principio_ativo: z.string().optional(),
  fabricante: z.string().optional(),
  estoque: z.coerce.number().min(0, "Estoque não pode ser negativo"),
});

export type ProdutoFormValues = z.infer<typeof formSchema>;

interface ProdutoModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  produtoToEdit: ProdutoListado | null;
}

export function ProdutoModal({
  open,
  onOpenChange,
  produtoToEdit,
}: ProdutoModalProps) {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<ProdutoFormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      ean: "",
      descricao: "",
      principio_ativo: "",
      fabricante: "",
      estoque: 0,
    },
  });

  useEffect(() => {
    if (produtoToEdit && open) {
      // Para o DTO, precisamos garantir que EAN venha do item.
      // Atualmente ProdutoListado não retorna o "EAN" original puro se ele foi escondido no nome, vamos garantir que seja mapeado na listagem.
      form.reset({
        ean: produtoToEdit.ean || "",
        descricao: produtoToEdit.nome || "",
        principio_ativo: produtoToEdit.ativo || "",
        fabricante: produtoToEdit.fabricante || "",
        estoque: produtoToEdit.estoque || 0,
      });
    } else if (open) {
      form.reset({
        ean: "",
        descricao: "",
        principio_ativo: "",
        fabricante: "",
        estoque: 0,
      });
    }
  }, [produtoToEdit, open, form]);

  const onSubmit = async (values: ProdutoFormValues) => {
    setIsSubmitting(true);
    try {
      const response = await upsertProduto({
        ean: values.ean,
        descricao: values.descricao,
        principio_ativo: values.principio_ativo || null,
        fabricante: values.fabricante || null,
        estoque: values.estoque,
      }, produtoToEdit?.id);

      if (response && response.error) {
        throw new Error(response.error);
      }

      toast({
        title: produtoToEdit ? "Produto atualizado" : "Produto cadastrado",
        description: "Operação realizada com sucesso no banco de dados.",
      });

      onOpenChange(false);
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: "Erro ao salvar",
        description: error.message || "Ocorreu um erro ao salvar o produto.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>
            {produtoToEdit ? "Editar Produto" : "Adicionar Produto"}
          </DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4 pt-4">
            <FormField
              control={form.control}
              name="ean"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>EAN / Código de Barras</FormLabel>
                  <FormControl>
                    <Input placeholder="Ex: 7891010101010" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="descricao"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Descrição do Produto</FormLabel>
                  <FormControl>
                    <Input placeholder="Ex: Dipirona 500mg" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="principio_ativo"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Princípio Ativo</FormLabel>
                  <FormControl>
                    <Input placeholder="Ex: Dipirona Monoidratada" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="fabricante"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Fabricante</FormLabel>
                  <FormControl>
                    <Input placeholder="Ex: Medley" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="estoque"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Estoque Disponível</FormLabel>
                  <FormControl>
                    <Input type="number" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end pt-4">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {produtoToEdit ? "Salvar Alterações" : "Cadastrar"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
