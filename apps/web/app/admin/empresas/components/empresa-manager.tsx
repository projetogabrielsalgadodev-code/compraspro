"use client"

import { useState, useTransition } from "react"
import { upsertEmpresa, deleteEmpresa } from "../actions"
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
import { Badge } from "@/components/ui/badge"
import { MoreHorizontal, Plus, Edit, Trash2, Loader2, Building2 } from "lucide-react"

type Empresa = {
  id: string
  nome: string
  cnpj: string
  created_at: string
  qtdeUsuarios: number
}

export function EmpresaManager({ initialData }: { initialData: Empresa[] }) {
  const [isOpen, setIsOpen] = useState(false)
  const [editingData, setEditingData] = useState<Empresa | null>(null)
  const [isPending, startTransition] = useTransition()
  const { toast } = useToast()

  const handleOpenNew = () => {
     setEditingData(null)
     setIsOpen(true)
  }

  const handleOpenEdit = (empresa: Empresa) => {
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

  const handleDelete = (id: string) => {
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

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
             <Button onClick={handleOpenNew} className="bg-action-primary hover:bg-action-primary/90 text-white">
               <Plus className="mr-2 h-4 w-4" /> Cadastrar Empresa
             </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px] bg-fundo border-borderapp">
            <form onSubmit={handleSave}>
              <DialogHeader>
                <DialogTitle className="text-texto">{editingData ? "Editar Empresa" : "Nova Empresa"}</DialogTitle>
                <DialogDescription className="text-secondarytext">
                  Preencha os dados da filial ou farmácia principal.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {/* Campo oculto p/ ID se em modo edit */}
                {editingData && <input type="hidden" name="id" value={editingData.id} />}
                
                <div className="space-y-2">
                  <Label htmlFor="nome">Nome / Razão Social</Label>
                  <Input 
                     id="nome" 
                     name="nome" 
                     defaultValue={editingData?.nome || ""} 
                     placeholder="Drogaria Nova Esperança" 
                     required className="bg-inputapp" 
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="cnpj">CNPJ</Label>
                  <Input 
                     id="cnpj" 
                     name="cnpj" 
                     defaultValue={editingData?.cnpj || ""} 
                     placeholder="00.000.000/0000-00" 
                     required className="bg-inputapp" 
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="submit" disabled={isPending} className="bg-action-primary">
                  {isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Salvar Dados"}
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
              <TableHead className="text-mutedtext">Nome</TableHead>
              <TableHead className="text-mutedtext">CNPJ</TableHead>
              <TableHead className="text-mutedtext text-center">Usuários</TableHead>
              <TableHead className="text-right text-mutedtext">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {initialData.map((empresa) => (
              <TableRow key={empresa.id} className="border-borderapp hover:bg-black/5">
                <TableCell>
                  <div className="font-medium text-texto flex items-center">
                     <Building2 className="mr-2 h-4 w-4 text-mutedtext" /> 
                     {empresa.nome}
                  </div>
                </TableCell>
                <TableCell className="text-secondarytext font-mono text-sm">
                  {empresa.cnpj}
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant="default" className="bg-primaria/10 text-primaria font-normal">
                     {empresa.qtdeUsuarios} {empresa.qtdeUsuarios === 1 ? 'Membro' : 'Membros'}
                  </Badge>
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
                         onClick={() => handleOpenEdit(empresa)}
                         className="cursor-pointer text-texto focus:bg-primaria/10"
                       >
                         <Edit className="mr-2 h-4 w-4" />
                         <span>Editar</span>
                       </DropdownMenuItem>
                       <DropdownMenuItem 
                         onClick={() => handleDelete(empresa.id)}
                         className="cursor-pointer text-descartavel focus:bg-descartavel/10"
                       >
                         <Trash2 className="mr-2 h-4 w-4" />
                         <span>Remover Base</span>
                       </DropdownMenuItem>
                     </DropdownMenuContent>
                   </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
            {initialData.length === 0 && (
              <TableRow className="border-borderapp hover:bg-transparent">
                <TableCell colSpan={4} className="h-24 text-center text-mutedtext">
                  Nenhuma empresa encontrada.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
