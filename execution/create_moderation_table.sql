-- Tabela de estado de moderação (bloqueios/mutes/avisos por número).
-- Substitui o arquivo local execution/moderation_state.json, que era perdido
-- a cada deploy. Rode no SQL Editor do Supabase (projeto: prefeituras).
CREATE TABLE IF NOT EXISTS moderation (
    remote_jid text PRIMARY KEY,
    entry jsonb NOT NULL,
    updated_at timestamptz DEFAULT timezone('utc'::text, now())
);

-- RLS no mesmo padrão da tabela feedbacks (acesso via anon key).
ALTER TABLE moderation ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "moderation_select" ON moderation;
DROP POLICY IF EXISTS "moderation_insert" ON moderation;
DROP POLICY IF EXISTS "moderation_update" ON moderation;
DROP POLICY IF EXISTS "moderation_delete" ON moderation;

CREATE POLICY "moderation_select" ON moderation FOR SELECT USING (true);
CREATE POLICY "moderation_insert" ON moderation FOR INSERT WITH CHECK (true);
CREATE POLICY "moderation_update" ON moderation FOR UPDATE USING (true);
CREATE POLICY "moderation_delete" ON moderation FOR DELETE USING (true);
