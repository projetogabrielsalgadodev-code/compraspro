create index if not exists idx_produtos_empresa_ean on public.produtos (empresa_id, ean);
create index if not exists idx_produtos_empresa_principio_ativo on public.produtos (empresa_id, principio_ativo);
create index if not exists idx_produtos_empresa_fabricante on public.produtos (empresa_id, fabricante);

create index if not exists idx_historico_precos_empresa_ean_data on public.historico_precos (empresa_id, ean, data_entrada desc);
create index if not exists idx_historico_precos_produto_id on public.historico_precos (produto_id);

create index if not exists idx_analises_oferta_empresa_created_at on public.analises_oferta (empresa_id, created_at desc);
create index if not exists idx_analises_oferta_empresa_fornecedor on public.analises_oferta (empresa_id, fornecedor);

create index if not exists idx_itens_oferta_analise_id on public.itens_oferta (analise_id);
create index if not exists idx_itens_oferta_produto_id on public.itens_oferta (produto_id);
create index if not exists idx_itens_oferta_classificacao on public.itens_oferta (classificacao);

create index if not exists idx_vendas_diarias_empresa_ean_data on public.vendas_diarias (empresa_id, ean, data_venda desc);
create index if not exists idx_vendas_diarias_produto_id on public.vendas_diarias (produto_id);

create index if not exists idx_configuracoes_empresa_empresa_id on public.configuracoes_empresa (empresa_id);
create index if not exists idx_perfis_empresa_id on public.perfis (empresa_id);

insert into public.aliases_laboratorio (alias, nome_canonico)
values
  ('NQ', 'Neoquimica'),
  ('MDL', 'Medley'),
  ('EMS', 'EMS'),
  ('PD', 'Prati-Donaduzzi')
on conflict (alias) do update
set nome_canonico = excluded.nome_canonico;
