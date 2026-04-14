"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState, useTransition } from "react";
import { ChevronDown, Loader2, Save, Settings2 } from "lucide-react";
import { createBrowserClient } from "@supabase/ssr";
import { buscarConfiguracaoEmpresa, salvarConfiguracaoEmpresa, type ConfiguracaoEmpresa } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const EMPRESA_ID_PADRAO = process.env.NEXT_PUBLIC_EMPRESA_ID_PADRAO ?? "";

const configuracaoLocal: ConfiguracaoEmpresa = {
  empresa_id: "local",
  estoque_minimo_dias: 30,
  estoque_alto_dias: 90,
  vantagem_minima_percentual: 5,
  metodo_comparacao: "average",
  considerar_equivalentes: true,
  horizonte_sugestao_meses: 3,
  usar_demanda_mes_sugcompra: true,
  exibir_extremos_historicos: true
};

export function ConfiguracoesEmpresaForm() {
  const [configuracao, setConfiguracao] = useState<ConfiguracaoEmpresa>(configuracaoLocal);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [empresaNome, setEmpresaNome] = useState<string | null>(null);

  useEffect(() => {
    if (!EMPRESA_ID_PADRAO) {
      setMensagem("Defina `NEXT_PUBLIC_EMPRESA_ID_PADRAO` para carregar e salvar as configurações reais da empresa.");
      return;
    }

    // Buscar nome da empresa
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
    );
    supabase
      .from("empresas")
      .select("nome")
      .eq("id", EMPRESA_ID_PADRAO)
      .single()
      .then(({ data }) => {
        if (data?.nome) setEmpresaNome(data.nome);
      });

    startTransition(async () => {
      try {
        const data = await buscarConfiguracaoEmpresa(EMPRESA_ID_PADRAO);
        setConfiguracao(data);
        setMensagem("Configurações carregadas do Supabase.");
      } catch (loadError) {
        setErro(loadError instanceof Error ? loadError.message : "Falha ao carregar configurações.");
      }
    });
  }, []);

  const modoLeitura = useMemo(() => !EMPRESA_ID_PADRAO, []);

  function updateNumber<K extends keyof ConfiguracaoEmpresa>(key: K, value: string) {
    setConfiguracao((current) => ({ ...current, [key]: Number(value) }));
  }

  function updateBoolean<K extends keyof ConfiguracaoEmpresa>(key: K, value: boolean) {
    setConfiguracao((current) => ({ ...current, [key]: value }));
  }

  function salvar() {
    if (modoLeitura) {
      return;
    }

    setMensagem(null);
    setErro(null);
    startTransition(async () => {
      try {
        const salvo = await salvarConfiguracaoEmpresa({ ...configuracao, empresa_id: EMPRESA_ID_PADRAO });
        setConfiguracao(salvo);
        setMensagem("Configurações salvas com sucesso.");
      } catch (saveError) {
        setErro(saveError instanceof Error ? saveError.message : "Falha ao salvar configurações.");
      }
    });
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <span className="ds-icon-chip text-primariaapp"><Settings2 className="h-4 w-4" /></span>
            <div>
              <p className="ds-eyebrow">Regras de compra</p>
              <CardTitle className="mt-2">Parâmetros operacionais da empresa</CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="ds-subpanel rounded-[24px] px-4 py-4 text-sm text-secondary">
            {modoLeitura ? (
              <p>Modo local ativo. As alterações ficam apenas na interface até você informar uma empresa padrão.</p>
            ) : (
              <p>Empresa conectada: <span className="font-semibold text-texto">{empresaNome || EMPRESA_ID_PADRAO}</span></p>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Field label="Estoque mínimo em dias">
              <Input type="number" min={1} value={configuracao.estoque_minimo_dias} onChange={(event) => updateNumber("estoque_minimo_dias", event.target.value)} />
            </Field>
            <Field label="Estoque alto a partir de X dias">
              <Input type="number" min={1} value={configuracao.estoque_alto_dias} onChange={(event) => updateNumber("estoque_alto_dias", event.target.value)} />
            </Field>
            <Field label="Vantagem mínima (%)">
              <Input type="number" min={0} step="0.1" value={configuracao.vantagem_minima_percentual} onChange={(event) => updateNumber("vantagem_minima_percentual", event.target.value)} />
            </Field>
            <Field label="Horizonte da sugestão (meses)">
              <Input type="number" min={1} value={configuracao.horizonte_sugestao_meses} onChange={(event) => updateNumber("horizonte_sugestao_meses", event.target.value)} />
            </Field>
          </div>

          {/* C-24: Select estilizado com aparência consistente com o design system */}
          <Field label="Método de comparação histórica">
            <div className="relative">
              <select
                className="flex h-12 w-full appearance-none rounded-2xl border border-app bg-input-app px-4 py-2 pr-10 text-sm text-texto transition-colors hover:border-app-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo"
                value={configuracao.metodo_comparacao}
                onChange={(event) => setConfiguracao((current) => ({ ...current, metodo_comparacao: event.target.value as ConfiguracaoEmpresa["metodo_comparacao"] }))}
              >
                <option value="average">Média histórica</option>
                <option value="median">Mediana</option>
                <option value="lowest">Menor preço histórico</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-secondary" />
            </div>
          </Field>

          {/* C-14: Toggle switches customizados em vez de checkbox nativo */}
          <div className="grid gap-3 md:grid-cols-3">
            <ToggleCard
              label="Considerar equivalentes"
              description="Inclui itens equivalentes na classificação e no alerta de estoque."
              checked={configuracao.considerar_equivalentes}
              onCheckedChange={(value) => updateBoolean("considerar_equivalentes", value)}
            />
            <ToggleCard
              label="Usar demanda do Sugcompra"
              description="Mantém a demanda mensal importada como referência principal."
              checked={configuracao.usar_demanda_mes_sugcompra}
              onCheckedChange={(value) => updateBoolean("usar_demanda_mes_sugcompra", value)}
            />
            <ToggleCard
              label="Exibir extremos históricos"
              description="Mostra 2 menores e 2 maiores entradas quando a oferta é competitiva."
              checked={configuracao.exibir_extremos_historicos}
              onCheckedChange={(value) => updateBoolean("exibir_extremos_historicos", value)}
            />
          </div>

          {erro ? <p className="text-sm text-descartavel">{erro}</p> : null}
          {mensagem ? <p className="text-sm text-secondary">{mensagem}</p> : null}

          <div className="flex justify-end">
            <Button onClick={salvar} disabled={modoLeitura || isPending} className="gap-2 px-6">
              {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Salvar configurações
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-medium text-texto">{label}</span>
      {children}
    </label>
  );
}

/* C-14: Toggle switch customizado com visual do design system */
function ToggleCard({
  label,
  description,
  checked,
  onCheckedChange
}: {
  label: string;
  description: string;
  checked: boolean;
  onCheckedChange: (value: boolean) => void;
}) {
  return (
    <label className="ds-subpanel flex cursor-pointer items-start justify-between gap-4 rounded-[24px] px-4 py-4 transition hover:border-app-strong">
      <div>
        <p className="text-sm font-semibold text-texto">{label}</p>
        <p className="mt-1 text-xs text-secondary">{description}</p>
      </div>
      {/* Switch customizado: action-primary quando ativo, surface-section quando inativo */}
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onCheckedChange(!checked)}
        className={`relative mt-0.5 inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo ${
          checked ? "bg-[rgb(var(--accent-primary))]" : "bg-[rgb(var(--bg-input) / 1)] border border-app"
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform ${
            checked ? "translate-x-[22px]" : "translate-x-1"
          }`}
        />
      </button>
    </label>
  );
}
