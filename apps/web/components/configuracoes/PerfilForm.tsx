"use client"

import { useRef, useState, useTransition } from "react"
import { Camera, Loader2, Save, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { updatePerfil, uploadAvatar } from "@/app/(dashboard)/configuracoes/actions"
import { formatTelefone } from "@/lib/formatters"

interface PerfilData {
  id: string
  nome: string | null
  email: string | null
  telefone: string | null
  avatar_url: string | null
  papel: string
}

export function PerfilForm({ perfil }: { perfil: PerfilData }) {
  const [form, setForm] = useState(perfil)
  const [mensagem, setMensagem] = useState<string | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [isPending, startTransition] = useTransition()
  const [uploadingAvatar, setUploadingAvatar] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function update<K extends keyof typeof form>(key: K, value: string) {
    setForm((cur) => ({ ...cur, [key]: value }))
  }

  async function handleAvatarChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    // Validar tamanho (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      setErro("Imagem deve ter no máximo 2MB.")
      return
    }

    setUploadingAvatar(true)
    setErro(null)
    try {
      const fd = new FormData()
      fd.set("file", file)
      const result = await uploadAvatar(fd)
      if (result.error) {
        setErro(result.error)
      } else if (result.url) {
        setForm((cur) => ({ ...cur, avatar_url: result.url! }))
        setMensagem("Avatar atualizado!")
      }
    } catch {
      setErro("Falha ao enviar avatar.")
    } finally {
      setUploadingAvatar(false)
    }
  }

  function salvar() {
    setMensagem(null)
    setErro(null)
    startTransition(async () => {
      const fd = new FormData()
      fd.set("nome", form.nome || "")
      fd.set("telefone", form.telefone || "")
      if (form.avatar_url) fd.set("avatar_url", form.avatar_url)

      const result = await updatePerfil(fd)
      if (result.error) setErro(result.error)
      else setMensagem(result.success!)
    })
  }

  const initials = (form.nome || "U").slice(0, 2).toUpperCase()

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-3">
          <span className="ds-icon-chip text-primariaapp"><User className="h-4 w-4" /></span>
          <div>
            <p className="ds-eyebrow">Conta</p>
            <CardTitle className="mt-2">Meu perfil</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Avatar */}
        <div className="flex items-center gap-6">
          <div className="relative">
            {form.avatar_url ? (
              <img
                src={form.avatar_url}
                alt="Avatar"
                className="h-20 w-20 rounded-full object-cover border-2 border-app"
              />
            ) : (
              <div className="h-20 w-20 rounded-full bg-gradient-to-br from-[#245BFF] to-[#0EA5E9] flex items-center justify-center text-white text-xl font-bold">
                {initials}
              </div>
            )}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingAvatar}
              className="absolute -bottom-1 -right-1 h-8 w-8 rounded-full bg-[rgb(var(--accent-primary))] text-white flex items-center justify-center shadow-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {uploadingAvatar ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Camera className="h-3.5 w-3.5" />}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleAvatarChange}
            />
          </div>
          <div>
            <p className="font-semibold text-texto">{form.nome || "Usuário"}</p>
            <p className="text-sm text-secondary">{form.email}</p>
            <span className="mt-1 inline-block rounded-full bg-[rgb(var(--accent-primary)/0.1)] px-3 py-0.5 text-xs font-medium text-[rgb(var(--accent-primary))]">
              {form.papel === "admin" ? "Administrador" : form.papel === "comprador" ? "Comprador" : form.papel}
            </span>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Nome completo *">
            <Input value={form.nome || ""} onChange={(e) => update("nome", e.target.value)} placeholder="Seu nome" />
          </Field>
          <Field label="E-mail">
            <Input value={form.email || ""} disabled className="opacity-60 cursor-not-allowed" />
            <p className="text-xs text-secondary mt-1">O e-mail é vinculado à conta e não pode ser alterado aqui.</p>
          </Field>
          <Field label="Telefone">
            <Input value={form.telefone || ""} onChange={(e) => update("telefone", formatTelefone(e.target.value))} placeholder="(00) 00000-0000" />
          </Field>
          <Field label="Função">
            <Input value={form.papel === "admin" ? "Administrador" : form.papel === "comprador" ? "Comprador" : form.papel} disabled className="opacity-60 cursor-not-allowed" />
            <p className="text-xs text-secondary mt-1">Função definida pelo administrador.</p>
          </Field>
        </div>

        {erro ? <p className="text-sm text-descartavel">{erro}</p> : null}
        {mensagem ? <p className="text-sm text-[rgb(var(--accent-primary))]">{mensagem}</p> : null}

        <div className="flex justify-end">
          <Button onClick={salvar} disabled={isPending} className="gap-2 px-6">
            {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
            Salvar perfil
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="space-y-2">
      <span className="text-sm font-medium text-texto">{label}</span>
      {children}
    </label>
  )
}
