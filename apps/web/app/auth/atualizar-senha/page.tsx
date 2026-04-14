"use client"

import * as React from "react"
import { useTransition, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { updatePassword } from "./actions"
import { Loader2, ArrowRight } from "lucide-react"

export default function AtualizarSenhaPage() {
  const [isPending, startTransition] = useTransition()
  const [isSuccess, setIsSuccess] = useState(false)
  const { toast } = useToast()
  const router = useRouter()

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    
    const password = formData.get('password') as string
    const confirmPassword = formData.get('confirmPassword') as string

    if (password !== confirmPassword) {
       toast({
         variant: "destructive",
         title: "Senhas diferentes",
         description: "A confirmação de senha precisa ser idêntica.",
       })
       return
    }

    startTransition(async () => {
      const result = await updatePassword(formData)
      if (result?.error) {
        toast({
          variant: "destructive",
          title: "Erro ao atualizar",
          description: result.error,
        })
      } else if (result?.success) {
        setIsSuccess(true)
        toast({
          title: "Senha atualizada!",
          description: result.success,
        })
        
        // Redireciona para o admin aps 2 seg
        setTimeout(() => {
           router.push("/home")
        }, 2000)
      }
    })
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-fundo p-4 relative overflow-hidden">
      {/* Background decorativo */}
      <div className="absolute bottom-[10%] left-[-10%] w-[30%] h-[30%] bg-tertiaryaccent/20 rounded-full blur-[100px] pointer-events-none" />
      
      <Card className="w-full max-w-md shadow-cartao relative z-10 border-borderapp">
        <CardHeader className="space-y-1 pb-6">
          <div className="flex justify-center mb-2">
            <div className="h-12 w-12 bg-primaria rounded-xl flex items-center justify-center shadow-primario">
              <span className="text-xl font-bold text-white tracking-widest text-center leading-none">C<br />P</span>
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-center text-texto">Nova Senha</CardTitle>
          <CardDescription className="text-center text-secondarytext">
            Por favor, defina sua nova senha abaixo.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isSuccess ? (
            <div className="flex flex-col items-center justify-center py-6 text-center space-y-4">
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-texto">Tudo pronto!</h3>
                <p className="text-sm text-secondarytext">
                  Redirecionando para o sistema...
                </p>
              </div>
              <Loader2 className="h-8 w-8 animate-spin text-primaria" />
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">Nova Senha</Label>
                <Input 
                  id="password" 
                  name="password" 
                  type="password" 
                  placeholder="••••••••"
                  required 
                  minLength={6}
                  className="bg-inputapp"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirme a Nova Senha</Label>
                <Input 
                  id="confirmPassword" 
                  name="confirmPassword" 
                  type="password" 
                  placeholder="••••••••"
                  required 
                  minLength={6}
                  className="bg-inputapp"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full bg-action-primary hover:bg-action-primary/90 text-white font-semibold py-6 rounded-lg transition-all mt-4"
                disabled={isPending}
              >
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Salvando...
                  </>
                ) : (
                  <>
                    Salvar senha
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </>
                )}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
