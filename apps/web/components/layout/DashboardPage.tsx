import { Header } from "@/components/layout/Header";

interface DashboardPageProps {
  titulo: string;
  subtitulo?: string;
  eyebrow?: string;
  children: React.ReactNode;
  containerClassName?: string;
}

export function DashboardPage({ titulo, subtitulo, eyebrow, children, containerClassName = "" }: DashboardPageProps) {
  return (
    <div className="pb-12">
      <Header titulo={titulo} subtitulo={subtitulo} eyebrow={eyebrow} />
      <div className={`w-full space-y-6 px-4 py-6 sm:px-6 ${containerClassName}`}>{children}</div>
    </div>
  );
}
