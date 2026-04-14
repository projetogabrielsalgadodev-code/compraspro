"use client"

import * as React from "react"
import { useTransition, useState } from "react"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { createPassword } from "./actions"
import { Loader2, ArrowRight, ShieldCheck, Eye, EyeOff } from "lucide-react"

export default function CriarSenhaPage() {
  const [isPending, startTransition] = useTransition()
  const [isSuccess, setIsSuccess] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirm, setShowConfirm] = useState(false)
  const { toast } = useToast()
  const router = useRouter()

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    
    const password = formData.get('password') as string
    const confirmPassword = formData.get('confirmPassword') as string

    if (password.length < 6) {
      toast({
        variant: "destructive",
        title: "Senha muito curta",
        description: "A senha deve ter no mínimo 6 caracteres.",
      })
      return
    }

    if (password !== confirmPassword) {
       toast({
         variant: "destructive",
         title: "Senhas diferentes",
         description: "A confirmação de senha precisa ser idêntica.",
       })
       return
    }

    startTransition(async () => {
      const result = await createPassword(formData)
      if (result?.error) {
        toast({
          variant: "destructive",
          title: "Erro ao criar senha",
          description: result.error,
        })
      } else if (result?.success) {
        setIsSuccess(true)
        toast({
          title: "Tudo pronto!",
          description: result.success,
        })
        
        setTimeout(() => {
           router.push("/home")
        }, 2500)
      }
    })
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-fundo p-4 relative overflow-hidden">
      {/* Background decorativo */}
      <div className="absolute top-[-10%] right-[-5%] w-[35%] h-[35%] bg-primaria/15 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[30%] h-[30%] bg-tertiaryaccent/20 rounded-full blur-[100px] pointer-events-none" />
      
      <Card className="w-full max-w-md shadow-cartao relative z-10 border-borderapp">
        <CardHeader className="space-y-1 pb-6">
          <div className="flex justify-center mb-3">
            <div className="h-14 w-14 bg-gradient-to-br from-[rgb(var(--accent-primary))] to-[rgb(var(--accent-secondary))] rounded-2xl flex items-center justify-center shadow-lg">
              <ShieldCheck className="h-7 w-7 text-white" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-center text-texto">
            Bem-vindo ao Compras PRO!
          </CardTitle>
          <CardDescription className="text-center text-secondarytext">
            Seu convite foi aceito. Agora crie uma senha segura para acessar o sistema.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isSuccess ? (
            <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
              <div className="h-16 w-16 rounded-full bg-[rgb(var(--accent-primary)/0.12)] flex items-center justify-center">
                <ShieldCheck className="h-8 w-8 text-primariaapp" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-texto">Conta configurada!</h3>
                <p className="text-sm text-secondarytext">
                  Redirecionando para o sistema...
                </p>
              </div>
              <Loader2 className="h-6 w-6 animate-spin text-primariaapp" />
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="password">Senha</Label>
                <div className="relative">
                  <Input 
                    id="password" 
                    name="password" 
                    type={showPassword ? "text" : "password"}
                    placeholder="Mínimo 6 caracteres"
                    required 
                    minLength={6}
                    className="bg-inputapp pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary hover:text-texto transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirme a Senha</Label>
                <div className="relative">
                  <Input 
                    id="confirmPassword" 
                    name="confirmPassword" 
                    type={showConfirm ? "text" : "password"}
                    placeholder="Repita a senha"
                    required 
                    minLength={6}
                    className="bg-inputapp pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirm(!showConfirm)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary hover:text-texto transition-colors"
                    tabIndex={-1}
                  >
                    {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="rounded-lg bg-[var(--surface-highlight)] p-3 text-xs text-secondary space-y-1">
                <p>🔒 Dicas para uma senha segura:</p>
                <ul className="list-disc list-inside space-y-0.5 ml-1">
                  <li>Mínimo de 6 caracteres</li>
                  <li>Misture letras maiúsculas e minúsculas</li>
                  <li>Inclua números e caracteres especiais</li>
                </ul>
              </div>

              <Button 
                type="submit" 
                className="w-full bg-action-primary hover:bg-action-primary/90 text-white font-semibold py-6 rounded-lg transition-all mt-2"
                disabled={isPending}
              >
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Criando senha...
                  </>
                ) : (
                  <>
                    Criar senha e entrar
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
