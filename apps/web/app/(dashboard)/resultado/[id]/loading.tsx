import { DashboardPage } from "@/components/layout/DashboardPage";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <DashboardPage
      titulo="Processando análise..."
      subtitulo="A IA está cruzando dados de histórico, demanda e estoque."
      eyebrow="Resultado executivo"
    >
      <div className="grid gap-6">
        {/* Skeleton for summary cards */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-4 w-1/2 mb-4 bg-app-strong" />
                <Skeleton className="h-8 w-3/4 mb-2 bg-app-strong" />
                <Skeleton className="h-3 w-full bg-app-strong" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Skeleton for the main table */}
        <Card>
          <CardHeader>
            <Skeleton className="h-5 w-1/4 mb-2 bg-app-strong" />
            <Skeleton className="h-8 w-1/2 bg-app-strong" />
          </CardHeader>
          <CardContent>
            <div className="ds-subpanel overflow-x-auto rounded-[24px] p-4">
              <div className="space-y-4">
                <Skeleton className="h-6 w-full bg-app-strong/50" />
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-10 w-full bg-app-strong" />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardPage>
  );
}
