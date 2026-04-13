-- =====================================================================
-- Migration: Criar tabelas de persistência de análises Agno
-- Projeto: Compras PRO
-- Data: 2026-04-12
-- Descrição: Cria as tabelas `analises` e `analise_itens` para persistir
--            os resultados do agente Agno de análise de ofertas.
-- =====================================================================

-- Tabela principal de análises
CREATE TABLE IF NOT EXISTS analises (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    empresa_id      TEXT NOT NULL,
    fornecedor      TEXT,
    origem          TEXT DEFAULT 'texto',
    status          TEXT DEFAULT 'concluida',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Índice para busca por empresa
CREATE INDEX IF NOT EXISTS idx_analises_empresa_id ON analises (empresa_id);

-- Índice para listagem recente
CREATE INDEX IF NOT EXISTS idx_analises_created_at ON analises (created_at DESC);

-- Tabela de itens individuais da análise
CREATE TABLE IF NOT EXISTS analise_itens (
    id                  UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    analise_id          UUID NOT NULL REFERENCES analises(id) ON DELETE CASCADE,
    produto_id          TEXT,
    ean                 TEXT,
    descricao_original  TEXT NOT NULL,
    preco_oferta        NUMERIC(12,4),
    classificacao       TEXT NOT NULL CHECK (classificacao IN ('ouro', 'prata', 'atencao', 'descartavel')),
    confianca_match     TEXT CHECK (confianca_match IN ('alto', 'medio', 'baixo')),
    recomendacao        TEXT,
    dados_json          JSONB,
    created_at          TIMESTAMPTZ DEFAULT now()
);

-- Índice para busca por análise
CREATE INDEX IF NOT EXISTS idx_analise_itens_analise_id ON analise_itens (analise_id);

-- Índice para busca por EAN
CREATE INDEX IF NOT EXISTS idx_analise_itens_ean ON analise_itens (ean);

-- Índice para busca por classificação
CREATE INDEX IF NOT EXISTS idx_analise_itens_classificacao ON analise_itens (classificacao);

-- =====================================================================
-- RLS (Row Level Security) — Segurança por empresa
-- =====================================================================

ALTER TABLE analises ENABLE ROW LEVEL SECURITY;
ALTER TABLE analise_itens ENABLE ROW LEVEL SECURITY;

-- Política: usuários só veem análises da própria empresa
-- (Requer que o JWT contenha app_metadata.empresa_id)
CREATE POLICY analises_empresa_policy ON analises
    FOR ALL
    USING (
        empresa_id = coalesce(
            current_setting('request.jwt.claims', true)::json->>'empresa_id',
            (current_setting('request.jwt.claims', true)::json->'app_metadata'->>'empresa_id')
        )
    );

-- Política: itens de análise seguem a permissão da análise pai
CREATE POLICY analise_itens_empresa_policy ON analise_itens
    FOR ALL
    USING (
        analise_id IN (
            SELECT id FROM analises
            WHERE empresa_id = coalesce(
                current_setting('request.jwt.claims', true)::json->>'empresa_id',
                (current_setting('request.jwt.claims', true)::json->'app_metadata'->>'empresa_id')
            )
        )
    );

-- =====================================================================
-- Trigger para atualizar updated_at automaticamente
-- =====================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_analises
    BEFORE UPDATE ON analises
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
