"use client"

import { useState, useTransition } from "react"
import { inviteUser, updateRole, deleteUser, updateUser } from "../actions"
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { 
  Plus, Shield, Loader2, Trash2, UserCog, Search, 
  Mail, ShieldAlert, Building2, UserPlus, Edit
} from "lucide-react"
import { cn } from "@/lib/utils"
import type { UserUsageStats } from "../actions"

type UserProfile = {
  id: string
  nome: string
  email: string
  papel: string
  empresa_id?: string
  created_at: string
  empresas?: { id: string; nome: string }[] | { id: string; nome: string } | null
}

type EmpresaOption = {
  id: string
  nome: string
}

interface UserManagerProps {
  initialUsers: UserProfile[]
  empresas: EmpresaOption[]
  empresaIdFilter?: string
  usageStats?: UserUsageStats[]
}

export function UserManager({ initialUsers, empresas, empresaIdFilter, usageStats = [] }: UserManagerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [editingData, setEditingData] = useState<UserProfile | null>(null)
  const [isPending, startTransition] = useTransition()
  const [searchTerm, setSearchTerm] = useState("")
  const { toast } = useToast()

  const handleOpenNew = () => {
    setEditingData(null)
    setIsOpen(true)
  }

  const handleOpenEdit = (user: UserProfile, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingData(user)
    setIsOpen(true)
  }

  const handleSave = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    startTransition(async () => {
      const result = editingData
        ? await updateUser(formData)
        : await inviteUser(formData)

      if (result.error) {
        toast({
          variant: "destructive",
          title: "Erro",
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

  const handleRoleChange = (userId: string, newRole: string) => {
    startTransition(async () => {
      const result = await updateRole(userId, newRole)
      if (result.error) {
        toast({ variant: "destructive", title: "Erro", description: result.error })
      } else {
        toast({ title: "Perfil atualizado", description: result.success })
      }
    })
  }

  const handleDelete = (userId: string) => {
    if (confirm("Certeza absoluta que deseja revogar o acesso deste usuário permanentemente?")) {
      startTransition(async () => {
        const result = await deleteUser(userId)
        if (result.error) {
          toast({ variant: "destructive", title: "Erro", description: result.error })
        } else {
          toast({ title: "Removido", description: result.success })
        }
      })
    }
  }

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map(w => w[0])
      .slice(0, 2)
      .join("")
      .toUpperCase()
  }

  const filtered = initialUsers.filter(u =>
    u.nome.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-secondary" />
          <Input
            placeholder="Buscar por nome ou e-mail..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="pl-10 bg-input-app"
          />
        </div>
        <Button
          onClick={handleOpenNew}
          className="bg-[linear-gradient(135deg,rgb(var(--accent-primary)),rgb(var(--accent-secondary)))] text-white font-semibold shadow-[0_8px_24px_rgba(36,76,255,0.28)] hover:shadow-[0_12px_32px_rgba(36,76,255,0.36)] transition-all hover:-translate-y-0.5"
        >
          <UserPlus className="mr-2 h-4 w-4" /> Cadastrar Usuário
        </Button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="surface-card rounded-2xl px-4 py-3 soft-stroke">
          <p className="ds-eyebrow">Total</p>
          <p className="mt-1 text-2xl font-bold text-texto">{initialUsers.length}</p>
        </div>
        <div className="surface-card rounded-2xl px-4 py-3 soft-stroke">
          <p className="ds-eyebrow">Admins</p>
          <p className="mt-1 text-2xl font-bold text-texto">{initialUsers.filter(u => u.papel === 'admin').length}</p>
        </div>
        <div className="surface-card rounded-2xl px-4 py-3 soft-stroke">
          <p className="ds-eyebrow">Funcionários</p>
          <p className="mt-1 text-2xl font-bold text-texto">{initialUsers.filter(u => u.papel !== 'admin').length}</p>
        </div>
        <div className="surface-card rounded-2xl px-4 py-3 soft-stroke">
          <p className="ds-eyebrow">Total Análises</p>
          <p className="mt-1 text-2xl font-bold text-primariaapp">{usageStats.reduce((acc, s) => acc + s.total_analises, 0)}</p>
        </div>
        <div className="surface-card rounded-2xl px-4 py-3 soft-stroke">
          <p className="ds-eyebrow">Custo Total</p>
          <p className="mt-1 text-2xl font-bold text-primariaapp">
            {usageStats.reduce((acc, s) => acc + s.total_custo, 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </p>
        </div>
      </div>

      {/* User cards */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((user) => (
          <div
            key={user.id}
            className="surface-card rounded-[20px] p-5 soft-stroke transition-all duration-300 hover:shadow-[var(--shadow-card-hover)] hover:-translate-y-0.5"
          >
            <div className="flex items-start gap-3 mb-4">
              {/* Avatar */}
              <div className={cn(
                "flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl text-sm font-bold",
                user.papel === 'admin'
                  ? "bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 0.22),rgb(var(--accent-tertiary) / 0.16))] text-primariaapp"
                  : "bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.92))] text-secondary"
              )}>
                {getInitials(user.nome)}
              </div>
              <div className="min-w-0 flex-1">
                <h3 className="font-semibold text-texto truncate">{user.nome}</h3>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <Mail className="h-3 w-3 text-secondary shrink-0" />
                  <span className="text-xs text-secondary truncate">{user.email}</span>
                </div>
              </div>
            </div>

            {/* Role & Empresa badges */}
            <div className="flex flex-wrap gap-2 mb-4">
              {user.papel === 'admin' ? (
                <Badge variant="default" className="bg-[rgb(var(--accent-primary) / 0.12)] text-primariaapp border-0 shadow-none text-xs">
                  <Shield className="w-3 h-3 mr-1" /> Admin
                </Badge>
              ) : (
                <Badge variant="default" className="bg-[var(--surface-highlight)] text-secondary border-0 shadow-none text-xs">
                  <UserCog className="w-3 h-3 mr-1" /> Funcionário
                </Badge>
              )}
              {user.empresas && (
                <Badge variant="default" className="bg-[rgb(var(--accent-secondary) / 0.10)] text-[rgb(var(--accent-secondary))] border-0 shadow-none text-xs">
                  <Building2 className="w-3 h-3 mr-1" /> {Array.isArray(user.empresas) ? user.empresas[0]?.nome : user.empresas?.nome || '—'}
                </Badge>
              )}
            </div>

            {/* Usage metrics */}
            {(() => {
              const stats = usageStats.find(s => s.usuario_id === user.id)
              if (!stats) return null
              return (
                <div className="grid grid-cols-3 gap-2 mb-4">
                  <div className="bg-[var(--surface-highlight)] rounded-xl px-3 py-2 text-center">
                    <p className="text-[10px] uppercase tracking-wider text-secondary">Análises</p>
                    <p className="text-sm font-bold text-texto">{stats.total_analises}</p>
                  </div>
                  <div className="bg-[var(--surface-highlight)] rounded-xl px-3 py-2 text-center">
                    <p className="text-[10px] uppercase tracking-wider text-secondary">Tokens</p>
                    <p className="text-sm font-bold text-texto">{stats.total_tokens.toLocaleString('pt-BR')}</p>
                  </div>
                  <div className="bg-[var(--surface-highlight)] rounded-xl px-3 py-2 text-center">
                    <p className="text-[10px] uppercase tracking-wider text-secondary">Custo</p>
                    <p className="text-sm font-bold text-primariaapp">
                      {stats.total_custo.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                    </p>
                  </div>
                </div>
              )
            })()}

            {/* Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-app">
              <span className="text-xs text-secondary">
                {new Date(user.created_at).toLocaleDateString("pt-BR")}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-secondary hover:text-texto"
                  onClick={(e) => handleOpenEdit(user, e)}
                >
                  <Edit className="h-3.5 w-3.5" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs text-secondary hover:text-primariaapp"
                  onClick={() => handleRoleChange(user.id, user.papel === 'admin' ? 'funcionario' : 'admin')}
                >
                  <ShieldAlert className="h-3.5 w-3.5 mr-1" />
                  {user.papel === 'admin' ? 'Rebaixar' : 'Promover'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 w-7 p-0 text-secondary hover:text-descartavel"
                  onClick={() => handleDelete(user.id)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="sm:col-span-2 lg:col-span-3 surface-card rounded-[20px] p-12 soft-stroke text-center">
            <UserCog className="h-10 w-10 text-secondary mx-auto mb-3 opacity-40" />
            <p className="text-secondary">
              {searchTerm ? "Nenhum usuário encontrado para essa busca." : "Nenhum usuário cadastrado."}
            </p>
          </div>
        )}
      </div>

      {/* Modal de convite / edição */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[480px] border-app-strong bg-[rgb(var(--bg-card))]">
          <form onSubmit={handleSave}>
            <DialogHeader>
              <DialogTitle className="text-texto">
                {editingData ? "Editar Usuário" : "Cadastrar na Plataforma"}
              </DialogTitle>
              <DialogDescription className="text-secondary">
                {editingData 
                  ? "Atualize os dados e acessos do usuário." 
                  : "O usuário receberá um link mágico no e-mail para configurar a senha."}
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-5">
              {editingData && <input type="hidden" name="id" value={editingData.id} />}
              <div className="space-y-2">
                <Label htmlFor="nome">Nome Completo *</Label>
                <Input 
                  id="nome" 
                  name="nome" 
                  defaultValue={editingData?.nome || ""}
                  placeholder="Maria Silva" 
                  required 
                  className="bg-input-app" 
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">E-mail *</Label>
                <Input 
                  id="email" 
                  name="email" 
                  type="email" 
                  defaultValue={editingData?.email || ""}
                  placeholder="maria@farmacia.com" 
                  required 
                  disabled={!!editingData}
                  className="bg-input-app disabled:opacity-50" 
                />
                {editingData && <p className="text-xs text-secondary mt-1">O e-mail não pode ser alterado.</p>}
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="papel">Nível de Acesso</Label>
                  <Select name="papel" defaultValue={editingData?.papel || "funcionario"}>
                    <SelectTrigger className="bg-input-app">
                      <SelectValue placeholder="Selecione" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">Administrador</SelectItem>
                      <SelectItem value="funcionario">Funcionário</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="empresa_id">Empresa *</Label>
                  <Select name="empresa_id" defaultValue={editingData?.empresa_id || empresaIdFilter || ""}>
                    <SelectTrigger className="bg-input-app">
                      <SelectValue placeholder="Selecione a empresa" />
                    </SelectTrigger>
                    <SelectContent>
                      {empresas.map(emp => (
                        <SelectItem key={emp.id} value={emp.id}>
                          {emp.nome}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
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
                {isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Mail className="mr-2 h-4 w-4" />}
                {isPending ? "Salvando..." : (editingData ? "Salvar Alterações" : "Enviar Convite")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
