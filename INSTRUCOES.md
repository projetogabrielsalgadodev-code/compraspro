# INSTRUÇÕES — ComprasPRO

> Documento operacional para agentes de IA e desenvolvedores que atuem no projeto.
> Última atualização: Maio/2026

---

## 1. Resumo do Projeto

**ComprasPRO** é uma plataforma de inteligência de compras para farmácias, desenvolvida sob demanda para a **Rede Inova** (cliente: Gabriel Salgado). O sistema recebe ofertas de fornecedores (via WhatsApp, Excel, imagens ou texto) e cruza automaticamente com histórico de preços, estoque atual e produtos equivalentes — entregando uma decisão clara: **comprar, aguardar ou descartar**.

**Visão**: ser a ferramenta definitiva de decisão de compra para gestores de farmácias, eliminando análises manuais e garantindo que nenhuma "oportunidade de ouro" seja perdida.

---

## 2. Histórico e Evolução

### Fase 1 — Concepção e MVP (Março/2026)
- **Início**: 12–15 de março de 2026.
- **Problema identificado**: o cliente recebia 400–500 mensagens de fornecedores por dia no WhatsApp e analisava manualmente cada oferta contra estoque e histórico — processo lento e falível.
- **Decisões arquiteturais**: Next.js (frontend), Python/FastAPI (backend IA), Supabase (banco + auth).
- **Primeiros 5 chats** com o cliente definiram as regras de negócio fundamentais:
  - **Chat 1** (14/mar): padrão de análise com Resumo Executivo + detalhamento por produto.
  - **Chat 2** (13/mar): equivalentes por princípio ativo, remoção de "Preço Venda", sugestão de pedido (`max(0, demanda_mes × 3 − estoque)`).
  - **Chat 3** (13/mar): regra obrigatória de preço unitário histórico = `valor_total_item / qtd_unitaria`.
  - **Chat 4** (13/mar): fonte de verdade do estoque = coluna `Estoque` do arquivo Sugcompra.
  - **Chat 5** (12/mar): cruzamento de bases (Sugcompra × Entradas por fornecedor × Vendas diárias), nível de confiança do match (Alto/Médio/Baixo), cálculos de cobertura e sazonalidade.

### Fase 2 — Construção do Motor de Análise (Março–Abril/2026)
- Implementação do fluxo completo: extração de itens via Claude API → matching por EAN/heurística → cálculos determinísticos em Python → persistência no Supabase.
- Criação do `analysis_engine.py` — motor 100% determinístico (zero dependência de LLM para cálculos).
- Implementação de weighted token scoring para matching de produtos.
- Suporte a ofertas com desconto percentual (sem preço absoluto).
- Busca de equivalentes por princípio ativo com filtro de categoria farmacêutica.
- Classificação automática: Ouro (≥20% desconto), Prata (5–20%), Atenção (0–5%), Descartável (ágio).

### Fase 3 — Estabilização e Transição Determinística (Abril/2026)
- Remoção de serviços legados (`agno_tools`, `matching_service`, `preco_service` antigos).
- Consolidação em arquitetura "Single Source of Truth" com `analysis_engine.py` + `offer_extractor.py`.
- Resolução de bugs de escala/multiplicador em preços unitários.
- Testes extensivos de pipeline end-to-end.

### Fase 4 — Integração WhatsApp (Abril–Maio/2026)
- **Integração com Uazapi** (API de WhatsApp Business):
  - Conexão self-service via QR Code pela plataforma.
  - Webhook para recepção de mensagens em tempo real.
  - Cron job (`pg_cron`) para análise automática de mensagens pendentes a cada 2h.
  - Sistema de deduplicação (UNIQUE constraint `instancia_id,message_id`).
  - Notificações em 3 canais: in-app (Supabase Realtime), email (Resend), WhatsApp (Uazapi).
- **Migração para plano pago da Uazapi** com refinamento de filtros de ingestão.
- Suporte a mídias (imagens com caption) e processamento assíncrono em background.

### Fase 5 — Refinamentos Contínuos (Maio/2026)
- Otimização do offer_extractor com multiplicador inteligente por categoria.
- Normalização de laboratórios (siglas → nomes completos).
- Melhorias no design system com modo escuro/claro premium.
- Dashboard administrativo com painel de métricas.

---

## 3. Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + shadcn/ui + Tailwind CSS |
| Backend IA | Python 3.11 + FastAPI + Agno framework |
| Banco de dados | Supabase (PostgreSQL + Auth + Storage + RLS) |
| Deploy Frontend | Vercel |
| Deploy Backend | Railway / Render (FastAPI) |
| IA / Extração | Claude (Anthropic) via Agno Agent com tool calling |
| WhatsApp | Uazapi (API WhatsApp Business) |
| Email | Resend (transacional) |
| Cron | `pg_cron` (PostgreSQL) |
| Monorepo | npm workspaces (`apps/web` + `python-api`) |

---

## 4. Instruções para Agentes de IA

### 4.1 Regras Inegociáveis
1. **Nunca criar lógica de preço histórico no frontend** — sempre via FastAPI/Python.
2. **Nunca usar estoque de fonte que não seja a tabela `estoque` do Supabase** (ou coluna `Estoque` do Sugcompra quando em contexto de arquivo).
3. **Nunca comparar produtos apenas por nome** — sempre priorizar EAN.
4. **Nunca expor dados de uma empresa para outra** — RLS é inegociável.
5. **Nunca usar `demanda_diaria` nas interfaces** — apenas `demanda_mes`.
6. **Nunca usar `any` no TypeScript** — strict mode obrigatório.
7. **Nunca hardcodar chaves de API** — usar `.env.local` (Next.js) e `.env` (FastAPI).

### 4.2 Regras de Cálculo
- **Preço unitário histórico**: `valor_total_item / qtd_unitaria` (nunca usar custo médio).
- **Sugestão de pedido**: `max(0, (demanda_mes × 3) − estoque_atual)`.
- **Classificação**:
  - 🥇 Ouro: `variação >= 20%` (desconto forte)
  - 🥈 Prata: `5% <= variação < 20%`
  - ⚠️ Atenção: `0% <= variação < 5%`
  - ❌ Descartável: `variação < 0%` (ágio) ou sem dados
- **Variação**: `((menor_histórico − preço_oferta) / menor_histórico) × 100`

### 4.3 Convenções de Código
- **TypeScript strict** em todo o frontend.
- **shadcn/ui** para componentes base. Não criar UI do zero se houver componente equivalente.
- **Server Components** por padrão no Next.js. `"use client"` apenas quando necessário.
- **Supabase client**: `createServerClient` em Server Components/Route Handlers, `createBrowserClient` em Client Components.
- **FastAPI**: um router por domínio, validação com Pydantic em todos os endpoints.
- **Design System**: seguir tokens definidos em `design system.md` — nunca usar valores arbitrários.

### 4.4 Variáveis de Ambiente Obrigatórias

```env
# Next.js
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
FASTAPI_URL=
NEXT_PUBLIC_APP_URL=
NEXT_PUBLIC_EMPRESA_ID_PADRAO=

# FastAPI
ANTHROPIC_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
CORS_ALLOWED_ORIGINS=

# WhatsApp / Cron
CRON_SECRET=
RESEND_API_KEY=
UAZAPI_ADMIN_TOKEN=
UAZAPI_BASE_URL=
```

### 4.5 Fluxo Principal (Análise de Oferta)
```
1. Usuário cola texto / faz upload / WhatsApp envia mensagem
2. Next.js → POST /api/ofertas/analisar (ou cron automático)
3. FastAPI → Claude API: extrai itens, preços, fornecedor
4. Para cada item:
   a. Busca EAN exato no índice (arquivo ou banco)
   b. Se não achar: weighted token scoring por descrição normalizada
   c. Atribui confiança: Alto (EAN) / Médio (>= 1 drug token) / Baixo (aproximado)
   d. Busca histórico → calcula menor, média, maior preço
   e. Busca equivalentes por princípio ativo (mesma categoria farmacêutica)
   f. Classifica: Ouro / Prata / Atenção / Descartável
   g. Gera recomendação textual determinística
5. Retorna JSON estruturado → Next.js renderiza resultado
6. Salva análise + itens no Supabase
```

### 4.6 Fluxo WhatsApp (Automático)
```
1. Fornecedor envia mensagem no grupo/chat do cliente
2. Uazapi dispara webhook → POST /api/whatsapp/webhook
3. Mensagem salva em `whatsapp_mensagens` com status "pendente"
4. pg_cron a cada 2h chama POST /api/whatsapp/cron-whatsapp (por empresa)
5. Mensagens pendentes agrupadas por chat_id
6. Texto concatenado → reutiliza _executar_e_persistir do fluxo principal
7. Resultado salvo em `analises_oferta` + mensagens marcadas "analisada"
8. Notificações disparadas: in-app, email (Resend), WhatsApp (Uazapi)
```

### 4.7 O que o Agente NÃO Deve Fazer
- Não criar novos services sem antes verificar se já existe um equivalente.
- Não alterar a estrutura de resposta do `analysis_engine.py` sem garantir compatibilidade com o frontend.
- Não remover RLS de nenhuma tabela.
- Não usar queries diretas ao Supabase no frontend para dados sensíveis — sempre via Route Handlers.
- Não ignorar o Design System — toda nova UI deve usar os tokens definidos.
- Não quebrar o fluxo de deduplicação do WhatsApp (constraint `instancia_id,message_id`).

---

## 5. Arquivos de Referência Importantes

| Arquivo | Descrição |
|---|---|
| `AGENTS.md` | Diretrizes originais para agentes (visão geral, stack, regras de negócio) |
| `design system.md` | Design System completo v2 com tokens, componentes e telas |
| `consolidacao_chats_1_a_5.md` | Regras de negócio extraídas dos 5 primeiros chats com o cliente |
| `doc_dump.txt` | PRD original com requisitos funcionais e backlog |
| `.env.example` | Template de variáveis de ambiente |
| `CONTEXTO_DETALHADO.md` | Contexto técnico exaustivo de todo o projeto |

---

## 6. Comandos Úteis

```bash
# Rodar tudo (frontend + backend)
npm run dev

# Apenas frontend
npm run dev:web

# Apenas backend
npm run dev:api

# Build frontend
npm run build:web

# Instalar deps Python
cd python-api && pip install -r requirements.txt
```

---

> **Nota final**: este documento deve ser atualizado a cada nova feature relevante. Qualquer agente de IA que atue no projeto deve ler este arquivo E o `CONTEXTO_DETALHADO.md` antes de iniciar qualquer trabalho.
