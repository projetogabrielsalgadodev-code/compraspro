"use client"

import { useState, useTransition } from "react"
import { useRouter } from "next/navigation"
import { upsertEmpresa, deleteEmpresa, toggleEmpresaAtivo } from "../actions"
import { useToast } from "@/hooks/use-toast"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { 
  Building2, Plus, Edit, Trash2, Loader2, Users, Phone, Mail, 
  MapPin, Search, ToggleLeft, ToggleRight, ChevronRight
} from "lucide-react"
import { cn } from "@/lib/utils"

type Empresa = {
  id: string
  nome: string
  cnpj: string
  razao_social?: string
  telefone?: string
  email?: string
  endereco?: string
  ativo?: boolean
  created_at: string
  qtdeUsuarios: number
}

export function EmpresaManager({ initialData }: { initialData: Empresa[] }) {
  const [isOpen, setIsOpen] = useState(false)
  const [editingData, setEditingData] = useState<Empresa | null>(null)
  const [isPending, startTransition] = useTransition()
  const [searchTerm, setSearchTerm] = useState("")
  const { toast } = useToast()
  const router = useRouter()

  const handleOpenNew = () => {
    setEditingData(null)
    setIsOpen(true)
  }

  const handleOpenEdit = (empresa: Empresa, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingData(empresa)
    setIsOpen(true)
  }

  const handleSave = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    startTransition(async () => {
      const result = await upsertEmpresa(formData)
      if (result.error) {
        toast({
          variant: "destructive",
          title: "Erro ao salvar",
          description: result.error,
        })
      } else {
        toast({
          title: "Sucesso!",
          description: result.success,
        })
        setIsOpen(false)
      }
    })
  }

  const handleDelete = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (confirm("Certeza absoluta que deseja remover esta empresa? Todos os vínculos serão perdidos!")) {
      startTransition(async () => {
        const result = await deleteEmpresa(id)
        if (result.error) {
          toast({ variant: "destructive", title: "Erro", description: result.error })
        } else {
          toast({ title: "Removida", description: result.success })
        }
      })
    }
  }

  const handleToggleAtivo = (id: string, currentAtivo: boolean, e: React.MouseEvent) => {
    e.stopPropagation()
    startTransition(async () => {
      const result = await toggleEmpresaAtivo(id, !currentAtivo)
      if (result.error) {
        toast({ variant: "destructive", title: "Erro", description: result.error })
      } else {
        toast({ title: "Status alterado", description: result.success })
      }
    })
  }

  const handleCardClick = (empresaId: string) => {
    router.push(`/admin/usuarios?empresa_id=${empresaId}`)
  }

  const filtered = initialData.filter(e =>
    e.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.cnpj.includes(searchTerm) ||
    (e.razao_social || "").toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary" />
          <Input
            placeholder="Buscar por nome, CNPJ ou razão social..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="pl-10 bg-input-app"
          />
        </div>
        <Button onClick={handleOpenNew} className="bg-[linear-gradient(135deg,rgb(var(--accent-primary)),rgb(var(--accent-secondary)))] text-white font-semibold shadow-[0_8px_24px_rgba(36,76,255,0.28)] hover:shadow-[0_12px_32px_rgba(36,76,255,0.36)] transition-all hover:-translate-y-0.5">
          <Plus className="mr-2 h-4 w-4" /> Nova Empresa
        </Button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <div className="surface-card rounded-2xl px-4 py-3 soft-stroke">
          <p className="ds-eyebrow">Total</p>
          <p className="mt-1 text-2xl font-bold text-texto">{initialData.length}</p>
        </div>
        <div className="surface-card rounded-2xl px-4 py-3 soft-stroke">
          <p className="ds-eyebrow">Ativas</p>
          <p className="mt-1 text-2xl font-bold text-texto">{initialData.filter(e => e.ativo !== false).length}</p>
        </div>
        <div className="surface-card rounded-2xl px-4 py-3 soft-stroke hidden sm:block">
          <p className="ds-eyebrow">Membros</p>
          <p className="mt-1 text-2xl font-bold text-texto">{initialData.reduce((acc, e) => acc + e.qtdeUsuarios, 0)}</p>
        </div>
      </div>

      {/* Card grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((empresa) => (
          <div
            key={empresa.id}
            onClick={() => handleCardClick(empresa.id)}
            className={cn(
              "surface-card rounded-[20px] p-5 soft-stroke cursor-pointer group transition-all duration-300 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-1",
              empresa.ativo === false && "opacity-60"
            )}
          >
            {/* Card header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="ds-icon-chip h-11 w-11 shrink-0 bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 0.22),rgb(var(--accent-secondary) / 0.14))]">
                  <Building2 className="h-5 w-5 text-primariaapp" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-texto truncate">{empresa.nome}</h3>
                  <p className="text-xs text-secondary font-mono">{empresa.cnpj}</p>
                </div>
              </div>
              <Badge
                variant="default"
                className={cn(
                  "text-xs font-medium shadow-none border-0",
                  empresa.ativo !== false
                    ? "bg-[rgb(var(--accent-primary) / 0.12)] text-primariaapp"
                    : "bg-[var(--surface-highlight)] text-secondary"
                )}
              >
                {empresa.ativo !== false ? "Ativa" : "Inativa"}
              </Badge>
            </div>

            {/* Details */}
            <div className="space-y-1.5 mb-4 text-sm">
              {empresa.razao_social && (
                <p className="text-secondary truncate">{empresa.razao_social}</p>
              )}
              {empresa.email && (
                <div className="flex items-center gap-2 text-secondary">
                  <Mail className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{empresa.email}</span>
                </div>
              )}
              {empresa.telefone && (
                <div className="flex items-center gap-2 text-secondary">
                  <Phone className="h-3.5 w-3.5 shrink-0" />
                  <span>{empresa.telefone}</span>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-3 border-t border-app">
              <div className="flex items-center gap-1.5">
                <Users className="h-3.5 w-3.5 text-primariaapp" />
                <span className="text-xs font-medium text-primariaapp">
                  {empresa.qtdeUsuarios} {empresa.qtdeUsuarios === 1 ? "membro" : "membros"}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-secondary hover:text-texto"
                  onClick={(e) => handleOpenEdit(empresa, e)}
                >
                  <Edit className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-secondary hover:text-primariaapp"
                  onClick={(e) => handleToggleAtivo(empresa.id, empresa.ativo !== false, e)}
                >
                  {empresa.ativo !== false ? <ToggleRight className="h-3.5 w-3.5" /> : <ToggleLeft className="h-3.5 w-3.5" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-secondary hover:text-descartavel"
                  onClick={(e) => handleDelete(empresa.id, e)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
                <ChevronRight className="h-4 w-4 text-secondary opacity-0 group-hover:opacity-100 transition-opacity ml-1" />
              </div>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="sm:col-span-2 lg:col-span-3 surface-card rounded-[20px] p-12 soft-stroke text-center">
            <Building2 className="h-10 w-10 text-secondary mx-auto mb-3 opacity-40" />
            <p className="text-secondary">
              {searchTerm ? "Nenhuma empresa encontrada para essa busca." : "Nenhuma empresa cadastrada ainda."}
            </p>
          </div>
        )}
      </div>

      {/* Modal de criação/edição */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[520px] ds-panel border-app-strong">
          <form onSubmit={handleSave}>
            <DialogHeader>
              <DialogTitle className="text-texto">
                {editingData ? "Editar Empresa" : "Cadastrar Nova Empresa"}
              </DialogTitle>
              <DialogDescription className="text-secondary">
                Preencha os dados da filial ou farmácia principal.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-5">
              {editingData && <input type="hidden" name="id" value={editingData.id} />}
              
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="nome">Nome Fantasia *</Label>
                  <Input
                    id="nome"
                    name="nome"
                    defaultValue={editingData?.nome || ""}
                    placeholder="Farmácia Esperança"
                    required
                    className="bg-input-app"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cnpj">CNPJ *</Label>
                  <Input
                    id="cnpj"
                    name="cnpj"
                    defaultValue={editingData?.cnpj || ""}
                    placeholder="00.000.000/0000-00"
                    required
                    className="bg-input-app"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="razao_social">Razão Social</Label>
                <Input
                  id="razao_social"
                  name="razao_social"
                  defaultValue={editingData?.razao_social || ""}
                  placeholder="Drogaria Nova Esperança LTDA"
                  className="bg-input-app"
                />
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="email">E-mail Corporativo</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    defaultValue={editingData?.email || ""}
                    placeholder="contato@farmacia.com"
                    className="bg-input-app"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="telefone">Telefone</Label>
                  <Input
                    id="telefone"
                    name="telefone"
                    defaultValue={editingData?.telefone || ""}
                    placeholder="(11) 99999-9999"
                    className="bg-input-app"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="endereco">Endereço</Label>
                <Input
                  id="endereco"
                  name="endereco"
                  defaultValue={editingData?.endereco || ""}
                  placeholder="Rua das Flores, 123 - Centro, São Paulo - SP"
                  className="bg-input-app"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setIsOpen(false)}
                className="text-secondary"
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                disabled={isPending}
                className="bg-[linear-gradient(135deg,rgb(var(--accent-primary)),rgb(var(--accent-secondary)))] text-white font-semibold"
              >
                {isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                {isPending ? "Salvando..." : "Salvar Dados"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
