"use client"

import * as React from "react"
import { useTransition } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { useToast } from "@/hooks/use-toast"
import { login } from "./actions"
import { Loader2 } from "lucide-react"
import Link from "next/link"

export default function LoginPage() {
  const [isPending, startTransition] = useTransition()
  const { toast } = useToast()

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)

    startTransition(async () => {
      const result = await login(formData)
      if (result?.error) {
        toast({
          variant: "destructive",
          title: "Erro de autenticação",
          description: result.error,
        })
      }
    })
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-fundo p-4 relative overflow-hidden">
      {/* Background decorativo */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primaria/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-secondaryaccent/10 rounded-full blur-[120px] pointer-events-none" />
      
      <Card className="w-full max-w-md shadow-cartao relative z-10 border-borderapp">
        <CardHeader className="space-y-1 pb-8">
          <div className="flex items-center justify-center mb-6">
            <div className="h-12 w-12 bg-primaria rounded-xl flex items-center justify-center shadow-primario">
              <span className="text-xl font-bold text-white tracking-widest text-center leading-none">C<br />P</span>
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-center text-texto">Entre na sua conta</CardTitle>
          <CardDescription className="text-center text-secondarytext">
            Digite seu e-mail e senha para acessar o painel
          </CardDescription>
        </CardHeader>
        <CardContent>
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
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Senha</Label>
                <Link 
                  href="/auth/recuperar-senha" 
                  className="text-sm font-medium text-primaria hover:underline"
                  tabIndex={-1}
                >
                  Esqueceu a senha?
                </Link>
              </div>
              <Input 
                id="password" 
                name="password" 
                type="password" 
                placeholder="••••••••"
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
                  Entrando...
                </>
              ) : (
                "Entrar"
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <div className="text-sm text-center text-mutedtext">
            Acesso restrito para administradores e empresas cadastradas no Compras PRO.
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
