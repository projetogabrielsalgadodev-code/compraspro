import type { ReactNode } from "react";

export function MetricCard({ eyebrow, value, description, icon }: { eyebrow: string; value: string; description?: string; icon?: ReactNode }) {
  return (
    <div className="ds-panel p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="ds-eyebrow">{eyebrow}</p>
        {icon ? <span className="ds-icon-chip text-primariaapp">{icon}</span> : null}
      </div>
      <p className="mt-4 text-4xl font-semibold tracking-tight text-texto">{value}</p>
      {description ? <p className="mt-2 text-sm text-secondary">{description}</p> : null}
    </div>
  );
}
