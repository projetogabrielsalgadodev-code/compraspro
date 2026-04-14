"use client"

import { useState, useTransition } from "react"
import { Building2, Loader2, Save } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { updateEmpresa } from "@/app/(dashboard)/configuracoes/actions"
import { formatCNPJ, formatTelefone } from "@/lib/formatters"

interface EmpresaData {
  id: string
  nome: string
  cnpj: string | null
  razao_social: string | null
  telefone: string | null
  email: string | null
  endereco: string | null
}

export function EmpresaForm({ empresa }: { empresa: EmpresaData }) {
  const [form, setForm] = useState<EmpresaData>(empresa)
  const [mensagem, setMensagem] = useState<string | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()

  function update<K extends keyof EmpresaData>(key: K, value: string) {
    setForm((cur) => ({ ...cur, [key]: value }))
  }

  function salvar() {
    setMensagem(null)
    setErro(null)
    startTransition(async () => {
      const fd = new FormData()
      fd.set("empresa_id", form.id)
      fd.set("nome", form.nome || "")
      fd.set("razao_social", form.razao_social || "")
      fd.set("cnpj", form.cnpj || "")
      fd.set("telefone", form.telefone || "")
      fd.set("email", form.email || "")
      fd.set("endereco", form.endereco || "")

      const result = await updateEmpresa(fd)
      if (result.error) setErro(result.error)
      else setMensagem(result.success!)
    })
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <span className="ds-icon-chip text-primariaapp"><Building2 className="h-4 w-4" /></span>
          <div>
            <p className="ds-eyebrow">Cadastro</p>
            <CardTitle className="mt-2">Dados da empresa</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Nome fantasia *">
            <Input value={form.nome || ""} onChange={(e) => update("nome", e.target.value)} placeholder="Nome da empresa" />
          </Field>
          <Field label="Razão social">
            <Input value={form.razao_social || ""} onChange={(e) => update("razao_social", e.target.value)} placeholder="Razão social" />
          </Field>
          <Field label="CNPJ">
            <Input value={form.cnpj || ""} onChange={(e) => update("cnpj", formatCNPJ(e.target.value))} placeholder="00.000.000/0001-00" />
          </Field>
          <Field label="Telefone">
            <Input value={form.telefone || ""} onChange={(e) => update("telefone", formatTelefone(e.target.value))} placeholder="(00) 00000-0000" />
          </Field>
          <Field label="E-mail">
            <Input type="email" value={form.email || ""} onChange={(e) => update("email", e.target.value)} placeholder="contato@empresa.com" />
          </Field>
          <Field label="Endereço">
            <Input value={form.endereco || ""} onChange={(e) => update("endereco", e.target.value)} placeholder="Rua, número, cidade - UF" />
          </Field>
        </div>

        {erro ? <p className="text-sm text-descartavel">{erro}</p> : null}
        {mensagem ? <p className="text-sm text-[rgb(var(--accent-primary))]">{mensagem}</p> : null}

        <div className="flex justify-end">
          <Button onClick={salvar} disabled={isPending} className="gap-2 px-6">
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Salvar dados da empresa
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-medium text-texto">{label}</span>
      {children}
    </label>
  )
}
