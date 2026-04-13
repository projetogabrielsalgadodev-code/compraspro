import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatarMoeda(valor?: number | null) {
  if (valor == null || Number.isNaN(valor)) return "--";
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL"
  }).format(valor);
}

export function formatarPercentual(valor?: number | null) {
  if (valor == null || Number.isNaN(valor)) return "--";
  const sinal = valor > 0 ? "+" : "";
  return `${sinal}${valor.toFixed(1)}%`;
}
