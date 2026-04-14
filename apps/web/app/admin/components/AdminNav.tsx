"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Building2, Users, Bot } from "lucide-react"
import { cn } from "@/lib/utils"

export function AdminNav() {
  const pathname = usePathname()

  const tabs = [
    { name: "Empresas", href: "/admin/empresas", icon: Building2 },
    { name: "Usuários", href: "/admin/usuarios", icon: Users },
    { name: "Configurações Agente", href: "/admin/agente", icon: Bot },
  ]

  return (
    <div className="mb-8 border-b border-app">
      <nav className="-mb-px flex space-x-6" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = pathname === tab.href || pathname?.startsWith(`${tab.href}/`)
          const Icon = tab.icon

          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "group inline-flex items-center gap-2 border-b-2 py-4 px-1 text-sm font-medium transition-colors",
                isActive
                  ? "border-primariaapp text-primariaapp"
                  : "border-transparent text-secondary hover:border-app-strong hover:text-texto"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4",
                  isActive ? "text-primariaapp" : "text-secondary group-hover:text-texto"
                )}
                aria-hidden="true"
              />
              {tab.name}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
