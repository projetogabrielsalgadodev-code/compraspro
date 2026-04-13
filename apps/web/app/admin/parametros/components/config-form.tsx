"use client"

import { useState, useEffect, useTransition } from "react"
import { saveConfiguracao, getConfiguracao } from "../actions"
import { useToast } from "@/hooks/use-toast"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Loader2, Save, ActivitySquare } from "lucide-react"

type EmpresaLite = {
  id: string
  nome: string
}

export function ConfigForm({ empresas }: { empresas: EmpresaLite[] }) {
  const [empresaId, setEmpresaId] = useState<string>("")
  const [margem, setMargem] = useState("30.00")
  const [dias, setDias] = useState("90")
  const [variacao, setVariacao] = useState("15.00")
  
  const [isLoadingConfig, startLoadingConfig] = useTransition()
  const [isSaving, startSaving] = useTransition()
  const { toast } = useToast()

  // Quando a empresa muda, buscar configurações dela
  useEffect(() => {
    if (!empresaId) return

    startLoadingConfig(async () => {
      const config = await getConfiguracao(empresaId)
      if (config) {
        setMargem(config.margem_lucro_padrao || "30.00")
        setDias(config.ignorar_historico_acima_dias || "90")
        setVariacao(config.percentual_variacao_alerta || "15.00")
      } else {
        // Fallback default caso nao tenha registro
        setMargem("30.00")
        setDias("90")
        setVariacao("15.00")
      }
    })
  }, [empresaId])

  const handleSave = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!empresaId) {
      toast({ variant: "destructive", title: "Erro", description: "Selecione uma empresa primeiro." })
      return
    }

    const formData = new FormData(e.currentTarget)
    formData.append("empresa_id", empresaId)

    startSaving(async () => {
      const result = await saveConfiguracao(formData)
      if (result.error) {
        toast({ variant: "destructive", title: "Falha ao salvar", description: result.error })
      } else {
        toast({ title: "Configurações Atualizadas", description: result.success })
      }
    })
  }

  return (
    <div className="space-y-6">
      <Card className="border-borderapp bg-card shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl">Empresa Alvo</CardTitle>
          <CardDescription>
            Selecione qual conta será afetada por estes parâmetros.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-w-md space-y-2">
            <Label htmlFor="empresa">Organização</Label>
            <Select value={empresaId} onValueChange={setEmpresaId}>
              <SelectTrigger id="empresa" className="bg-inputapp">
                <SelectValue placeholder="Selecione uma filial..." />
              </SelectTrigger>
              <SelectContent>
                {empresas.map(emp => (
                  <SelectItem key={emp.id} value={emp.id}>{emp.nome}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card className="border-borderapp bg-card shadow-sm relative overflow-hidden">
        {/* State visual feedback */}
        {isLoadingConfig && (
           <div className="absolute inset-0 bg-fundo/40 backdrop-blur-[2px] z-10 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primaria" />
           </div>
        )}

        <form onSubmit={handleSave}>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <ActivitySquare className="h-5 w-5 text-primaria" />
              <CardTitle className="text-xl">Algoritmo de IA e Análise</CardTitle>
            </div>
            <CardDescription>
              Ajuste as métricas de tolerância usadas pelo sistema para formular recomendações de compras automáticas.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="margem_lucro_padrao" className="flex items-center space-x-2">
                <span>Margem de Lucro Padrão (%)</span>
              </Label>
              <Input 
                id="margem_lucro_padrao" 
                name="margem_lucro_padrao" 
                type="number"
                step="0.01" 
                value={margem}
                onChange={e => setMargem(e.target.value)}
                required
                className="bg-inputapp font-mono"
              />
              <p className="text-xs text-mutedtext">Utilizado para projetar o Lucro Bruto nas tabelas.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="ignorar_historico_acima_dias">Ignorar Histórico Acima de (Dias)</Label>
              <Input 
                id="ignorar_historico_acima_dias" 
                name="ignorar_historico_acima_dias" 
                type="number" 
                value={dias}
                onChange={e => setDias(e.target.value)}
                required
                className="bg-inputapp font-mono"
              />
              <p className="text-xs text-mutedtext">Preços fora deste range não comporão a média do produto.</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="percentual_variacao_alerta">Alerta de Variação Grosseira (%)</Label>
              <Input 
                id="percentual_variacao_alerta" 
                name="percentual_variacao_alerta" 
                type="number"
                step="0.01" 
                value={variacao}
                onChange={e => setVariacao(e.target.value)}
                required
                className="bg-inputapp font-mono"
              />
              <p className="text-xs text-mutedtext">Avisa o usuário se o preço atual estiver distante da média acima deste limite.</p>
            </div>
          </CardContent>
          <CardFooter className="bg-fundo/40 border-t border-borderapp py-4 flex justify-end">
            <Button 
               type="submit" 
               disabled={isSaving || !empresaId} 
               className="bg-action-primary hover:bg-action-primary/90 text-white min-w-[150px]"
            >
              {isSaving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
              Salvar Parâmetros
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
