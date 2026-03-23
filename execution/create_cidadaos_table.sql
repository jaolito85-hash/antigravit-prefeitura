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
