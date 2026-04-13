import { AlertTriangle, Award, BadgeDollarSign, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { ClassificacaoOferta } from "@/types";

/* C-30: Emojis alinhados com design system.md */
const config: Record<ClassificacaoOferta, { label: string; emoji: string; icon: JSX.Element; variant: "success" | "warning" | "danger" }> = {
  ouro: { label: "Ouro", emoji: "🥇", icon: <Award className="mr-1 h-3 w-3" />, variant: "success" },
  prata: { label: "Prata", emoji: "🥈", icon: <BadgeDollarSign className="mr-1 h-3 w-3" />, variant: "warning" },
  atencao: { label: "Atenção", emoji: "⚠️", icon: <AlertTriangle className="mr-1 h-3 w-3" />, variant: "warning" },
  descartavel: { label: "Descartável", emoji: "❌", icon: <XCircle className="mr-1 h-3 w-3" />, variant: "danger" }
};

export function OfferBadge({ classification }: { classification: ClassificacaoOferta }) {
  const item = config[classification];
  return (
    <Badge variant={item.variant}>
      <span className="mr-1">{item.emoji}</span>
      {item.label}
    </Badge>
  );
}
