-- Migração: cria tabela de cidadãos para controle de consentimento LGPD
-- Seguro para rodar múltiplas vezes (IF NOT EXISTS)

CREATE TABLE IF NOT EXISTS cidadaos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    telefone TEXT UNIQUE NOT NULL,
    nome TEXT,
    consentimento BOOLEAN DEFAULT FALSE,
    consentido_em TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índice para busca rápida por telefone
CREATE INDEX IF NOT EXISTS idx_cidadaos_telefone ON cidadaos (telefone);

-- RLS: policies permissivas (padrao do projeto, igual feedbacks/config).
-- Sem isso, a chave `anon` e bloqueada. Com service_role o bypass e automatico,
-- mas deixamos as policies pra evitar quebrar producao se a chave for trocada.
ALTER TABLE cidadaos ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'cidadaos' AND policyname = 'Allow public read cidadaos') THEN
        CREATE POLICY "Allow public read cidadaos" ON cidadaos FOR SELECT USING (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'cidadaos' AND policyname = 'Allow public insert cidadaos') THEN
        CREATE POLICY "Allow public insert cidadaos" ON cidadaos FOR INSERT WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'cidadaos' AND policyname = 'Allow public update cidadaos') THEN
        CREATE POLICY "Allow public update cidadaos" ON cidadaos FOR UPDATE USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'cidadaos' AND policyname = 'Allow public delete cidadaos') THEN
        CREATE POLICY "Allow public delete cidadaos" ON cidadaos FOR DELETE USING (true);
    END IF;
END$$;
