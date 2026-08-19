import pytest

from app.workouts.parser import parse_workout_text, WorkoutParseError

FULL_EXAMPLE = """Treinamento noturno 🏋️
Sexta-feira, Ago 07, 2026 às 8:21pm

Barra Fixa
"Warm up"
Série 1: 2 repetições
Série 2: 2 repetições
Série 3: 2 repetições

Balanço Na Barra Fixa
"Warm up"
Série 1: 10 repetições
Série 2: 10 repetições
Série 3: 10 repetições

Abdominal (Com Peso)
"Warm up"
Série 1: 10 kg x 20
Série 2: 10 kg x 20
Série 3: 10 kg x 20

Corrida Sprint 500m
"Skill"
Série 1: 1min 53s

Abdominal Tradicional Com Lançamento Wall Ball
"Wod"
Série 1: 10 kg x 15
Série 2: 10 kg x 20
Série 3: 10 kg x 25

Saltos Corda
"Warm up"
Série 1: 50 repetições
Série 2: 50 repetições
Série 3: 50 repetições

Elevação Kipping
"Wod"
Série 1: 5 repetições
Série 2: 5 repetições
Série 3: 10 repetições

Saltos Corda
"Wod"
Série 1: 50 repetições
Série 2: 60 repetições
Série 3: 70 repetições

@hevyapp
https://hevy.com/workout/wJIH0rqTGZH
"""


# ---------------------------------------------------------------------
# Caso 1 — repetição
# ---------------------------------------------------------------------

def test_caso1_repeticao():
    text = (
        "Treino A\n"
        "Segunda-feira, Jan 05, 2026 às 7:00am\n\n"
        "Agachamento\n"
        '"Wod"\n'
        "Série 1: 5 repetições\n"
    )
    parsed = parse_workout_text(text)
    s = parsed.exercises[0].sets[0]
    assert s.repetitions == 5
    assert s.weight is None
    assert s.duration_seconds is None


# ---------------------------------------------------------------------
# Caso 2 — peso + repetição
# ---------------------------------------------------------------------

def test_caso2_peso_repeticao():
    text = (
        "Treino A\n"
        "Segunda-feira, Jan 05, 2026 às 7:00am\n\n"
        "Supino\n"
        '"Wod"\n'
        "Série 1: 10 kg x 20\n"
    )
    parsed = parse_workout_text(text)
    s = parsed.exercises[0].sets[0]
    assert s.weight == 10
    assert s.unit == "kg"
    assert s.repetitions == 20


# ---------------------------------------------------------------------
# Caso 3 — tempo
# ---------------------------------------------------------------------

def test_caso3_tempo():
    text = (
        "Treino A\n"
        "Segunda-feira, Jan 05, 2026 às 7:00am\n\n"
        "Corrida Sprint 500m\n"
        '"Skill"\n'
        "Série 1: 1min 53s\n"
    )
    parsed = parse_workout_text(text)
    s = parsed.exercises[0].sets[0]
    assert s.duration_seconds == 113
    assert s.repetitions is None
    assert s.weight is None


# ---------------------------------------------------------------------
# Caso 4 — múltiplos exercícios (exemplo completo real)
# ---------------------------------------------------------------------

def test_caso4_multiplos_exercicios():
    parsed = parse_workout_text(FULL_EXAMPLE)
    assert parsed.name == "Treinamento noturno"
    assert parsed.exercise_count == 8
    assert parsed.set_count == 22
    names = [ex.exercise_name for ex in parsed.exercises]
    assert names[0] == "Barra Fixa"
    assert names[3] == "Corrida Sprint 500m"


# ---------------------------------------------------------------------
# Caso 5 — exercícios com o mesmo nome permanecem distintos e ordenados
# ---------------------------------------------------------------------

def test_caso5_exercicios_com_mesmo_nome():
    parsed = parse_workout_text(FULL_EXAMPLE)
    saltos = [ex for ex in parsed.exercises if ex.exercise_name == "Saltos Corda"]
    assert len(saltos) == 2
    assert saltos[0].exercise_order != saltos[1].exercise_order
    assert saltos[0].set_type == "Warm up"
    assert saltos[1].set_type == "Wod"
    # a ordem original do treino é preservada (Saltos Corda Warm up vem
    # antes de Elevação Kipping, que vem antes de Saltos Corda Wod)
    order_by_name = [ex.exercise_name for ex in parsed.exercises]
    assert order_by_name.index("Saltos Corda") < order_by_name.index("Elevação Kipping")


# ---------------------------------------------------------------------
# Caso 6 — treino sem link do Hevy
# ---------------------------------------------------------------------

def test_caso6_sem_link_hevy():
    text = (
        "Treino A\n"
        "Segunda-feira, Jan 05, 2026 às 7:00am\n\n"
        "Agachamento\n"
        '"Wod"\n'
        "Série 1: 5 repetições\n"
    )
    parsed = parse_workout_text(text)
    assert parsed.source is None
    assert parsed.source_url is None
    assert parsed.exercise_count == 1


def test_caso6b_com_link_hevy():
    parsed = parse_workout_text(FULL_EXAMPLE)
    assert parsed.source == "hevy"
    assert parsed.source_url == "https://hevy.com/workout/wJIH0rqTGZH"


# ---------------------------------------------------------------------
# Caso 7 — texto inválido
# ---------------------------------------------------------------------

def test_caso7_texto_invalido():
    with pytest.raises(WorkoutParseError):
        parse_workout_text("isso não é um treino, só um texto qualquer")


def test_caso7_texto_vazio():
    with pytest.raises(WorkoutParseError):
        parse_workout_text("")


def test_caso7_sem_series():
    text = "Treino A\nSegunda-feira, Jan 05, 2026 às 7:00am\n\nAgachamento\n\"Wod\"\n"
    with pytest.raises(WorkoutParseError):
        parse_workout_text(text)


# ---------------------------------------------------------------------
# Caso 8 — timezone: a data não pode ser deslocada por conversão UTC
# ---------------------------------------------------------------------

def test_caso8_timezone_nao_desloca_data():
    parsed = parse_workout_text(FULL_EXAMPLE)
    # "Ago 07, 2026 às 8:21pm" (horário de Brasília) deve continuar sendo
    # 2026-08-07, mesmo esse horário correspondendo a 2026-08-07T23:21:00+00:00
    # em UTC (ou seja, ainda no mesmo dia em UTC neste caso — o teste abaixo
    # cobre também o caso em que UTC já viraria o dia seguinte).
    assert parsed.workout_date == "2026-08-07"


def test_caso8_timezone_proximo_da_meia_noite():
    # 23:30 em Brasília (UTC-3) é 02:30 do dia seguinte em UTC.
    # Uma conversão ingênua para UTC antes de extrair a data erraria o dia.
    text = (
        "Treino tarde da noite\n"
        "Sexta-feira, Ago 07, 2026 às 11:30pm\n\n"
        "Agachamento\n"
        '"Wod"\n'
        "Série 1: 5 repetições\n"
    )
    parsed = parse_workout_text(text)
    assert parsed.workout_date == "2026-08-07"


# ---------------------------------------------------------------------
# Formatos adicionais
# ---------------------------------------------------------------------

def test_nome_do_treino_remove_emoji():
    parsed = parse_workout_text(FULL_EXAMPLE)
    assert "🏋️" not in parsed.name
    assert parsed.name == "Treinamento noturno"


def test_campo_nao_reconhecido_vira_observacao_sem_inventar_numero():
    text = (
        "Treino A\n"
        "Segunda-feira, Jan 05, 2026 às 7:00am\n\n"
        "Prancha\n"
        '"Wod"\n'
        "Série 1: falha na terceira tentativa\n"
    )
    parsed = parse_workout_text(text)
    s = parsed.exercises[0].sets[0]
    assert s.repetitions is None
    assert s.weight is None
    assert s.duration_seconds is None
    assert s.notes == "falha na terceira tentativa"
