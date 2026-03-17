-- Adiciona coluna 'protocol' na tabela feedbacks (se já não existir)
-- Rode no SQL Editor do Supabase (projeto: prefeituras)
ALTER TABLE feedbacks
ADD COLUMN IF NOT EXISTS protocol text;