"use client";

import { useEffect, useState } from "react";
import { Clock } from "lucide-react";

export function SyncIndicator() {
  const [ultimaSincronizacao, setUltimaSincronizacao] = useState<string>("Carregando...");

  useEffect(() => {
    const hasDb = sessionStorage.getItem("banco_dados_ativo");
    if (hasDb) {
      setUltimaSincronizacao("Hoje, 09:12");
    } else {
      setUltimaSincronizacao("Mock (Hoje, 08:30)");
    }
  }, []);

  return (
    <div className="flex items-center gap-2 rounded-full border border-app-strong bg-app px-3 py-1.5 text-sm text-secondary">
      <Clock className="h-4 w-4" />
      <span>
        Base sincronizada: <strong className="text-texto">{ultimaSincronizacao}</strong>
      </span>
    </div>
  );
}
