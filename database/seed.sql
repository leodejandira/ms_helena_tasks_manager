-- Helena Task Manager — Beta
-- Seed dos hábitos fixos.
-- Idempotente: pode ser executado várias vezes sem duplicar registros.
-- Identificador estável = `key` (UNIQUE em habits.key), nunca o id serial.
--
-- IMPORTANTE: as keys 'sem_conteudo' e 'sem_junk_food' são usadas
-- literalmente no frontend (frontend/src/pages/habits/HabitsPage.jsx,
-- RED_HABITS) para decidir quais botões são exibidos em vermelho. Não
-- renomear essas keys sem também atualizar o frontend.

INSERT INTO habits (key, name, type, target, steps) VALUES
    ('beber_agua',          'Beber 10 copos de água',            'counter', 10,   '[]'::jsonb),
    ('sem_conteudo',        'Não consumir conteúdo',              'boolean', NULL, '[]'::jsonb),
    ('atividade_fisica',    'Fazer atividade física',             'boolean', NULL, '[]'::jsonb),
    ('higiene_pessoal',     'Rotina de higiene pessoal',          'steps',   NULL, '["manhã","tarde","noite"]'::jsonb),
    ('sem_junk_food',       'Não consumir junk food',             'boolean', NULL, '[]'::jsonb),
    ('alimentacao_saudavel','Alimentação saudável',               'steps',   NULL, '["café","almoço","jantar"]'::jsonb),
    ('cavaco',              'Tocar 15 min de cavaquinho',         'minutes', 15,   '[]'::jsonb),
    ('informacao',          'Usar 15 minutos para se informar',   'minutes', 15,   '[]'::jsonb)
ON CONFLICT (key) DO UPDATE SET
    name   = EXCLUDED.name,
    type   = EXCLUDED.type,
    target = EXCLUDED.target,
    steps  = EXCLUDED.steps;
