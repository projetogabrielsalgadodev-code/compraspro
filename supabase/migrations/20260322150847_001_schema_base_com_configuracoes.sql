create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.empresas (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  cnpj text,
  created_at timestamptz not null default now()
);

create table if not exists public.perfis (
  id uuid primary key references auth.users(id) on delete cascade,
  empresa_id uuid references public.empresas(id) on delete set null,
  nome text,
  email text,
  papel text not null default 'comprador',
  created_at timestamptz not null default now()
);

create table if not exists public.produtos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas(id) on delete cascade,
  ean text not null,
  descricao text,
  principio_ativo text,
  fabricante text,
  fabricante_bruto text,
  curva_abc text,
  estoque integer not null default 0,
  demanda_mes numeric,
  custo_medio numeric,
  preco_venda numeric,
  grupo text,
  created_at timestamptz not null default now(),
  unique (empresa_id, ean)
);

create table if not exists public.historico_precos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas(id) on delete cascade,
  ean text not null,
  produto_id uuid references public.produtos(id) on delete set null,
  data_entrada date not null,
  fornecedor text,
  quantidade_unitaria numeric not null,
  valor_total_item numeric not null,
  valor_icms_st numeric not null default 0,
  valor_outras_despesas numeric not null default 0,
  preco_unitario numeric generated always as (valor_total_item / nullif(quantidade_unitaria, 0)) stored,
  preco_unitario_liquido numeric generated always as ((valor_total_item - valor_outras_despesas - valor_icms_st) / nullif(quantidade_unitaria, 0)) stored,
  created_at timestamptz not null default now()
);

create table if not exists public.analises_oferta (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas(id) on delete cascade,
  usuario_id uuid references public.perfis(id) on delete set null,
  fornecedor text,
  origem text,
  entrada_bruta text,
  status text not null default 'pendente',
  created_at timestamptz not null default now()
);

create table if not exists public.itens_oferta (
  id uuid primary key default gen_random_uuid(),
  analise_id uuid not null references public.analises_oferta(id) on delete cascade,
  ean text,
  produto_id uuid references public.produtos(id) on delete set null,
  descricao_bruta text,
  preco_oferta numeric,
  menor_preco_historico numeric,
  origem_menor_historico text,
  desconto_percentual numeric,
  estoque_item integer,
  demanda_mes numeric,
  sugestao_pedido integer,
  estoque_equivalentes integer,
  classificacao text,
  confianca_match text,
  recomendacao text,
  dados_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.vendas_diarias (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references public.empresas(id) on delete cascade,
  data_venda date not null,
  ean text not null,
  produto_id uuid references public.produtos(id) on delete set null,
  quantidade_vendida numeric,
  valor_liquido numeric,
  created_at timestamptz not null default now()
);

create table if not exists public.aliases_laboratorio (
  id uuid primary key default gen_random_uuid(),
  alias text not null unique,
  nome_canonico text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.configuracoes_empresa (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null unique references public.empresas(id) on delete cascade,
  estoque_minimo_dias integer not null default 30,
  estoque_alto_dias integer not null default 90,
  vantagem_minima_percentual numeric not null default 5,
  metodo_comparacao text not null default 'average',
  considerar_equivalentes boolean not null default true,
  horizonte_sugestao_meses integer not null default 3,
  usar_demanda_mes_sugcompra boolean not null default true,
  exibir_extremos_historicos boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.criar_configuracao_padrao_empresa()
returns trigger
language plpgsql
as $$
begin
  insert into public.configuracoes_empresa (empresa_id)
  values (new.id)
  on conflict (empresa_id) do nothing;
  return new;
end;
$$;

create or replace trigger trg_configuracoes_empresa_updated_at
before update on public.configuracoes_empresa
for each row
execute function public.set_updated_at();

create or replace trigger trg_empresas_cria_configuracao_padrao
after insert on public.empresas
for each row
execute function public.criar_configuracao_padrao_empresa();
