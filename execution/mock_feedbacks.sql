-- =================================================================
-- SCRIPT DE CORREÇÃO E POPULAÇÃO - PREFEITURA (V2)
-- Copie e cole no SQL Editor do Supabase para corrigir e popular.
-- =================================================================
-- 1. GARANTIR QUE AS COLUNAS EXISTAM
-- Se elas não existirem, serão criadas agora.
ALTER TABLE feedbacks
ADD COLUMN IF NOT EXISTS topic text;
ALTER TABLE feedbacks
ADD COLUMN IF NOT EXISTS resolved_at text;
ALTER TABLE feedbacks
ADD COLUMN IF NOT EXISTS region text;
ALTER TABLE feedbacks
ADD COLUMN IF NOT EXISTS sentiment text;
-- 2. CORRIGIR A SEQUÊNCIA DE IDS
-- Isso evita o erro de "duplicate key value"
SELECT setval(
        pg_get_serial_sequence('feedbacks', 'id'),
        COALESCE(
            (
                SELECT MAX(id) + 1
                FROM feedbacks
            ),
            1
        ),
        false
    );
-- 3. INSERIR DADOS MOCK (20 Feedbacks)
INSERT INTO feedbacks (
        sender,
        name,
        message,
        timestamp,
        category,
        region,
        urgency,
        sentiment,
        topic,
        status,
        resolved_at
    )
VALUES (
        '5511999990001',
        'Maria Silva',
        'Tem um buraco enorme na Rua das Flores, zona norte. Já furou 2 pneus!',
        NOW() - interval '5 minutes',
        'Infraestrutura & Obras',
        'Zona Norte',
        'Urgente',
        'Negativo',
        'Buraco Na Via',
        'aberto',
        NULL
    ),
    (
        '5511999990002',
        'João Santos',
        'Parabéns à prefeitura! Arrumaram a praça do centro, ficou linda demais!',
        NOW() - interval '12 minutes',
        'Limpeza & Meio Ambiente',
        'Centro',
        'Positivo',
        'Positivo',
        'Praça Reformada',
        'aberto',
        NULL
    ),
    (
        '5511999990003',
        'Ana Oliveira',
        'Posto de saúde da zona sul tá sem médico há 3 dias! Absurdo! Minha filha tá doente.',
        NOW() - interval '20 minutes',
        'Saúde & Atendimento',
        'Zona Sul',
        'Urgente',
        'Negativo',
        'Saúde',
        'aberto',
        NULL
    ),
    (
        '5511999990004',
        'Carlos Ferreira',
        'Assalto agora na praça central! Tem gente armada! Cadê a guarda municipal?!',
        NOW() - interval '2 minutes',
        'Segurança Pública',
        'Centro',
        'Critico',
        'Negativo',
        'Segurança',
        'aberto',
        NULL
    ),
    (
        '5511999990005',
        'Fernanda Lima',
        'Ônibus da linha 42 atrasado de novo, faz 40 minutos esperando no ponto da zona leste',
        NOW() - interval '35 minutes',
        'Transporte & Mobilidade',
        'Zona Leste',
        'Urgente',
        'Negativo',
        'Ônibus',
        'aberto',
        NULL
    ),
    (
        '5511999990006',
        'Roberto Almeida',
        'Escola municipal do bairro oeste não tem merenda há uma semana. As crianças ficam com fome!',
        NOW() - interval '45 minutes',
        'Educação & Escolas',
        'Zona Oeste',
        'Urgente',
        'Negativo',
        'Escola',
        'aberto',
        NULL
    ),
    (
        '5511999990007',
        'Lucia Costa',
        'Esgoto aberto na rua principal da zona leste, mau cheiro horrível, tem rato saindo',
        NOW() - interval '55 minutes',
        'Infraestrutura & Obras',
        'Zona Leste',
        'Urgente',
        'Negativo',
        'Esgoto',
        'aberto',
        NULL
    ),
    (
        '5511999990008',
        'Pedro Mendes',
        'A nova ciclovia ficou muito boa, parabéns! Top demais, curti muito!',
        NOW() - interval '60 minutes',
        'Transporte & Mobilidade',
        'Centro',
        'Positivo',
        'Positivo',
        'Ciclovia',
        'aberto',
        NULL
    ),
    (
        '5511999990009',
        'Beatriz Ramos',
        'Semáforo quebrado no cruzamento da Av. Brasil com Rua 7, quase causou acidente!',
        NOW() - interval '1 hour 15 minutes',
        'Transporte & Mobilidade',
        'Zona Norte',
        'Urgente',
        'Negativo',
        'Semáforo',
        'aberto',
        NULL
    ),
    (
        '5511999990010',
        'Marcos Souza',
        'Terreno baldio na zona rural cheio de entulho e lixo, tá virando foco de dengue',
        NOW() - interval '1 hour 30 minutes',
        'Limpeza & Meio Ambiente',
        'Zona Rural',
        'Urgente',
        'Negativo',
        'Lixo/Sujeira',
        'aberto',
        NULL
    ),
    (
        '5511999990011',
        'Camila Rodrigues',
        'Calçada toda quebrada na frente da escola, idosos estão caindo! Zona sul',
        NOW() - interval '2 hours',
        'Infraestrutura & Obras',
        'Zona Sul',
        'Urgente',
        'Negativo',
        'Calçada',
        'em_andamento',
        NULL
    ),
    (
        '5511999990012',
        'Diego Martins',
        'Obrigado por consertarem a iluminação da minha rua! Agora tá seguro de noite. Show!',
        NOW() - interval '2 hours 20 minutes',
        'Infraestrutura & Obras',
        'Zona Oeste',
        'Positivo',
        'Positivo',
        'Iluminação',
        'resolvido',
        (NOW() - interval '1 hour')::text
    ),
    (
        '5511999990013',
        'Patrícia Nunes',
        'Vazamento de água enorme na Rua 15, distrito industrial. A rua tá alagando!',
        NOW() - interval '2 hours 45 minutes',
        'Infraestrutura & Obras',
        'Distrito Industrial',
        'Critico',
        'Negativo',
        'Vazamento',
        'aberto',
        NULL
    ),
    (
        '5511999990014',
        'Thiago Barros',
        'Falta de remédio na UBS central, minha mãe precisa do remédio de pressão e não tem!',
        NOW() - interval '3 hours',
        'Saúde & Atendimento',
        'Centro',
        'Urgente',
        'Negativo',
        'Saúde',
        'em_andamento',
        NULL
    ),
    (
        '5511999990015',
        'Juliana Pereira',
        'A coleta de lixo na zona norte não passa há 4 dias, lixo acumulando nas ruas',
        NOW() - interval '3 hours 30 minutes',
        'Limpeza & Meio Ambiente',
        'Zona Norte',
        'Urgente',
        'Negativo',
        'Coleta De Lixo',
        'aberto',
        NULL
    ),
    (
        '5511999990016',
        'André Vieira',
        'Muito bom o novo parque da zona sul, as crianças adoraram! Arrasou prefeitura!',
        NOW() - interval '4 hours',
        'Limpeza & Meio Ambiente',
        'Zona Sul',
        'Positivo',
        'Positivo',
        'Parque',
        'aberto',
        NULL
    ),
    (
        '5511999990017',
        'Renata Dias',
        'Poste de luz caiu na estrada da zona rural, fio solto no chão! Perigo de morte!',
        NOW() - interval '4 hours 15 minutes',
        'Infraestrutura & Obras',
        'Zona Rural',
        'Critico',
        'Negativo',
        'Poste Caiu',
        'aberto',
        NULL
    ),
    (
        '5511999990018',
        'Felipe Gomes',
        'Creche da zona leste tá com vaga sobrando mas não aceita matrícula, que palhaçada!',
        NOW() - interval '5 hours',
        'Educação & Escolas',
        'Zona Leste',
        'Urgente',
        'Negativo',
        'Escola',
        'aberto',
        NULL
    ),
    (
        '5511999990019',
        'Isabela Moura',
        'Pessoa desmaiou no terminal de ônibus da zona norte, precisa de ambulância urgente!',
        NOW() - interval '1 minute',
        'Segurança Pública',
        'Zona Norte',
        'Critico',
        'Negativo',
        'Emergência Médica',
        'aberto',
        NULL
    ),
    (
        '5511999990020',
        'Lucas Cardoso',
        'Mato alto na praça do bairro oeste, não dá nem pra andar. Precisa de capina urgente',
        NOW() - interval '5 hours 30 minutes',
        'Limpeza & Meio Ambiente',
        'Zona Oeste',
        'Urgente',
        'Negativo',
        'Mato Alto',
        'aberto',
        NULL
    );