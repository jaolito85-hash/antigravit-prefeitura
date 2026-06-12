-- Adiciona campos para handoff humano obrigatorio em casos sensiveis.
-- Seguro para rodar multiplas vezes (IF NOT EXISTS).

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS handoff_required BOOLEAN DEFAULT FALSE;
ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS sensitive_case BOOLEAN DEFAULT FALSE;
ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS sensitive_reasons JSONB DEFAULT '[]'::jsonb;
