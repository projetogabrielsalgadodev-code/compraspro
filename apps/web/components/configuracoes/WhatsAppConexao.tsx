"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import {
  Loader2,
  MessageSquare,
  Plug,
  PlugZap,
  Power,
  QrCode,
  RefreshCw,
  Smartphone,
  Wifi,
  WifiOff,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type ConexaoStatus =
  | "sem_instancia"
  | "criando"
  | "aguardando_qr"
  | "conectada"
  | "desconectada"
  | "erro"

interface InstanciaInfo {
  instance_id?: string
  nome_instancia?: string
  profile_name?: string
  numero_telefone?: string
  qrcode?: string | null
  status: string
}

export function WhatsAppConexao() {
  const [status, setStatus] = useState<ConexaoStatus>("sem_instancia")
  const [instancia, setInstancia] = useState<InstanciaInfo | null>(null)
  const [qrcode, setQrcode] = useState<string | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const pollingCountRef = useRef(0)

  // ─── Carregar estado inicial ──────────────────────────────────────────
  const carregarInstancia = useCallback(async () => {
    try {
      const res = await fetch("/api/whatsapp/instancia")
      const data = await res.json()

      if (data.instancia) {
        setInstancia(data.instancia)
        const dbStatus = data.instancia.status as string

        if (dbStatus === "conectada") {
          setStatus("conectada")
        } else if (dbStatus === "aguardando_qr") {
          setStatus("aguardando_qr")
          iniciarPolling()
        } else {
          setStatus("desconectada")
        }
      } else {
        setStatus("sem_instancia")
      }
    } catch {
      setErro("Erro ao carregar status da instância.")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    carregarInstancia()
    return () => pararPolling()
  }, [carregarInstancia])

  // ─── Polling de status ────────────────────────────────────────────────
  function iniciarPolling() {
    pararPolling()
    pollingCountRef.current = 0

    pollingRef.current = setInterval(async () => {
      pollingCountRef.current++

      // Máx 2 minutos (40 × 3s)
      if (pollingCountRef.current > 40) {
        pararPolling()
        setStatus("erro")
        setErro("Tempo limite atingido. Tente novamente.")
        return
      }

      try {
        const res = await fetch("/api/whatsapp/instancia/status")
        const data = await res.json()

        if (data.status === "conectada") {
          pararPolling()
          setStatus("conectada")
          setQrcode(null)
          setInstancia((prev) => ({
            ...prev,
            ...data,
            status: "conectada",
          }))
        } else if (data.status === "aguardando_qr" && data.qrcode) {
          setQrcode(data.qrcode)
        } else if (data.status === "desconectada") {
          pararPolling()
          setStatus("desconectada")
          setQrcode(null)
        }
      } catch {
        // Ignora erros de polling silenciosamente
      }
    }, 3000)
  }

  function pararPolling() {
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  // ─── Ações ────────────────────────────────────────────────────────────
  async function criarInstancia() {
    setActionLoading(true)
    setErro(null)
    setStatus("criando")

    try {
      const res = await fetch("/api/whatsapp/instancia", { method: "POST" })
      const data = await res.json()

      if (!res.ok) {
        setErro(data.detail || data.error || "Erro ao criar instância.")
        setStatus("erro")
        return
      }

      setInstancia(data)
      if (data.qrcode) {
        setQrcode(data.qrcode)
        setStatus("aguardando_qr")
        iniciarPolling()
      } else {
        setStatus("aguardando_qr")
        iniciarPolling()
      }
    } catch {
      setErro("Erro de conexão. Tente novamente.")
      setStatus("erro")
    } finally {
      setActionLoading(false)
    }
  }

  async function desconectar() {
    setActionLoading(true)
    setErro(null)

    try {
      const res = await fetch("/api/whatsapp/instancia/desconectar", { method: "POST" })
      if (res.ok) {
        setStatus("desconectada")
        setQrcode(null)
        pararPolling()
      } else {
        const data = await res.json()
        setErro(data.detail || data.error || "Erro ao desconectar.")
      }
    } catch {
      setErro("Erro de conexão.")
    } finally {
      setActionLoading(false)
    }
  }

  async function reconectar() {
    setActionLoading(true)
    setErro(null)

    try {
      const res = await fetch("/api/whatsapp/instancia/reconectar", { method: "POST" })
      const data = await res.json()

      if (res.ok) {
        if (data.qrcode) setQrcode(data.qrcode)
        setStatus("aguardando_qr")
        iniciarPolling()
      } else {
        setErro(data.detail || data.error || "Erro ao reconectar.")
      }
    } catch {
      setErro("Erro de conexão.")
    } finally {
      setActionLoading(false)
    }
  }

  // ─── Render ───────────────────────────────────────────────────────────
  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader2 className="h-6 w-6 animate-spin text-secondary" />
          <span className="ml-3 text-secondary">Carregando...</span>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <span className="ds-icon-chip text-primariaapp">
              <MessageSquare className="h-4 w-4" />
            </span>
            <div>
              <p className="ds-eyebrow">Integração</p>
              <CardTitle className="mt-2">Conexão WhatsApp</CardTitle>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* Banner informativo */}
          <div className="ds-subpanel rounded-[24px] px-4 py-4 text-sm text-secondary">
            <p>
              Conecte o WhatsApp da farmácia para receber e analisar ofertas automaticamente.
              O sistema lerá as mensagens de grupos e contatos e processará novas ofertas a cada 2 horas.
            </p>
          </div>

          {/* Status Badge */}
          <StatusBadge status={status} instancia={instancia} />

          {/* QR Code Display */}
          {status === "aguardando_qr" && (
            <QRCodeDisplay qrcode={qrcode} />
          )}

          {/* Erro */}
          {erro && (
            <div className="flex items-start gap-3 rounded-2xl border border-descartavel/20 bg-descartavel/5 px-4 py-3">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-descartavel" />
              <p className="text-sm text-descartavel">{erro}</p>
            </div>
          )}

          {/* Ações */}
          <div className="flex flex-wrap gap-3">
            {status === "sem_instancia" && (
              <Button
                onClick={criarInstancia}
                disabled={actionLoading}
                className="gap-2 px-6"
              >
                {actionLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Plug className="h-4 w-4" />
                )}
                Conectar WhatsApp
              </Button>
            )}

            {status === "erro" && (
              <Button
                onClick={criarInstancia}
                disabled={actionLoading}
                className="gap-2 px-6"
              >
                {actionLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <RefreshCw className="h-4 w-4" />
                )}
                Tentar novamente
              </Button>
            )}

            {status === "criando" && (
              <Button disabled className="gap-2 px-6">
                <Loader2 className="h-4 w-4 animate-spin" />
                Criando instância...
              </Button>
            )}

            {status === "aguardando_qr" && (
              <div className="text-sm text-secondary flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Aguardando leitura do QR Code...
              </div>
            )}

            {status === "conectada" && (
              <Button
                onClick={desconectar}
                disabled={actionLoading}
                variant="ghost"
                className="gap-2 px-6 text-descartavel hover:bg-descartavel/10 hover:text-descartavel border-descartavel/30"
              >
                {actionLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Power className="h-4 w-4" />
                )}
                Desconectar
              </Button>
            )}

            {status === "desconectada" && (
              <Button
                onClick={reconectar}
                disabled={actionLoading}
                className="gap-2 px-6"
              >
                {actionLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <PlugZap className="h-4 w-4" />
                )}
                Reconectar
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Sub-componentes ────────────────────────────────────────────────────────

function StatusBadge({
  status,
  instancia,
}: {
  status: ConexaoStatus
  instancia: InstanciaInfo | null
}) {
  const configs: Record<
    ConexaoStatus,
    { icon: typeof Wifi; label: string; color: string; bgColor: string }
  > = {
    sem_instancia: {
      icon: WifiOff,
      label: "Nenhuma instância configurada",
      color: "text-secondary",
      bgColor: "bg-[rgb(var(--bg-surface-section))]",
    },
    criando: {
      icon: Loader2,
      label: "Criando instância...",
      color: "text-primariaapp",
      bgColor: "bg-primariaapp/5",
    },
    aguardando_qr: {
      icon: QrCode,
      label: "Aguardando leitura do QR Code",
      color: "text-[rgb(var(--accent-warning))]",
      bgColor: "bg-[rgb(var(--accent-warning)/0.08)]",
    },
    conectada: {
      icon: CheckCircle2,
      label: "WhatsApp conectado",
      color: "text-competitiva",
      bgColor: "bg-competitiva/5",
    },
    desconectada: {
      icon: XCircle,
      label: "WhatsApp desconectado",
      color: "text-descartavel",
      bgColor: "bg-descartavel/5",
    },
    erro: {
      icon: AlertCircle,
      label: "Erro na conexão",
      color: "text-descartavel",
      bgColor: "bg-descartavel/5",
    },
  }

  const config = configs[status]
  const Icon = config.icon

  return (
    <div className={`flex items-center gap-4 rounded-2xl ${config.bgColor} px-5 py-4`}>
      <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${config.bgColor} ${config.color}`}>
        <Icon className={`h-5 w-5 ${status === "criando" ? "animate-spin" : ""}`} />
      </div>
      <div className="flex-1">
        <p className={`text-sm font-semibold ${config.color}`}>{config.label}</p>
        {status === "conectada" && instancia && (
          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-secondary">
            {instancia.profile_name && (
              <span className="flex items-center gap-1">
                <Smartphone className="h-3 w-3" />
                {instancia.profile_name}
              </span>
            )}
            {instancia.numero_telefone && (
              <span className="flex items-center gap-1">
                <Wifi className="h-3 w-3" />
                +{instancia.numero_telefone}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function QRCodeDisplay({ qrcode }: { qrcode: string | null }) {
  if (!qrcode) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-dashed border-app py-12">
        <Loader2 className="h-8 w-8 animate-spin text-secondary" />
        <p className="text-sm text-secondary">Gerando QR Code...</p>
      </div>
    )
  }

  // QR pode vir como base64 puro ou data:image/png;base64,...
  const imageSrc = qrcode.startsWith("data:")
    ? qrcode
    : `data:image/png;base64,${qrcode}`

  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl border border-app bg-white p-6 dark:bg-[rgb(var(--bg-card))]">
      <div className="rounded-xl bg-white p-3">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageSrc}
          alt="QR Code do WhatsApp"
          className="h-64 w-64"
        />
      </div>
      <div className="space-y-1 text-center">
        <p className="text-sm font-semibold text-texto">Escaneie o QR Code</p>
        <p className="text-xs text-secondary">
          Abra o WhatsApp no celular → Dispositivos conectados → Conectar dispositivo
        </p>
      </div>
    </div>
  )
}
