-- ═══════════════════════════════════════════════════════════════════════════
-- Review core features — bundle de correções aplicadas no review de 2026-05-14
--
-- Espelha o que foi aplicado no Supabase remoto. Idempotente; pode ser rodada
-- em qualquer ambiente novo.
-- ═══════════════════════════════════════════════════════════════════════════

-- ─── 1. Rotação do cron secret (assume vault já populado por setup_pg_cron) ──
-- Em ambiente novo, antes desta migration rodar:
--   SELECT vault.create_secret('SEU_SECRET', 'cron_whatsapp_secret');

-- ─── 2. Dispatcher do cron WhatsApp ──────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.disparar_cron_por_empresa()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
  emp RECORD;
  cron_secret TEXT;
BEGIN
  SELECT decrypted_secret INTO cron_secret
  FROM vault.decrypted_secrets
  WHERE name = 'cron_whatsapp_secret'
  LIMIT 1;
  IF cron_secret IS NULL THEN
    RAISE EXCEPTION 'cron_whatsapp_secret não encontrado no Vault';
  END IF;
  FOR emp IN
    SELECT DISTINCT wi.empresa_id
    FROM whatsapp_instancias wi
    WHERE wi.status = 'conectada'
      AND EXISTS (
        SELECT 1 FROM whatsapp_mensagens wm
        WHERE wm.empresa_id = wi.empresa_id
          AND wm.status_analise IN ('pendente', 'erro_analise')
          AND wm.tipo_mensagem = 'text'
      )
  LOOP
    PERFORM net.http_post(
      url := 'https://compraspro.onrender.com/api/whatsapp/cron-whatsapp',
      headers := jsonb_build_object('Content-Type', 'application/json', 'X-Cron-Secret', cron_secret),
      body := jsonb_build_object('empresa_id', emp.empresa_id)
    );
  END LOOP;
END;
$function$;

REVOKE EXECUTE ON FUNCTION public.disparar_cron_por_empresa() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.disparar_cron_por_empresa() TO postgres, service_role;

-- ─── 3. Claim atômico ───────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.claim_whatsapp_messages(
  p_empresa_id UUID,
  p_limit INT DEFAULT 50
)
RETURNS TABLE (
  id UUID,
  empresa_id UUID,
  chat_id TEXT,
  conteudo_texto TEXT,
  sender_phone TEXT,
  tipo_mensagem TEXT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
BEGIN
  RETURN QUERY
  WITH cte AS (
    SELECT m.id
    FROM whatsapp_mensagens m
    WHERE m.empresa_id = p_empresa_id
      AND m.status_analise IN ('pendente', 'erro_analise')
      AND m.tipo_mensagem = 'text'
    ORDER BY m.timestamp_msg
    LIMIT p_limit
    FOR UPDATE SKIP LOCKED
  )
  UPDATE whatsapp_mensagens m
  SET status_analise = 'em_analise'
  FROM cte
  WHERE m.id = cte.id
  RETURNING m.id, m.empresa_id, m.chat_id, m.conteudo_texto, m.sender_phone, m.tipo_mensagem;
END;
$function$;

REVOKE EXECUTE ON FUNCTION public.claim_whatsapp_messages(UUID, INT) FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.claim_whatsapp_messages(UUID, INT) TO service_role;

-- ─── 4. Reaper ──────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.reaper_whatsapp_em_analise()
RETURNS INT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE affected INT;
BEGIN
  WITH cte AS (
    UPDATE whatsapp_mensagens
    SET status_analise = 'pendente'
    WHERE status_analise = 'em_analise'
      AND created_at < now() - interval '30 minutes'
    RETURNING 1
  )
  SELECT count(*) INTO affected FROM cte;
  RETURN affected;
END;
$function$;

REVOKE EXECUTE ON FUNCTION public.reaper_whatsapp_em_analise() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.reaper_whatsapp_em_analise() TO postgres, service_role;

-- ─── 5. Índices ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_wamsg_analise
  ON public.whatsapp_mensagens(analise_id)
  WHERE analise_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_wamsg_cron_filter
  ON public.whatsapp_mensagens(empresa_id, status_analise, tipo_mensagem, timestamp_msg);

-- ─── 6. Drop tabelas legadas ────────────────────────────────────────────────
DROP TABLE IF EXISTS public.analise_itens CASCADE;
DROP TABLE IF EXISTS public.analises CASCADE;

-- ─── 7. RLS optimization e merge ────────────────────────────────────────────
-- Ver script setup_pg_cron.sql e migration optimize_rls_policies para o detalhe.

-- ─── 8. Agendar jobs ────────────────────────────────────────────────────────
DO $$
DECLARE jid BIGINT;
BEGIN
  SELECT jobid INTO jid FROM cron.job WHERE jobname='analise-whatsapp-auto';
  IF jid IS NOT NULL THEN PERFORM cron.unschedule(jid); END IF;
END $$;
SELECT cron.schedule(
  'analise-whatsapp-auto',
  '0 11,13,15,17,19,21,23 * * *',
  'SELECT public.disparar_cron_por_empresa();'
);

DO $$
DECLARE jid BIGINT;
BEGIN
  SELECT jobid INTO jid FROM cron.job WHERE jobname='reaper-whatsapp-em-analise';
  IF jid IS NOT NULL THEN PERFORM cron.unschedule(jid); END IF;
END $$;
SELECT cron.schedule(
  'reaper-whatsapp-em-analise',
  '*/15 * * * *',
  'SELECT public.reaper_whatsapp_em_analise();'
);
