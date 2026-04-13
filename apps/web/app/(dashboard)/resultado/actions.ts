"use server";

import { createClient } from "@/lib/supabase/server";
import { revalidatePath } from "next/cache";

export async function updateAnaliseStatus(analiseId: string, status: string) {
  try {
    const supabase = await createClient();
    
    const { error } = await supabase
      .from("analises_oferta")
      .update({ status })
      .eq("id", analiseId);

    if (error) {
      console.error("Erro ao atualizar status:", error);
      return { success: false, error: error.message };
    }

    revalidatePath(`/resultado/${analiseId}`);
    return { success: true };
  } catch (error) {
    console.error("Erro no updateAnaliseStatus:", error);
    return { success: false, error: "Erro interno no servidor." };
  }
}
