"use client"

import { useState, useTransition } from "react"
import { inviteUser, updateRole, deleteUser } from "../actions"
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
  Mail, ShieldAlert, Building2, UserPlus 
} from "lucide-react"
import { cn } from "@/lib/utils"

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
}

export function UserManager({ initialUsers, empresas, empresaIdFilter }: UserManagerProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isPending, startTransition] = useTransition()
  const [searchTerm, setSearchTerm] = useState("")
  const { toast } = useToast()

  const handleInvite = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    startTransition(async () => {
      const result = await inviteUser(formData)
      if (result.error) {
        toast({
          variant: "destructive",
          title: "Erro ao convidar",
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
          onClick={() => setIsOpen(true)}
          className="bg-[linear-gradient(135deg,rgb(var(--accent-primary)),rgb(var(--accent-secondary)))] text-white font-semibold shadow-[0_8px_24px_rgba(36,76,255,0.28)] hover:shadow-[0_12px_32px_rgba(36,76,255,0.36)] transition-all hover:-translate-y-0.5"
        >
          <UserPlus className="mr-2 h-4 w-4" /> Convidar Usuário
        </Button>
      </div>

      {/* Stats strip */}
      <div className="grid grid-cols-3 gap-3">
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

            {/* Actions */}
            <div className="flex items-center justify-between pt-3 border-t border-app">
              <span className="text-xs text-secondary">
                {new Date(user.created_at).toLocaleDateString("pt-BR")}
              </span>
              <div className="flex items-center gap-1">
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

      {/* Modal de convite */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[480px] ds-panel border-app-strong">
          <form onSubmit={handleInvite}>
            <DialogHeader>
              <DialogTitle className="text-texto">Convidar para a Plataforma</DialogTitle>
              <DialogDescription className="text-secondary">
                O usuário receberá um link mágico no e-mail para configurar a senha.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-5">
              <div className="space-y-2">
                <Label htmlFor="nome">Nome Completo *</Label>
                <Input id="nome" name="nome" placeholder="Maria Silva" required className="bg-input-app" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">E-mail *</Label>
                <Input id="email" name="email" type="email" placeholder="maria@farmacia.com" required className="bg-input-app" />
              </div>
              <div className="grid sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="papel">Nível de Acesso</Label>
                  <Select name="papel" defaultValue="funcionario">
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
                  <Select name="empresa_id" defaultValue={empresaIdFilter || ""}>
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
                {isPending ? "Enviando..." : "Enviar Convite"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
