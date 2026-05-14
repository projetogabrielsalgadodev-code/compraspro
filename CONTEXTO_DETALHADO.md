# CONTEXTO DETALHADO — ComprasPRO

> Compilação técnica exaustiva do projeto. Última atualização: Maio/2026.

---

## 1. Propósito da Plataforma

**ComprasPRO** resolve o problema de **ineficiência na análise de ofertas farmacêuticas**. O cliente (Rede Inova — +700 lojas) recebe 400–500 mensagens/dia de fornecedores via WhatsApp. Analisar manualmente cada oferta contra estoque e histórico é impossível em escala, causando perda de oportunidades e compras desnecessárias.

**O que a plataforma entrega:**
- Análise automática de ofertas (texto, Excel, imagem, WhatsApp)
- Classificação de oportunidade: Ouro / Prata / Atenção / Descartável
- Cruzamento com histórico de preços e estoque atual
- Detecção de equivalentes por princípio ativo
- Sugestão de pedido baseada em demanda e estoque
- Notificações multicanal (in-app, email, WhatsApp)
- Dashboard analítico premium com modo escuro/claro

---

## 2. Arquitetura Geral

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Next.js 14    │────▶│  FastAPI/Python   │────▶│    Supabase     │
│  (App Router)   │     │  (Motor de IA)   │     │  (PostgreSQL)   │
│  Vercel Deploy  │     │  Railway/Render   │     │  Auth + RLS     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │                         │
                        ┌─────┴─────┐              ┌────┴────┐
                        │ Claude AI │              │ Uazapi  │
                        │ Anthropic │              │WhatsApp │
                        └───────────┘              └─────────┘
```

### Monorepo Structure
```
compras-pro/
├── package.json              # Monorepo root (npm workspaces)
├── apps/
│   └── web/                  # Next.js 14 App (frontend)
│       ├── app/
│       │   ├── (dashboard)/  # Telas autenticadas
│       │   │   ├── home/
│       │   │   ├── nova-analise/
│       │   │   ├── processando/
│       │   │   ├── revisao/
│       │   │   ├── resultado/
│       │   │   ├── item/
│       │   │   ├── historico/
│       │   │   ├── produtos/
│       │   │   ├── configuracoes/
│       │   │   └── dashboard/
│       │   ├── auth/           # Login, cadastro
│       │   ├── admin/          # Painel administrativo
│       │   └── api/            # Route Handlers (proxy)
│       │       ├── ofertas/
│       │       ├── produtos/
│       │       ├── whatsapp/
│       │       ├── webhooks/
│       │       ├── configuracoes/
│       │       └── auth/
│       ├── components/
│       │   ├── ui/             # shadcn/ui (não editar manualmente)
│       │   └── app/            # Componentes do domínio
│       ├── hooks/
│       ├── lib/
│       │   └── supabase/       # Clients (server + browser)
│       ├── types/
│       └── email-templates/
├── python-api/               # FastAPI (backend IA)
│   ├── app/
│   │   ├── main.py           # Entry point FastAPI
│   │   ├── routers/
│   │   │   ├── ofertas.py        # Análise de ofertas (sync + async)
│   │   │   ├── whatsapp.py       # Integração WhatsApp + Cron + Webhook
│   │   │   ├── produtos.py       # Consultas de estoque/histórico
│   │   │   ├── importacoes.py    # Upload CSV/Excel
│   │   │   └── configuracoes.py  # Regras de compra
│   │   ├── services/
│   │   │   ├── analysis_engine.py      # Motor determinístico (core)
│   │   │   ├── offer_extractor.py      # Extração via Claude + regex
│   │   │   ├── file_parser.py          # Parser Excel/CSV
│   │   │   ├── agno_agent.py           # Orquestrador Agno
│   │   │   ├── persistencia_service.py # Persistência no Supabase
│   │   │   ├── importacao_service.py   # Serviço de importação
│   │   │   ├── lab_normalizer.py       # Normalização de laboratórios
│   │   │   └── chat_context_service.py # Contexto de chat
│   │   ├── db/
│   │   │   └── supabase_client.py      # Client Supabase + Settings
│   │   ├── middleware/
│   │   │   └── auth.py                 # JWT validation
│   │   └── models/
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
├── supabase/
│   └── migrations/           # SQL de schema e RLS
├── AGENTS.md
├── INSTRUCOES.md
├── CONTEXTO_DETALHADO.md
├── design system.md
├── consolidacao_chats_1_a_5.md
├── doc_dump.txt
└── .env.example
```

---

## 3. Stack Técnica Detalhada

### 3.1 Frontend (Next.js 14)
- **Framework**: Next.js 14 com App Router
- **Linguagem**: TypeScript strict (sem `any`)
- **UI**: shadcn/ui + Tailwind CSS
- **Fonte**: Inter (Google Fonts)
- **Auth**: Supabase Auth via middleware.ts
- **State**: Server Components por padrão, `"use client"` quando necessário
- **Deploy**: Vercel

### 3.2 Backend (Python/FastAPI)
- **Framework**: FastAPI 0.2.0
- **Python**: 3.11+
- **IA**: Agno framework + Anthropic Claude API
- **Validação**: Pydantic v2
- **HTTP Client**: httpx (async)
- **Parsing**: openpyxl + pandas (Excel/CSV)
- **Deploy**: Railway ou Render

**Dependências principais** (`requirements.txt`):
```
agno>=1.4.4, anthropic>=0.46.0, fastapi>=0.135.0, httpx>=0.28.1
openpyxl>=3.1.5, pandas>=2.2.3, pydantic>=2.10.6
supabase>=2.15.0, resend>=2.0.0, uvicorn>=0.34.0
```

### 3.3 Banco de Dados (Supabase/PostgreSQL)

#### Tabelas Principais
```sql
-- Multiempresa
empresas (id, nome, cnpj, notificacao_email, notificacao_whatsapp,
          notificacoes_ativas, created_at)

-- Produtos cadastrados
produtos (id, empresa_id, ean, descricao, principio_ativo, fabricante,
          grupo, curva_abc, demanda_mes, estoque)

-- Estoque atual
estoque (id, empresa_id, produto_id, estoque, demanda_mes, custo_medio,
         preco_venda, dt_ult_entrada, dt_ult_venda)

-- Histórico de entradas
entradas (id, empresa_id, produto_id, fornecedor, data_entrada,
          qtd_unitaria, valor_total_item,
          preco_unitario GENERATED AS (valor_total_item / qtd_unitaria))

-- Análises de oferta
analises_oferta (id, empresa_id, usuario_id, origem, entrada_bruta,
                 status, resultado_json, fornecedor_detectado, created_at)

-- Itens de cada análise
analise_itens (id, analise_id, produto_id, preco_oferta, classificacao,
               confianca_match, recomendacao, dados_json)

-- WhatsApp
whatsapp_instancias (id, empresa_id, instance_id, api_token, status,
                     numero_telefone, nome_instancia, created_at, updated_at)

whatsapp_mensagens (id, empresa_id, instancia_id, message_id, chat_id,
                    chat_name, sender_id, sender_name, sender_phone,
                    is_group, tipo_mensagem, conteudo_texto, media_url,
                    timestamp_msg, status_analise, analise_id, raw_payload)
                    -- UNIQUE(instancia_id, message_id) para deduplicação

-- Notificações
notificacoes (id, empresa_id, tipo, titulo, mensagem, link, metadata,
              lida, created_at)
```

#### RLS (Row Level Security)
Toda tabela com `empresa_id` tem RLS ativo. O `empresa_id` é extraído do JWT do usuário autenticado.

---

## 4. Módulos do Backend (Detalhes)

### 4.1 `analysis_engine.py` — Motor Determinístico (Core)
**Responsabilidade**: todos os cálculos de análise — ZERO dependência de LLM.

- `calcular_variacao_percentual()`: `((menor_hist - preco_oferta) / menor_hist) × 100`
- `classificar_oferta()`: Ouro/Prata/Atenção/Descartável
- `calcular_sugestao_pedido()`: `max(0, demanda_mes × 3 - estoque)`
- `gerar_recomendacao()`: texto determinístico com dados reais
- `_match_item_no_arquivo()`: weighted token scoring (drug tokens peso 5, genéricos peso 1)
- `buscar_equivalentes()`: match por princípio ativo + filtro de categoria farmacêutica
- `construir_indice_arquivo()` / `construir_indice_banco()`: índices invertidos de tokens

**Mecanismos de qualidade**:
- Primary tokens check (todas as moléculas devem estar no candidato)
- Dosage matching (boost/penalidade por dosagem)
- Filtro de categoria farmacêutica (não mistura sólido com líquido)
- Salt prefix exclusion (`dicloridrato`, `fumarato`, etc.)
- Prefix-aware lookup (`amox` → `amoxicilina`)

### 4.2 `offer_extractor.py` — Extração de Itens
- Extração de itens da oferta via Claude API (Anthropic)
- Regex fallback para formatos conhecidos
- Multiplicador inteligente por categoria de produto
- Classificação de forma farmacêutica

### 4.3 `whatsapp.py` — Integração WhatsApp
**Endpoints**:
- `POST /cron-whatsapp`: chamado pelo pg_cron (protegido por X-Cron-Secret)
- `POST /webhook`: recebe mensagens da Uazapi em tempo real
- `POST /instancia/criar`: cria instância + QR Code (self-service)
- `GET /instancia/status`: polling de status + QR atualizado
- `GET /instancia`: consulta instância da empresa
- `POST /instancia/desconectar` / `POST /instancia/reconectar`

**Segurança**:
- `/cron-whatsapp`: X-Cron-Secret (server-to-server)
- `/webhook`: api_token da instância Uazapi (3 formas de auth)
- `/instancia/*`: JWT do usuário autenticado

**Notificações (3 canais)**:
1. In-app (tabela `notificacoes` + Supabase Realtime)
2. Email (Resend API)
3. WhatsApp (Uazapi — mensagem de texto formatada)

### 4.4 `ofertas.py` — Análise de Ofertas
- Análise síncrona e assíncrona
- `_executar_e_persistir()`: orquestrador reutilizado pelo cron WhatsApp
- Suporte a texto, Excel e arquivo
- Persistência em `analises_oferta` + `analise_itens`

### 4.5 `file_parser.py` — Parser de Arquivos
- Parse de Excel (.xlsx/.xls) e CSV
- Detecção automática de colunas (EAN, descrição, preço, quantidade)
- Cálculo de preço unitário com normalização

### 4.6 `persistencia_service.py` — Persistência
- `buscar_produtos()`: carrega todos os produtos de uma empresa
- `buscar_historico()`: carrega histórico de entradas agrupado por EAN

---

## 5. Regras de Negócio Críticas

### 5.1 Preço Histórico
```
preco_unitario = valor_total_item / qtd_unitaria
```
Nunca usar preço de tabela ou custo médio. Sempre calcular a partir das entradas.

### 5.2 Classificação de Oportunidade
| Classificação | Condição | Ícone |
|---|---|---|
| Ouro | `variação >= 20%` (desconto forte) | 🥇 |
| Prata | `5% <= variação < 20%` | 🥈 |
| Atenção | `0% <= variação < 5%` ou equivalente em estoque | ⚠️ |
| Descartável | `variação < 0%` (ágio) ou sem dados | ❌ |

### 5.3 Equivalência
Match por `princípio_ativo` + forma farmacêutica + concentração. Se houver estoque de equivalente, classificar como **Atenção** mesmo com preço bom.

### 5.4 Normalização de Laboratórios
`NQ → Neoquímica`, `MDL → Medley`, `EMS → EMS`, `PD → Prati-Donaduzzi`, etc.

---

## 6. Frontend — Telas e Rotas

| Rota | Descrição |
|---|---|
| `/` | Landing page / redirect para login |
| `/auth` | Login e cadastro (Supabase Auth) |
| `/(dashboard)/home` | Home com saudação, campo de nova oferta, atalhos e resumos |
| `/(dashboard)/nova-analise` | Formulário de nova análise (texto, upload, WhatsApp) |
| `/(dashboard)/processando` | Tela de progresso da análise |
| `/(dashboard)/revisao` | Revisão dos itens extraídos (confiança do match) |
| `/(dashboard)/resultado` | Resultado com cards classificados + filtros |
| `/(dashboard)/item` | Detalhe do item (histórico, equivalentes, decisão) |
| `/(dashboard)/historico` | Lista de análises anteriores |
| `/(dashboard)/produtos` | Catálogo de produtos com busca |
| `/(dashboard)/configuracoes` | Regras de compra e preferências |
| `/(dashboard)/dashboard` | Dashboard analítico premium |
| `/admin` | Painel administrativo |

---

## 7. Design System (Resumo)

- **Fonte**: Inter (Google Fonts)
- **Temas**: modo escuro (hero) e modo claro (tradução premium)
- **Cores escuro**: `bg-app: #090B10`, `accent: #2F6BFF`, `text: #F5F7FB`
- **Cores claro**: `bg-app: #F5F7FB`, `accent: #245BFF`, `text: #0B1220`
- **Status**: verde (`#16A34A` = Ouro), âmbar (`#D97706` = Prata/Atenção), vermelho (`#DC2626` = Descartável)
- **Cards**: `rounded-xl`, `shadow-sm`, borda esquerda colorida por status
- **Princípio**: "Decisão antes de dados" — recomendação no topo, dados abaixo

> Documento completo: `design system.md`

---

## 8. API Routes (Next.js → FastAPI)

| Next.js Route | FastAPI Endpoint | Descrição |
|---|---|---|
| `/api/ofertas/*` | `/api/ofertas/*` | Análise de ofertas |
| `/api/produtos/*` | `/api/produtos/*` | Consulta de produtos |
| `/api/whatsapp/*` | `/api/whatsapp/*` | Integração WhatsApp |
| `/api/configuracoes/*` | `/api/configuracoes/*` | Configurações |
| `/api/webhooks/*` | `/api/whatsapp/webhook` | Webhooks externos |
| `/api/auth/*` | — | Supabase Auth direto |

---

## 9. Visão e Roadmap

**Visão até aqui**: plataforma funcional que automatiza 100% do fluxo de análise de ofertas, desde o recebimento via WhatsApp até a recomendação de compra com notificação automática.

**Próximos passos potenciais**:
- Expansão para múltiplas redes de farmácias
- Análise de sazonalidade com dados de vendas diárias
- Exportação de lista de compras em .docx
- App mobile nativo
- Dashboard de economia acumulada
- Integração com ERPs farmacêuticos

---

> **Este documento é a fonte de verdade técnica do projeto. Atualize-o sempre que novas features forem implementadas.**
