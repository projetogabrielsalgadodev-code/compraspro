-- ═══════════════════════════════════════════════════════════════════════════
-- ComprasPRO — pg_cron + pg_net Setup
-- 
-- INSTRUÇÕES: Execute este script NO SQL EDITOR DO SUPABASE (Dashboard)
-- Pré-requisito: Habilitar pg_cron e pg_net em Database > Extensions
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. Habilitar extensões (se ainda não estiverem ativas)
CREATE EXTENSION IF NOT EXISTS pg_cron;
CREATE EXTENSION IF NOT EXISTS pg_net;

-- 2. Função que dispara 1 POST por empresa com instância conectada
-- Só dispara para empresas que TÊM mensagens pendentes (zero desperdício)
-- ATENÇÃO: Troque 'SEU_CRON_SECRET_AQUI' pelo MESMO valor usado no Render
CREATE OR REPLACE FUNCTION disparar_cron_por_empresa() RETURNS void AS $$
DECLARE
  emp RECORD;
  cron_secret TEXT := '2scQM-tZDKQZZUtwJR8UkzJI4D3uWJJI-yAuUZUOXFo';
BEGIN
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
      url := 'https://compraspro-api.onrender.com/api/whatsapp/cron-whatsapp',
      headers := jsonb_build_object(
        'Content-Type', 'application/json',
        'X-Cron-Secret', cron_secret
      ),
      body := jsonb_build_object('empresa_id', emp.empresa_id)
    );
  END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 3. Agendar análise automática a cada 2 horas
-- pg_cron roda em UTC. '0 */2 * * *' = a cada 2h (00:00, 02:00... UTC)
-- Para horário comercial BRT: '0 11,13,15,17,19,21 * * *' (= 08h-18h BRT)
SELECT cron.schedule(
  'analise-whatsapp-auto',
  '0 */2 * * *',
  'SELECT disparar_cron_por_empresa();'
);

-- 4. Agendar limpeza automática de dados antigos (diariamente às 03:00 UTC)
SELECT cron.schedule(
  'limpeza-whatsapp-90d',
  '0 3 * * *',
  $$
  DELETE FROM whatsapp_mensagens
  WHERE created_at < now() - interval '90 days';

  DELETE FROM notificacoes
  WHERE created_at < now() - interval '30 days';
  $$
);

-- 5. Verificar jobs criados
SELECT * FROM cron.job ORDER BY jobid;

-- ═══════════════════════════════════════════════════════════════════════════
-- MONITORAMENTO (executar quando quiser verificar)
-- ═══════════════════════════════════════════════════════════════════════════
-- SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 20;
