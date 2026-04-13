# Design System — Compras PRO
> Versão 2.0 | Plataforma de Inteligência de Compras para Farmácias

---

## Visão Geral do App

**Compras PRO** é uma ferramenta de inteligência comercial mobile-first para gestores de farmácias. O app recebe ofertas de fornecedores (WhatsApp, Excel, imagem, texto) e cruza automaticamente com histórico de preços, estoque atual e equivalentes — entregando uma decisão clara: **comprar, aguardar ou descartar**.

### Princípios de Design
- **O sistema terá modo escuro e modo claro como capacidade nativa do shell**
- **Decisão antes de dados**: o usuário vê primeiro a recomendação, depois os números
- **Clareza executiva**: interface limpa, analítica e de alta densidade visual sem parecer fria
- **Mobile-first com shell desktop premium**: no celular o fluxo continua direto; no desktop o produto ganha navegação lateral, painéis amplos e filtros persistentes
- **Hierarquia de status**: verde = oportunidade, âmbar = atenção, vermelho = descartável
- **Atmosfera visual**: superfícies escuras ou claras com gradientes sutis azulados, brilho discreto em CTAs e bordas com baixo contraste

### Direção Visual de Referência
- Sidebar escura e compacta, com branding no topo e navegação em pills
- Área principal com hero administrativo, overline discreta e títulos grandes
- Cards analíticos largos, com gradiente suave horizontal e borda translúcida
- Campos de filtro com aparência “painel operacional”, não formulário genérico
- Botões primários com azul elétrico e leve glow; secundários com fundo translúcido
- Modo claro preserva a mesma estrutura, só troca contraste e profundidade

### Ajuste de Identidade Visual — Produto Final
- O visual deve parecer **software operacional premium**, não wireframe ou protótipo estático
- Linhas e bordas devem ser **semi-transparentes**; evitar contorno cinza duro e excessivamente visível
- A cor deve vir de **camadas de gradiente** e **glows controlados**, não apenas de blocos sólidos
- Toda tela principal deve ter ao menos um ponto de ornamentação visual: brilho radial, malha suave, faixa cromática ou superfície iridescente discreta
- O contraste deve ser alto o suficiente para leitura, mas com superfícies ricas e menos chapadas
- O modo escuro é o tema hero; o modo claro é sua tradução premium, não uma folha branca simples

### Linguagem de Superfície
- **Shell**: fundo com composição de gradientes frios azul/ciano/violeta e profundidade em camadas
- **Cards**: base escura ou clara com dois planos cromáticos, highlight superior e sombra longa suave
- **Bordas**: 1px translúcido com leve brilho interno
- **Inputs e filtros**: aparência de console operacional, com fundo mais denso e glow de foco colorido
- **CTA principal**: gradiente marcante azul-violeta, brilho externo controlado e texto branco sólido
- **Navegação ativa**: pill com preenchimento colorido translúcido e ícone dentro de cápsula destacada

---

## Paleta de Cores

### Tokens Semânticos de Tema

#### Modo Escuro
| Token | Valor | Uso |
|---|---|---|
| `bg-app` | `#090B10` | Fundo principal do shell |
| `bg-sidebar` | `#0F1218` | Sidebar e áreas laterais |
| `bg-card` | `rgba(20,24,32,0.84)` | Cards principais |
| `bg-card-strong` | `#151922` | Cards de dados densos |
| `bg-input` | `#11151D` | Campos e filtros |
| `text-primary` | `#F5F7FB` | Headings e valores |
| `text-secondary` | `#A7B0C2` | Descrições |
| `text-muted` | `#6F7A90` | Labels auxiliares |
| `border-soft` | `rgba(148,163,184,0.18)` | Bordas padrão |
| `accent-primary` | `#2F6BFF` | CTA principal |
| `accent-primary-glow` | `rgba(47,107,255,0.34)` | Glow do CTA |

#### Modo Claro
| Token | Valor | Uso |
|---|---|---|
| `bg-app` | `#F5F7FB` | Fundo principal do shell |
| `bg-sidebar` | `#FFFFFF` | Sidebar e áreas laterais |
| `bg-card` | `rgba(255,255,255,0.84)` | Cards principais |
| `bg-card-strong` | `#FFFFFF` | Cards densos |
| `bg-input` | `#F8FAFC` | Campos e filtros |
| `text-primary` | `#0B1220` | Headings e valores |
| `text-secondary` | `#536075` | Descrições |
| `text-muted` | `#7C879B` | Labels auxiliares |
| `border-soft` | `rgba(15,23,42,0.08)` | Bordas padrão |
| `accent-primary` | `#245BFF` | CTA principal |
| `accent-primary-glow` | `rgba(36,91,255,0.22)` | Glow do CTA |

### Regras de Aplicação dos Temas
- O shell deve usar variáveis CSS semânticas, não hexadecimais fixos dentro dos componentes
- Todos os componentes base devem ler `background`, `foreground`, `card`, `border`, `muted`, `primary`
- Gradientes decorativos devem ser suaves e sempre secundários ao conteúdo
- Nunca usar preto absoluto puro em cards; reservar preto apenas para profundidade do fundo

### Mapeamento de Tokens → Valores Reais

#### Texto
| Token | Valor | Uso |
|---|---|---|
| `text-primary` | `#0F172A` | Títulos, nomes de produtos, dados principais |
| `text-secondary` | `#475569` | Laboratório, apresentação, descrições de apoio |
| `text-muted` | `#94A3B8` | Placeholders, hints, datas, metadados |
| `text-on-dark` | `#F8FAFC` | Texto sobre fundos escuros (header, splash) |
| `text-on-brand` | `#FFFFFF` | Texto sobre botões primários e badges coloridos |

#### Superfícies
| Token | Valor | Uso |
|---|---|---|
| `surface-page` | `#F1F5F9` | Fundo principal de todas as telas |
| `surface-section` | `#E2E8F0` | Seções alternadas, separadores visuais |
| `surface-card` | `#FFFFFF` | Cards de produto, cards de análise, inputs |
| `surface-subtle` | `#F8FAFC` | Áreas de destaque leve, fundo de chips inativos |
| `surface-elevated` | `#FFFFFF` | Modais, bottom sheets, dropdowns |

#### Ações
| Token | Valor | Uso |
|---|---|---|
| `action-primary` | `#1E40AF` | Botões principais, links, ícones de ação |
| `action-primary-hover` | `#1D4ED8` | Hover de botões primários |
| `action-primary-active` | `#1E3A8A` | Estado pressed de botões primários |
| `action-secondary` | `#E2E8F0` | Botões secundários, chips inativos |
| `action-strong` | `#0F172A` | CTA principal ("Analisar agora"), botões de alta conversão |
| `action-strong-hover` | `#1E293B` | Hover do CTA principal |

#### Bordas
| Token | Valor | Uso |
|---|---|---|
| `border-default` | `#CBD5E1` | Bordas de inputs, cards, divisores |
| `border-subtle` | `#E2E8F0` | Bordas muito sutis, separadores internos de card |
| `border-focus` | `#1E40AF` | Focus ring em inputs e elementos interativos |

#### Status — Core do App
| Token | Valor | Uso |
|---|---|---|
| `status-success` | `#16A34A` | Oportunidade Ouro (≥20% desconto), "Comprar" |
| `status-warning` | `#D97706` | Oportunidade Prata, "Atenção", estoque de equivalente |
| `status-error` | `#DC2626` | Descartável, preço ruim, estoque crítico |

#### Tokens de Status Estendidos (específicos do domínio)
| Token | Valor | Uso |
|---|---|---|
| `status-success-surface` | `#DCFCE7` | Fundo de badge/card Ouro |
| `status-success-border` | `#86EFAC` | Borda de card Ouro |
| `status-warning-surface` | `#FEF3C7` | Fundo de badge/card Prata e Atenção |
| `status-warning-border` | `#FCD34D` | Borda de card Prata e Atenção |
| `status-error-surface` | `#FEE2E2` | Fundo de badge/card Descartável |
| `status-error-border` | `#FCA5A5` | Borda de card Descartável |
| `status-neutral-surface` | `#F1F5F9` | Fundo de badge neutro / "Revisar" |
| `status-neutral-border` | `#CBD5E1` | Borda de badge neutro |

---

## Tipografia

### Fonte
**Inter** (Google Fonts) — fonte principal em todo o app.

### Escala de Tamanhos
| Token | Valor | Uso no App |
|---|---|---|
| `text-xs` | 12px | Badges de confiança, labels de status, timestamps |
| `text-sm` | 14px | Laboratório, apresentação, texto secundário de cards |
| `text-base` | 16px | Corpo de texto, descrições, conteúdo de inputs |
| `text-lg` | 18px | Nome do produto no card expandido |
| `text-xl` | 20px | Subtítulos de seção, totais de resumo |
| `text-2xl` | 24px | Títulos de tela (ex: "Resultado da Análise") |
| `text-3xl` | 30px | Preço em destaque no card de oferta |
| `text-4xl` | 36px | Headline do splash, títulos hero |
| `text-5xl` | 48px | Logo/nome do app na tela splash |

### Pesos
| Token | Valor | Uso |
|---|---|---|
| `font-normal` | 400 | Texto de apoio, descrições, metadados |
| `font-medium` | 500 | Labels de campo, texto de chips, valores numéricos |
| `font-semibold` | 600 | Nome do produto, títulos de card, botões |
| `font-bold` | 700 | Preço em destaque, headline de decisão, nome do app |

---

## Espaçamento

| Token | Valor | Uso no App |
|---|---|---|
| `space-1` | 4px | Gap entre ícone e label inline |
| `space-2` | 8px | Gap entre badge e texto, espaço interno de chips |
| `space-3` | 12px | Gap entre linhas de dados dentro de um card |
| `space-4` | 16px | Padding horizontal padrão de tela, gap entre cards |
| `space-6` | 24px | Padding interno de cards, gap entre seções próximas |
| `space-8` | 32px | Gap entre seções distintas |
| `space-12` | 48px | Padding de seções de conteúdo |
| `space-16` | 64px | Padding vertical de seções grandes |
| `space-20` | 80px | Padding da tela splash, hero sections |

---

## Bordas e Sombras

### Border Radius
| Token | Valor | Uso |
|---|---|---|
| `radius-sm` | 6px | Inputs, badges de status, chips de filtro |
| `radius-md` | 8px | Botões, selects, tooltips |
| `radius-lg` | 12px | Cards compactos (resumo, atalhos) |
| `radius-xl` | 16px | Cards principais de produto/oferta |
| `radius-2xl` | 24px | Bottom sheets, modais, card hero da Home |
| `radius-full` | 9999px | Avatar de perfil, pills de confiança, indicadores circulares |

### Sombras
| Token | Valor CSS | Uso |
|---|---|---|
| `shadow-sm` | `0 1px 3px rgba(15,23,42,0.08)` | Inputs com foco, hover states sutis |
| `shadow-md` | `0 4px 12px rgba(15,23,42,0.10)` | Cards padrão, dropdowns |
| `shadow-lg` | `0 8px 24px rgba(15,23,42,0.14)` | Modais, bottom sheets, popovers |
| `shadow-card` | `0 2px 8px rgba(15,23,42,0.08)` | Cards de produto em estado default |
| `shadow-card-hover` | `0 6px 20px rgba(15,23,42,0.14)` | Cards de produto em hover/expanded |
| `shadow-button-primary` | `0 4px 12px rgba(30,64,175,0.30)` | Botão primário (azul com glow) |

---

## Componentes

### 1. Botões

#### Primary
```
bg: action-primary
text: text-on-brand (font-semibold, text-base)
radius: radius-md
shadow: shadow-button-primary
padding: space-3 (vertical) × space-6 (horizontal)
```
**Estados:**
- `default`: bg `action-primary`
- `hover`: bg `action-primary-hover`, shadow levemente maior
- `active`: bg `action-primary-active`, shadow reduzido
- `focus`: ring 2px `border-focus` com offset 2px
- `disabled`: opacity 40%, cursor `not-allowed`

#### Strong (CTA Principal — "Analisar agora")
```
bg: action-strong
text: text-on-dark (font-bold, text-lg)
radius: radius-md
shadow: shadow-lg
padding: space-4 (vertical) × space-8 (horizontal)
width: 100% (mobile)
```
**Estados:**
- `default`: bg `action-strong`
- `hover`: bg `action-strong-hover`
- `active`: scale 0.98, shadow reduzido
- `focus`: ring 2px `border-focus`
- `disabled`: opacity 40%, cursor `not-allowed`

#### Secondary
```
bg: surface-card
text: text-primary (font-medium, text-base)
border: 1px border-default
radius: radius-md
padding: space-3 × space-4
```
**Estados:**
- `default`: bg `surface-card`, border `border-default`
- `hover`: bg `surface-section`, border `border-default`
- `active`: bg `surface-section`, shadow-sm
- `focus`: ring 2px `border-focus`
- `disabled`: opacity 40%, cursor `not-allowed`

---

### 2. Cards

#### Card de Produto / Oferta (fechado)
```
bg: surface-card
radius: radius-xl
shadow: shadow-card
padding: space-6
border-left: 4px solid [token de status correspondente]
```
**Estrutura interna:**
- Linha 1: `[Badge de status]` + `[Nome do produto]` (text-base, font-semibold, text-primary)
- Linha 2: Laboratório + Apresentação (text-sm, font-normal, text-secondary)
- Linha 3: `Preço oferta` (text-2xl, font-bold, text-primary) + `Var%` (text-sm, colorido por status)
- Linha 4: `[Chip: Comprar / Não comprar / Revisar]`

**Estados:**
- `default`: shadow `shadow-card`
- `hover/expanded`: shadow `shadow-card-hover`, border-left mais espessa (6px)
- `focus`: ring 2px `border-focus`

#### Card de Produto (expandido)
```
bg: surface-card
radius: radius-xl
shadow: shadow-card-hover
padding: space-6
```
**Seções internas (separadas por border-subtle):**
1. **Dados da oferta**: Preço oferta, fornecedor, data
2. **Histórico do item**: Menor histórico (`=` ou `≠`), Var%, 2 menores e 2 maiores preços
3. **Estoque e demanda**: Estoque atual, Demanda mês, Sugestão de pedido, Cobertura em dias
4. **Equivalentes**: Lista de equivalentes com estoque e laboratório
5. **Decisão**: Frase curta de recomendação + ações (Comprar / Aguardar / Descartar)

#### Card de Resumo (Home — métricas)
```
bg: surface-card
radius: radius-lg
shadow: shadow-card
padding: space-4
```
**Estrutura:**
- Ícone (24px) + Label (text-sm, text-secondary)
- Valor numérico (text-2xl, font-bold, text-primary)

#### Card Analítico Premium (dashboard desktop)
```
bg: gradiente suave sobre bg-card
radius: radius-2xl
border: 1px solid border-soft
shadow: 0 10px 30px rgba(0,0,0,0.20) no dark | 0 10px 25px rgba(15,23,42,0.08) no light
padding: space-6 ou space-8
```
**Estrutura:**
- Overline em caixa alta com tracking amplo
- Métrica principal grande
- Texto contextual curto abaixo
- Brilho radial sutil no canto direito

---

### 3. Inputs

#### Campo de texto padrão
```
bg: surface-card
border: 1px border-default
radius: radius-sm
padding: space-3 × space-4
text: text-base, font-normal, text-primary
placeholder: text-muted
```
**Estados:**
- `default`: border `border-default`
- `hover`: border `border-default`, shadow-sm
- `dark`: usar `bg-input`, borda translúcida e texto `text-primary`

### 3.1 Filtros Administrativos
- Campos devem parecer módulos de operação, com borda interna, fundo levemente contrastado e labels pequenas acima do valor
- Em desktop, filtros devem viver dentro de um painel horizontal contínuo
- Botões `Filtrar` e `Limpar` devem encerrar o bloco de filtros como ações bem visíveis

---

## Shell de Navegação

### Sidebar
- Largura desktop: `272px`
- Branding fixo no topo com selo do produto
- Grupo de navegação com label `Menu`
- Item ativo: pill preenchida com contraste sutil e ícone destacado
- Rodapé opcional com status da empresa/ambiente

### Header de Conteúdo
- Deve ficar acima do conteúdo principal, não dentro da sidebar
- Conter overline da área, título, descrição e ações rápidas à direita
- Incluir toggle de tema sempre disponível

### Fundo da Aplicação
- Usar composição de gradientes radiais e lineares discretos
- Evitar fundo chapado tanto no modo claro quanto no escuro
- O conteúdo deve flutuar visualmente sobre o shell, sem perder contraste
- `focus`: border `border-focus`, ring 2px `border-focus` com opacity 20%, shadow-sm
- `error`: border `status-error`, texto de erro em `status-error` (text-sm)
- `disabled`: bg `surface-section`, opacity 60%, cursor `not-allowed`

#### Área de texto grande (colar oferta)
```
bg: surface-card
border: 2px dashed border-default
radius: radius-xl
padding: space-6
min-height: 160px
text: text-base, text-primary
placeholder: text-muted, text-center
```
**Estados:**
- `default`: border dashed `border-default`
- `focus/drag-over`: border sólida `border-focus`, bg `surface-subtle`
- `filled`: border sólida `border-default`

---

### 4. Badges de Status (Classificação de Oportunidade)

#### Ouro (≥ 20% de desconto)
```
bg: status-success-surface
text: status-success (text-xs, font-semibold)
border: 1px status-success-border
radius: radius-full
padding: space-1 × space-2
```
Label: `🥇 Ouro`

#### Prata (1% a 19,9% de desconto)
```
bg: status-warning-surface
text: status-warning (text-xs, font-semibold)
border: 1px status-warning-border
radius: radius-full
padding: space-1 × space-2
```
Label: `🥈 Prata`

#### Atenção (preço bom, mas tem equivalente em estoque)
```
bg: status-warning-surface
text: status-warning (text-xs, font-semibold)
border: 1px status-warning-border
radius: radius-full
padding: space-1 × space-2
```
Label: `⚠️ Atenção`

#### Descartável (preço acima da média histórica)
```
bg: status-error-surface
text: status-error (text-xs, font-semibold)
border: 1px status-error-border
radius: radius-full
padding: space-1 × space-2
```
Label: `❌ Descartável`

---

### 5. Badges de Confiança do Match

| Nível | bg | text | label |
|---|---|---|---|
| Alto | `status-success-surface` | `status-success` | `🟢 Alto` |
| Médio | `status-warning-surface` | `status-warning` | `🟡 Médio` |
| Baixo | `status-error-surface` | `status-error` | `🔴 Baixo` |

```
radius: radius-full
padding: space-1 × space-2
text: text-xs, font-medium
```

---

### 6. Chips de Filtro

#### Inativo
```
bg: surface-subtle
text: text-secondary (text-sm, font-medium)
border: 1px border-default
radius: radius-full
padding: space-2 × space-4
```

#### Ativo
```
bg: action-primary
text: text-on-brand (text-sm, font-semibold)
border: none
radius: radius-full
padding: space-2 × space-4
shadow: shadow-sm
```

**Estados:**
- `default (inativo)`: conforme acima
- `hover (inativo)`: bg `surface-section`
- `active/selected`: conforme "Ativo"
- `focus`: ring 2px `border-focus`

---

### 7. Barra de Navegação Inferior (Bottom Nav)

```
bg: surface-elevated
border-top: 1px border-subtle
shadow: shadow-lg (invertido, para cima)
padding: space-2 (vertical) × space-4 (horizontal)
height: 64px
```

**Item inativo:**
- Ícone: 24px, cor `text-muted`
- Label: text-xs, font-medium, `text-muted`

**Item ativo:**
- Ícone: 24px, cor `action-primary`
- Label: text-xs, font-semibold, `action-primary`
- Indicador: dot 4px `action-primary` abaixo do ícone

---

### 8. Header de Tela

```
bg: action-strong
padding: space-4 (horizontal) × space-6 (vertical)
text título: text-xl, font-semibold, text-on-dark
```

**Variante Home (com saudação):**
- Saudação: text-sm, font-normal, text-on-dark (opacity 70%)
- Nome: text-xl, font-bold, text-on-dark
- Ícones de ação (notificação, perfil): 24px, text-on-dark

---

### 9. Indicador de Progresso (Tela de Processamento)

```
bg track: surface-section
bg fill: action-primary
radius: radius-full
height: 6px
```

**Etapas visuais:**
- Ícone de etapa concluída: `status-success` (checkmark)
- Ícone de etapa atual: `action-primary` (spinner)
- Ícone de etapa pendente: `text-muted` (círculo vazio)
- Texto de etapa: text-sm, font-medium, `text-secondary`

---

### 10. Linha de Dado (dentro de card expandido)

```
layout: flex, justify-between
padding: space-3 (vertical)
border-bottom: 1px border-subtle (exceto último)
```

- Label: text-sm, font-normal, `text-secondary`
- Valor: text-sm, font-semibold, `text-primary`
- Valor com status positivo: `status-success`
- Valor com status negativo: `status-error`
- Valor com status de atenção: `status-warning`

---

## Telas e Aplicação dos Tokens

### Tela Splash
- bg: `action-strong`
- Logo: `text-on-dark`, text-5xl, font-bold
- Subtítulo: `text-on-dark` (opacity 70%), text-lg, font-normal
- Padding: `space-20`

### Tela Home
- bg: `surface-page`
- Header: `action-strong`, padding `space-6`
- Card "Nova Oferta": `surface-card`, radius `radius-2xl`, shadow `shadow-md`, padding `space-6`
- Área de input: borda dashed `border-default`, radius `radius-xl`
- Botão "Analisar agora": Strong CTA, width 100%
- Cards de atalho: `surface-card`, radius `radius-lg`, shadow `shadow-card`, padding `space-4`
- Cards de resumo (métricas): `surface-card`, radius `radius-lg`, shadow `shadow-card`
- Seção "Últimas análises": bg `surface-page`, gap `space-4`

### Tela Nova Oferta
- bg: `surface-page`
- Seletor de origem: chips de filtro (Inativo/Ativo)
- Área de colar: input grande com borda dashed
- Opções avançadas: toggle switches com `action-primary`
- Botão fixo no rodapé: Strong CTA, shadow `shadow-lg`

### Tela de Processamento
- bg: `surface-page`
- Indicador de progresso: conforme componente acima
- Texto principal: text-2xl, font-bold, `text-primary`
- Etapas: lista vertical com ícones de status

### Tela Revisão da Leitura
- bg: `surface-page`
- Chips de filtro: Todos / Encontrados / Baixa confiança / Não encontrados
- Cards de item: `surface-card`, radius `radius-xl`, shadow `shadow-card`
  - Badge de confiança: componente de confiança (Alto/Médio/Baixo)
  - Texto original: text-sm, `text-secondary`
  - Match sugerido: text-base, font-semibold, `text-primary`
- Botão fixo: Strong CTA

### Tela Resultado da Análise
- bg: `surface-page`
- Header com fornecedor: `action-strong`
- Cards de resumo (4 métricas): `surface-card`, radius `radius-lg`
- Chips de filtro: Todos / Comprar / Não comprar / Revisar
- Cards de oferta: conforme componente Card de Produto
  - Borda esquerda colorida por status (Ouro = `status-success`, Prata/Atenção = `status-warning`, Descartável = `status-error`)

### Tela Detalhe do Item
- bg: `surface-page`
- Bloco de decisão: bg colorido por status, radius `radius-2xl`, padding `space-6`
- Seções de dados: cards `surface-card`, radius `radius-xl`, shadow `shadow-card`
- Gráfico de histórico: linha `action-primary`, fundo `surface-subtle`
- Botões de ação: Primary (Comprar agora) + Secondary (Aguardar / Revisar)

### Tela Histórico
- bg: `surface-page`
- Barra de busca: input padrão, radius `radius-md`
- Chips de filtro: data, fornecedor, origem, status
- Cards de análise: `surface-card`, radius `radius-lg`, shadow `shadow-card`

### Tela Produtos
- bg: `surface-page`
- Barra de busca: input grande, radius `radius-md`, shadow `shadow-sm`
- Chips de filtro: princípio ativo, laboratório, apresentação
- Cards de produto: `surface-card`, radius `radius-lg`, shadow `shadow-card`

### Tela Configurações
- bg: `surface-page`
- Seções: `surface-card`, radius `radius-xl`, shadow `shadow-card`, padding `space-6`
- Inputs numéricos: padrão com `border-default`
- Toggles: `action-primary` quando ativo, `surface-section` quando inativo
- Labels: text-base, font-medium, `text-primary`
- Descrições: text-sm, font-normal, `text-secondary`

---

## Regras de Uso dos Tokens de Status no Domínio

### Classificação de Oportunidade → Token de Status
| Classificação | Border-left card | Badge bg | Badge text | Ícone |
|---|---|---|---|---|
| Ouro (≥20% desc.) | `status-success` | `status-success-surface` | `status-success` | 🥇 |
| Prata (1–19,9%) | `status-warning` | `status-warning-surface` | `status-warning` | 🥈 |
| Atenção (equiv. em estoque) | `status-warning` | `status-warning-surface` | `status-warning` | ⚠️ |
| Descartável (preço ruim) | `status-error` | `status-error-surface` | `status-error` | ❌ |

### Variação de Preço (Var%) → Cor do Valor
| Situação | Token de cor |
|---|---|
| Desconto (preço abaixo do histórico) | `status-success` |
| Ágio pequeno (até 10% acima) | `status-warning` |
| Ágio alto (>10% acima) | `status-error` |
| Neutro / sem histórico | `text-muted` |

### Cobertura de Estoque → Cor do Valor
| Situação | Token de cor |
|---|---|
| > 90 dias | `status-success` |
| 30–90 dias | `status-warning` |
| < 30 dias | `status-error` |
| Zerado / negativo | `status-error` (bold) |

---

## Estados Obrigatórios (Checklist)

Todo componente interativo **deve** ter os 5 estados:

| Estado | Regra |
|---|---|
| `default` | Aparência base conforme especificação do componente |
| `hover` | Feedback visual: sombra levemente maior ou bg levemente mais escuro |
| `active/pressed` | Scale 0.98 ou bg mais escuro, shadow reduzido |
| `focus` | Ring 2px `border-focus` com offset 2px — obrigatório para acessibilidade |
| `disabled` | Opacity 40%, cursor `not-allowed`, sem hover/active |

---

## Regras Finais

1. **Nunca use valores arbitrários** — apenas os tokens definidos acima.
2. **Se precisar de um token que não existe**, pergunte antes de inventar.
3. **Mesmo componente = mesmos tokens sempre** — sem exceções por contexto.
4. **Mobile-first**: defina o layout mobile primeiro, adapte para desktop com breakpoints.
5. **Hierarquia de leitura**: decisão (comprar/não comprar) → preço → dados de suporte.
6. **Acessibilidade**: todo elemento interativo deve ter estado `focus` visível.
7. **Consistência de status**: use sempre o mesmo token para o mesmo significado semântico (ex: `status-success` = sempre positivo/comprar, nunca decorativo).
