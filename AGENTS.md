# AGENTS.md — Compras PRO

## Visão Geral
App mobile-first de inteligência de compras para farmácias. O usuário recebe ofertas de fornecedores (WhatsApp, Excel, imagem, texto) e o sistema cruza automaticamente com histórico de preços, estoque e equivalentes — entregando uma decisão clara de compra.

---

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 14 (App Router) + TypeScript + shadcn/ui + Tailwind CSS |
| Backend IA | Python 3.11 + FastAPI + Agno (agentes) |
| Banco de dados | Supabase (PostgreSQL + Auth + Storage + RLS) |
| Deploy | Vercel (frontend) + Railway ou Render (FastAPI) |
| IA | Claude (Anthropic) via Agno Agent com tool calling |

---

## Estrutura de Pastas

```
compras-pro/
├── app/                        # Next.js App Router
│   ├── (auth)/                 # Login, cadastro
│   ├── (dashboard)/            # Telas autenticadas
│   │   ├── page.tsx            # Home
│   │   ├── nova-oferta/
│   │   ├── resultado/[id]/
│   │   ├── historico/
│   │   ├── produtos/
│   │   └── configuracoes/
│   └── api/                    # Route handlers Next.js (proxy para FastAPI)
├── components/
│   ├── ui/                     # shadcn/ui (não editar manualmente)
│   └── app/                    # Componentes do domínio
├── lib/
│   ├── supabase/               # Client, server, types
│   └── utils.ts
├── python-api/                 # FastAPI separado
│   ├── main.py
│   ├── routers/
│   │   ├── ofertas.py          # Extração e análise de ofertas
│   │   ├── importacao.py       # Upload CSV/Excel
│   │   └── produtos.py         # Consultas de estoque/histórico
│   ├── services/
│   │   ├── claude_service.py   # Integração Claude API
│   │   ├── matching_service.py # Match EAN + heurística
│   │   └── preco_service.py    # Cálculo histórico e classificação
│   └── requirements.txt
└── supabase/
    └── migrations/             # SQL de schema e RLS
```

---

## Banco de Dados (Supabase)

### Tabelas principais

```sql
-- Empresas (multiempresa)
empresas (id, nome, cnpj, created_at)

-- Produtos cadastrados por empresa
produtos (id, empresa_id, ean, descricao, principio_ativo, fabricante, grupo, curva_abc)

-- Estoque atual (fonte de verdade = coluna estoque)
estoque (id, empresa_id, produto_id, estoque, demanda_mes, custo_medio, preco_venda, dt_ult_entrada, dt_ult_venda)

-- Histórico de entradas (base para preço histórico)
entradas (id, empresa_id, produto_id, fornecedor, data_entrada, qtd_unitaria, valor_total_item, preco_unitario GENERATED AS (valor_total_item / qtd_unitaria))

-- Análises de oferta
analises (id, empresa_id, fornecedor_detectado, origem, status, created_at)

-- Itens de cada análise
analise_itens (id, analise_id, produto_id, preco_oferta, classificacao, confianca_match, recomendacao, dados_json)
```

### RLS obrigatório
Toda tabela com `empresa_id` deve ter RLS ativo. O `empresa_id` é extraído do JWT do usuário autenticado via Supabase Auth.

---

## Regras de Negócio Críticas

### Preço histórico unitário
```
preco_unitario = valor_total_item / qtd_unitaria
```
Nunca usar preço de tabela ou custo médio como histórico. Sempre calcular a partir das entradas.

### Classificação de oportunidade
| Classificação | Condição |
|---|---|
| 🥇 Ouro | `preco_oferta <= menor_historico * 0.80` (≥20% desconto) |
| 🥈 Prata | `preco_oferta <= menor_historico * 0.99` (1–19,9% desconto) |
| ⚠️ Atenção | Preço bom, mas há estoque de equivalente suficiente |
| ❌ Descartável | `preco_oferta > media_historica` |

### Equivalência de produtos
Match por `principio_ativo` + forma farmacêutica + concentração. Se houver estoque de equivalente, classificar como **Atenção** mesmo com preço bom.

### Sugestão de pedido
```
sugestao_pedido = max(0, (demanda_mes * 3) - estoque_atual)
```

### Normalização de laboratórios
O Python deve resolver siglas antes de qualquer comparação:
`NQ → Neoquímica`, `MDL → Medley`, `EMS → EMS`, `PD → Prati-Donaduzzi`, etc.

---

## Fluxo Principal (Análise de Oferta)

```
1. Usuário cola texto / faz upload (Next.js)
2. Next.js → POST /api/ofertas/analisar (FastAPI e Agno)
3. FastAPI e Agno → Claude API: extrai itens, preços, fornecedor
4. Para cada item:
   a. Busca EAN exato no Supabase
   b. Se não achar: heurística por descrição normalizada
   c. Atribui confiança: Alto (EAN) / Médio (descrição) / Baixo (aproximado)
   d. Busca histórico de entradas → calcula menor, média, 2 menores, 2 maiores
   e. Busca equivalentes por principio_ativo
   f. Classifica: Ouro / Prata / Atenção / Descartável
5. Retorna JSON estruturado → Next.js renderiza resultado
6. Salva análise no Supabase
```

---

## Convenções de Código

- **TypeScript strict** em todo o frontend. Sem `any`.
- **shadcn/ui** para todos os componentes base. Não criar UI do zero se houver componente shadcn equivalente.
- **Server Components** por padrão no Next.js. Usar `"use client"` apenas quando necessário (interatividade, hooks).
- **Supabase client**: usar `createServerClient` em Server Components/Route Handlers e `createBrowserClient` em Client Components.
- **FastAPI**: um router por domínio. Validação com Pydantic em todos os endpoints.
- **Variáveis de ambiente**: nunca hardcodar chaves. Usar `.env.local` (Next.js) e `.env` (FastAPI).

### Variáveis de ambiente obrigatórias
```env
# Next.js
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
PYTHON_API_URL=

# FastAPI
ANTHROPIC_API_KEY=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

---

## Design System (resumo)

- **Fonte**: Inter
- **Cores principais**: `#0F172A` (texto), `#1E40AF` (ação), `#F1F5F9` (fundo)
- **Status**: `#16A34A` verde (Ouro/Comprar) · `#D97706` amarelo (Prata/Atenção) · `#DC2626` vermelho (Descartável)
- **Componentes**: cards com `rounded-xl`, `shadow-sm`, borda esquerda colorida por status
- **Decisão antes de dados**: mostrar recomendação no topo do card, dados de suporte abaixo

> Consultar `design-system-compras-pro.md` para tokens completos.

---

## O que o agente NÃO deve fazer

- Não criar lógica de preço histórico no frontend — sempre via FastAPI
- Não usar `estoque` de nenhuma fonte que não seja a tabela `estoque` do Supabase
- Não comparar produtos apenas por nome — sempre priorizar EAN
- Não expor dados de uma empresa para outra — RLS é inegociável
- Não usar `demanda_diaria` nas interfaces — apenas `demanda_mes`