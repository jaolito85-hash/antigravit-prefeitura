-- Adiciona coluna handoff_operator na tabela feedbacks
-- Armazena o nome do operador que assumiu o atendimento (handoff humano)
-- NULL = Clara (IA) responde automaticamente
-- "admin" / "João" = operador humano assumiu

ALTER TABLE feedbacks ADD COLUMN IF NOT EXISTS handoff_operator TEXT DEFAULT NULL;
