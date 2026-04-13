"use server";

import { createClient } from "@/lib/supabase/server";
import { revalidatePath } from "next/cache";

export interface ProdutoPayload {
  ean: string;
  descricao: string;
  principio_ativo: string | null;
  fabricante: string | null;
  estoque: number;
}

export async function upsertProduto(payload: ProdutoPayload, id?: string) {
  const supabase = await createClient();

  try {
    const dataToSave = {
      ean: payload.ean,
      descricao: payload.descricao,
      principio_ativo: payload.principio_ativo,
      fabricante: payload.fabricante,
      estoque: payload.estoque,
      ...( !id ? { empresa_id: process.env.NEXT_PUBLIC_EMPRESA_ID_PADRAO } : {} )
    };

    if (id) {
      // Update
      const { error } = await supabase
        .from("produtos")
        .update(dataToSave)
        .eq("id", id);
      
      if (error) {
        throw new Error(error.message);
      }
    } else {
      // Insert
      const { error } = await supabase
        .from("produtos")
        .insert([dataToSave]);
      
      if (error) {
        throw new Error(error.message);
      }
    }

    revalidatePath("/produtos");
    return { success: true };
  } catch (error: any) {
    return { success: false, error: error.message || "Erro ao salvar o produto." };
  }
}
