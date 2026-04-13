create extension if not exists pgcrypto;

create table if not exists empresas (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  cnpj text,
  created_at timestamptz default now()
);

create table if not exists perfis (
  id uuid primary key references auth.users(id) on delete cascade,
  empresa_id uuid references empresas(id) on delete set null,
  nome text,
  papel text default 'comprador',
  created_at timestamptz default now()
);

create table if not exists produtos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references empresas(id) on delete cascade,
  ean text not null,
  descricao text,
  principio_ativo text,
  fabricante text,
  fabricante_bruto text,
  curva_abc text,
  estoque integer default 0,
  demanda_mes numeric,
  custo_medio numeric,
  preco_venda numeric,
  grupo text,
  created_at timestamptz default now(),
  unique (empresa_id, ean)
);

create table if not exists historico_precos (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references empresas(id) on delete cascade,
  ean text not null,
  produto_id uuid references produtos(id) on delete set null,
  data_entrada date not null,
  fornecedor text,
  quantidade_unitaria numeric not null,
  valor_total_item numeric not null,
  valor_icms_st numeric default 0,
  valor_outras_despesas numeric default 0,
  preco_unitario numeric generated always as (valor_total_item / nullif(quantidade_unitaria, 0)) stored,
  preco_unitario_liquido numeric generated always as ((valor_total_item - valor_outras_despesas - valor_icms_st) / nullif(quantidade_unitaria, 0)) stored,
  created_at timestamptz default now()
);

create table if not exists analises_oferta (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references empresas(id) on delete cascade,
  usuario_id uuid references perfis(id) on delete set null,
  fornecedor text,
  origem text,
  entrada_bruta text,
  status text default 'pendente',
  created_at timestamptz default now()
);

create table if not exists itens_oferta (
  id uuid primary key default gen_random_uuid(),
  analise_id uuid not null references analises_oferta(id) on delete cascade,
  ean text,
  produto_id uuid references produtos(id) on delete set null,
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
  dados_json jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists vendas_diarias (
  id uuid primary key default gen_random_uuid(),
  empresa_id uuid not null references empresas(id) on delete cascade,
  data_venda date not null,
  ean text not null,
  produto_id uuid references produtos(id) on delete set null,
  quantidade_vendida numeric,
  valor_liquido numeric,
  created_at timestamptz default now()
);

create table if not exists aliases_laboratorio (
  id uuid primary key default gen_random_uuid(),
  alias text not null unique,
  nome_canonico text not null,
  created_at timestamptz default now()
);

alter table produtos enable row level security;
alter table historico_precos enable row level security;
alter table analises_oferta enable row level security;
alter table itens_oferta enable row level security;
alter table vendas_diarias enable row level security;
alter table perfis enable row level security;

create or replace function public.empresa_usuario_atual()
returns uuid
language sql
stable
as $$
  select empresa_id from perfis where id = auth.uid()
$$;

create policy if not exists produtos_isolamento_empresa on produtos
  using (empresa_id = public.empresa_usuario_atual())
  with check (empresa_id = public.empresa_usuario_atual());

create policy if not exists historico_precos_isolamento_empresa on historico_precos
  using (empresa_id = public.empresa_usuario_atual())
  with check (empresa_id = public.empresa_usuario_atual());

create policy if not exists analises_oferta_isolamento_empresa on analises_oferta
  using (empresa_id = public.empresa_usuario_atual())
  with check (empresa_id = public.empresa_usuario_atual());

create policy if not exists itens_oferta_isolamento_empresa on itens_oferta
  using (
    exists (
      select 1 from analises_oferta a
      where a.id = analise_id and a.empresa_id = public.empresa_usuario_atual()
    )
  )
  with check (
    exists (
      select 1 from analises_oferta a
      where a.id = analise_id and a.empresa_id = public.empresa_usuario_atual()
    )
  );

create policy if not exists vendas_diarias_isolamento_empresa on vendas_diarias
  using (empresa_id = public.empresa_usuario_atual())
  with check (empresa_id = public.empresa_usuario_atual());

create policy if not exists perfis_isolamento_empresa on perfis
  using (empresa_id = public.empresa_usuario_atual() or id = auth.uid())
  with check (id = auth.uid());

insert into aliases_laboratorio (alias, nome_canonico)
values
  ('NQ', 'Neoquimica'),
  ('MDL', 'Medley'),
  ('EMS', 'EMS'),
  ('PD', 'Prati-Donaduzzi')
on conflict (alias) do nothing;
