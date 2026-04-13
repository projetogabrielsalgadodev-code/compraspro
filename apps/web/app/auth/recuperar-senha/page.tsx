"use client"

import * as React from "react"
import { useTransition, useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { requestPasswordReset } from "./actions"
import { Loader2, ArrowLeft, CheckCircle2 } from "lucide-react"
import Link from "next/link"

export default function RecuperarSenhaPage() {
  const [isPending, startTransition] = useTransition()
  const [isSuccess, setIsSuccess] = useState(false)
  const { toast } = useToast()

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    startTransition(async () => {
      const result = await requestPasswordReset(formData)
      if (result?.error) {
        toast({
          variant: "destructive",
          title: "Erro ao solicitar recuperação",
          description: result.error,
        })
      } else if (result?.success) {
        setIsSuccess(true)
        toast({
          title: "Link enviado!",
          description: result.success,
        })
      }
    })
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-fundo p-4 relative overflow-hidden">
      {/* Background decorativo */}
      <div className="absolute top-[10%] right-[-10%] w-[30%] h-[30%] bg-primaria/20 rounded-full blur-[100px] pointer-events-none" />
      
      <Card className="w-full max-w-md shadow-cartao relative z-10 border-borderapp">
        <CardHeader className="space-y-1 pb-6">
          <div className="flex justify-center mb-2">
            <div className="h-12 w-12 bg-primaria rounded-xl flex items-center justify-center shadow-primario">
              <span className="text-xl font-bold text-white tracking-widest text-center leading-none">C<br />P</span>
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-center text-texto">Recuperar Senha</CardTitle>
          <CardDescription className="text-center text-secondarytext">
            Digite seu e-mail para receber um link de recuperação
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isSuccess ? (
            <div className="flex flex-col items-center justify-center py-6 text-center space-y-4">
              <CheckCircle2 className="h-16 w-16 text-sucesso-DEFAULT" />
              <div className="space-y-2">
                <h3 className="text-lg font-medium text-texto">Verifique seu e-mail</h3>
                <p className="text-sm text-secondarytext">
                  Enviamos as instruções para redefinir sua senha. Confira também a caixa de spam.
                </p>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input 
                  id="email" 
                  name="email" 
                  type="email" 
                  placeholder="nome@exemplo.com" 
                  required 
                  className="bg-inputapp"
                />
              </div>
              <Button 
                type="submit" 
                className="w-full bg-action-primary hover:bg-action-primary/90 text-white font-semibold py-6 rounded-lg transition-all"
                disabled={isPending}
              >
                {isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Enviando...
                  </>
                ) : (
                  "Enviar link de recuperação"
                )}
              </Button>
            </form>
          )}
        </CardContent>
        <CardFooter className="flex justify-center border-t border-borderapp pt-6">
          <Link 
            href="/auth/login" 
            className="flex items-center text-sm font-medium text-secondarytext hover:text-primaria transition-colors"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar para o Login
          </Link>
        </CardFooter>
      </Card>
    </div>
  )
}
