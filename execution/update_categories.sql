-- Atualiza categorias da Prefeitura de Ivaté no Supabase
-- Rode no SQL Editor do projeto: prefeituras
-- 1. Remove as categorias antigas
DELETE FROM config
WHERE type = 'category';
-- 2. Insere as novas categorias
INSERT INTO config (type, name, color)
VALUES ('category', 'Infraestrutura & Obras', '#f59e0b'),
    ('category', 'Saúde & Atendimento', '#ec4899'),
    ('category', 'Educação & Escolas', '#8b5cf6'),
    ('category', 'Segurança Pública', '#ef4444'),
    ('category', 'Limpeza Urbana', '#10b981'),
    ('category', 'Meio Ambiente', '#22c55e'),
    ('category', 'Agricultura & Rural', '#84cc16'),
    ('category', 'Assistência Social', '#f97316'),
    ('category', 'Transporte & Mobilidade', '#3b82f6');