import { Card } from "@/components/ui/card";
import type { EquivalenteResumo } from "@/types";

/* C-31: Substituídas cores hardcoded (slate-500/600) por tokens do design system */
export function EquivalentsList({ items }: { items?: EquivalenteResumo[] }) {
  if (!items?.length) {
    return <p className="text-sm text-secondary">Nenhum equivalente relevante encontrado.</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((equivalente) => (
        <Card key={`${equivalente.descricao}-${equivalente.fabricante ?? "sem-fabricante"}`} className="p-4">
          <p className="font-medium text-texto">{equivalente.descricao}</p>
          <div className="mt-2 flex items-center justify-between text-sm text-secondary">
            <span>{equivalente.fabricante ?? "Fabricante não informado"}</span>
            <span>Estoque: {equivalente.estoque ?? 0}</span>
          </div>
        </Card>
      ))}
    </div>
  );
}
