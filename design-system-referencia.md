# Design System

## Visao geral

Este sistema usa uma linguagem visual escura, sofisticada e orientada a paineis analiticos. A base do estilo combina superficies em gradiente grafite, brilho sutil azul e componentes com cantos generosos. O objetivo e manter consistencia entre filtros, cards, graficos, tabelas e futuras telas administrativas.

## Principios

- Priorizar contraste alto com fundo escuro e conteudo claro.
- Usar gradientes discretos, nunca chamativos, para criar profundidade.
- Tratar cards, graficos e filtros como a mesma familia visual.
- Manter densidade de informacao alta, mas com hierarquia clara.
- Usar azul como cor principal de acao e destaque operacional.

## Fundacoes visuais

### Superficie principal

- Classe base: `ds-panel`
- Estrutura visual:
  - borda suave em `zinc-800/80`
  - gradiente de `zinc-900` para `zinc-950`
  - brilho radial azul muito sutil no topo
  - linha superior transluzida para acabamento premium
  - sombra profunda, difusa e escura

### Raios e volumes

- Cards principais: `rounded-[28px]` ou `rounded-[30px]`
- Campos internos: `rounded-2xl` ou `rounded-[24px]`
- Chips e badges: `rounded-full`

### Cores

- Fundo macro: `zinc-950`
- Superficie elevada: gradiente entre `zinc-900` e `zinc-950`
- Borda: `zinc-800` / `zinc-700`
- Texto principal: `zinc-50`
- Texto secundario: `zinc-400`
- Texto terciario: `zinc-500`
- Cor primaria: azul (`blue-500` / `blue-600`)
- Sucesso: esmeralda
- Erro: vermelho
- Alerta operacional: ambar

## Tipografia

- Titulo de pagina: grande, forte, `text-3xl font-bold tracking-tight`
- Titulo de card: `text-sm` a `text-base`, peso medio
- Valor numerico principal: `text-4xl font-semibold tracking-tight`
- Label tecnica/eyebrow: `ds-eyebrow`
  - uppercase
  - tracking amplo
  - peso forte
  - cor `zinc-500`

## Componentes

### Cards de metrica

- Devem usar `ds-panel`
- Ter 3 camadas de informacao:
  1. eyebrow contextual
  2. titulo funcional
  3. numero principal com apoio em chip lateral
- Icone sempre dentro de `ds-icon-chip`

### Campos de filtro

- Campos usam o mesmo gradiente base dos cards
- Label pequena em uppercase
- Controle interno com fundo `zinc-950/90`
- Foco com borda azul e glow sutil
- Datas, selects e buscas devem parecer parte do mesmo bloco

### Graficos

- O container do grafico deve usar `ds-panel`
- A area do plot deve ficar dentro de uma segunda superficie interna:
  - `rounded-[24px]`
  - `bg-zinc-950/45`
  - borda suave
- Linhas de grade devem ser discretas e tracejadas
- Barras devem usar gradientes, nunca cor plana pura
- Sempre exibir pequenos chips-resumo acima do grafico quando fizer sentido
- Tooltip deve seguir o mesmo estilo de painel premium

### Listas e tabelas resumidas

- Containers principais usam `ds-panel`
- Linhas interativas devem ter hover suave com fundo levemente elevado
- Acoes pequenas usam botao circular com borda e fundo escuro

### Botoes

- Primario: azul forte com glow curto
- Secundario: fundo escuro com borda `zinc-700`
- Hover sempre com mudanca de contraste, sem exagero

## Tokens semanticos recomendados

- Operacional / andamento: azul
- Confirmado / concluido: esmeralda
- Problema / falha: vermelho
- Atenção / fila: ambar
- Neutro / estrutura: zinc

## Regras para novas telas

- Toda nova tela administrativa deve partir de cards `ds-panel`
- Filtros devem reaproveitar a familia visual ja criada em `FilterDateInput` e `FilterSelect`
- Graficos devem usar gradientes coerentes com o contexto, mantendo a base escura
- Evitar blocos brancos, cinzas claros ou superficies planas sem profundidade
- Evitar misturar estilos arredondados pequenos com paineis grandes; manter linguagem de cantos amplos
- Sempre separar informacao em hierarquia: eyebrow, titulo, descricao, valor/conteudo

## Arquivos de referencia

- `dashboard/src/app/globals.css`
- `dashboard/src/components/FilterDateInput.tsx`
- `dashboard/src/components/FilterSelect.tsx`
- `dashboard/src/components/DashboardCharts.tsx`
- `dashboard/src/app/(dashboard)/page.tsx`

## Direcao futura

Ao construir novas telas, manter este visual como padrao para:

- cards de resumo
- cabecalhos de secoes
- filtros e barras de busca
- graficos operacionais
- tabelas administrativas
- modais e drawers

Se um novo componente nao parecer pertencer a um painel analitico premium escuro com destaque azul, ele deve ser revisado antes de entrar no sistema.
