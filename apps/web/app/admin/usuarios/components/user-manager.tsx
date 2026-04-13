"use client"

import { useState, useTransition } from "react"
import { inviteUser, updateRole, deleteUser } from "../actions"
import { useToast } from "@/hooks/use-toast"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { MoreHorizontal, Plus, Shield, ShieldAlert, Loader2, Trash2, UserCog } from "lucide-react"

type UserProfile = {
  id: string
  nome: string
  email: string
  papel: string
  created_at: string
}

export function UserManager({ initialUsers }: { initialUsers: UserProfile[] }) {
  const [isOpen, setIsOpen] = useState(false)
  const [isPending, startTransition] = useTransition()
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
    // Idealmente um alerta de confiormaçao viria aqui
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

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button className="bg-action-primary hover:bg-action-primary/90 text-white">
              <Plus className="mr-2 h-4 w-4" /> Novo Usuário
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px] bg-fundo border-borderapp">
            <form onSubmit={handleInvite}>
              <DialogHeader>
                <DialogTitle className="text-texto">Convidar para a Plataforma</DialogTitle>
                <DialogDescription className="text-secondarytext">
                  Eles receberão um link mágico no e-mail para configurar a senha.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="nome">Nome Completo</Label>
                  <Input id="nome" name="nome" placeholder="Jane Doe" required className="bg-inputapp" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">E-mail</Label>
                  <Input id="email" name="email" type="email" placeholder="jane@farmacia.com" required className="bg-inputapp" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="papel">Nível de Acesso</Label>
                  <Select name="papel" defaultValue="funcionario">
                    <SelectTrigger className="bg-inputapp">
                      <SelectValue placeholder="Selecione o acesso" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">Administrador Total</SelectItem>
                      <SelectItem value="funcionario">Funcionário (Comum)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={isPending} className="bg-action-primary">
                  {isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Enviar Convite"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="rounded-md border border-borderapp bg-card">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent border-borderapp">
              <TableHead className="text-mutedtext">Membro</TableHead>
              <TableHead className="text-mutedtext">Função</TableHead>
              <TableHead className="text-mutedtext">Data de Entrada</TableHead>
              <TableHead className="text-right text-mutedtext">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {initialUsers.map((user) => (
              <TableRow key={user.id} className="border-borderapp hover:bg-black/5">
                <TableCell>
                  <div className="font-medium text-texto">{user.nome}</div>
                  <div className="text-sm text-secondarytext">{user.email}</div>
                </TableCell>
                <TableCell>
                  {user.papel === 'admin' ? (
                    <Badge variant="default" className="bg-sucesso-claro text-sucesso border-sucesso/20 shadow-none">
                      <Shield className="w-3 h-3 mr-1" /> Admin
                    </Badge>
                  ) : (
                    <Badge variant="default" className="bg-secondary/10 text-secondary border-transparent shadow-none">
                      <UserCog className="w-3 h-3 mr-1" /> Func.
                    </Badge>
                  )}
                </TableCell>
                <TableCell className="text-secondarytext">
                  {new Date(user.created_at).toLocaleDateString("pt-BR")}
                </TableCell>
                <TableCell className="text-right">
                   <DropdownMenu>
                     <DropdownMenuTrigger asChild>
                       <Button variant="ghost" className="h-8 w-8 p-0 text-secondarytext">
                         <span className="sr-only">Abrir menu</span>
                         <MoreHorizontal className="h-4 w-4" />
                       </Button>
                     </DropdownMenuTrigger>
                     <DropdownMenuContent align="end" className="bg-card border-borderapp">
                       <DropdownMenuItem 
                         onClick={() => handleRoleChange(user.id, user.papel === 'admin' ? 'funcionario' : 'admin')}
                         className="cursor-pointer text-texto focus:bg-primaria/10"
                       >
                         <ShieldAlert className="mr-2 h-4 w-4" />
                         <span>Tornar {user.papel === 'admin' ? 'Funcionário' : 'Admin'}</span>
                       </DropdownMenuItem>
                       <DropdownMenuItem 
                         onClick={() => handleDelete(user.id)}
                         className="cursor-pointer text-descartavel focus:bg-descartavel/10"
                       >
                         <Trash2 className="mr-2 h-4 w-4" />
                         <span>Revogar Acesso</span>
                       </DropdownMenuItem>
                     </DropdownMenuContent>
                   </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
            {initialUsers.length === 0 && (
              <TableRow className="border-borderapp hover:bg-transparent">
                <TableCell colSpan={4} className="h-24 text-center text-mutedtext">
                  Nenhum registro encontrado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
