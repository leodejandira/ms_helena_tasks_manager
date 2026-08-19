"""
Parser do texto de treino exportado pelo app Hevy (compartilhamento em
texto). Puro (sem I/O, sem banco) — só recebe uma string e devolve uma
estrutura `ParsedWorkout`, o que permite testá-lo isoladamente.

Formato de entrada esperado (blocos separados por linha em branco):

    Treinamento noturno 🏋️
    Sexta-feira, Ago 07, 2026 às 8:21pm

    Barra Fixa
    "Warm up"
    Série 1: 2 repetições
    Série 2: 2 repetições

    Corrida Sprint 500m
    "Skill"
    Série 1: 1min 53s

    @hevyapp
    https://hevy.com/workout/wJIH0rqTGZH

O bloco de cabeçalho (nome + data) e o bloco final de origem (@hevyapp +
link) são tratados como opcionais/best-effort quando fizer sentido — mas
nome, data, ao menos um exercício e ao menos uma série são obrigatórios
(ver `WorkoutParseError`).
"""

import re
from typing import List, Optional

from app.timezone_utils import local_datetime
from app.workouts.schemas import ParsedExercise, ParsedSet, ParsedWorkout


class WorkoutParseError(Exception):
    """Levantado quando o texto não pôde ser interpretado como um treino
    válido (ver seção de validação dos requisitos)."""


# ---------------------------------------------------------------------
# Meses (pt-BR e en, com e sem ponto de abreviação) -> número do mês
# ---------------------------------------------------------------------

_MONTHS = {
    "jan": 1, "janeiro": 1,
    "fev": 2, "fevereiro": 2, "feb": 2, "february": 2,
    "mar": 3, "marco": 3, "março": 3, "march": 3,
    "abr": 4, "abril": 4, "apr": 4, "april": 4,
    "mai": 5, "maio": 5, "may": 5,
    "jun": 6, "junho": 6, "june": 6,
    "jul": 7, "julho": 7, "july": 7,
    "ago": 8, "agosto": 8, "aug": 8, "august": 8,
    "set": 9, "setembro": 9, "sep": 9, "sept": 9, "september": 9,
    "out": 10, "outubro": 10, "oct": 10, "october": 10,
    "nov": 11, "novembro": 11, "november": 11,
    "dez": 12, "dezembro": 12, "dec": 12, "december": 12,
}

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E6-\U0001F1FF"
    "\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE,
)

_DATE_LINE_RE = re.compile(
    r"""
    ^\s*
    (?P<weekday>[^,]+),\s*
    (?P<month>[A-Za-zçÇãÃéÉ]+)\.?\s+
    (?P<day>\d{1,2}),\s*
    (?P<year>\d{4})
    \s+(?:às|as|at)\s+
    (?P<hour>\d{1,2}):(?P<minute>\d{2})\s*
    (?P<ampm>[ap]\.?m\.?)?
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

_SET_LINE_RE = re.compile(
    r"""^\s*(?:s[ée]rie|set)\s*(?P<num>\d+)\s*:\s*(?P<rest>.+?)\s*$""",
    re.IGNORECASE,
)

_TYPE_LINE_RE = re.compile(r'^\s*"(?P<type>[^"]+)"\s*$')

_REPS_RE = re.compile(
    r"^(?P<reps>\d+(?:[.,]\d+)?)\s*(?:repeti[cç][oõ]es|reps?)\s*$", re.IGNORECASE
)
_WEIGHT_REPS_RE = re.compile(
    r"^(?P<weight>\d+(?:[.,]\d+)?)\s*(?P<unit>kg|lb|lbs)\s*x\s*(?P<reps>\d+(?:[.,]\d+)?)\s*$",
    re.IGNORECASE,
)
_TIME_RE = re.compile(
    r"^(?:(?P<h>\d+)\s*h\s*)?(?:(?P<m>\d+)\s*min\s*)?(?:(?P<s>\d+(?:[.,]\d+)?)\s*s)?\s*$",
    re.IGNORECASE,
)

_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


def _to_float(raw: str) -> float:
    return float(raw.replace(",", "."))


def _parse_set_value(raw: str) -> ParsedSet:
    """Interpreta o texto após 'Série N:' — ver seção 7 dos requisitos.
    Nunca inventa peso/repetição: campos não encontrados ficam None."""
    raw = raw.strip()

    m = _WEIGHT_REPS_RE.match(raw)
    if m:
        return ParsedSet(
            set_number=0,  # preenchido pelo chamador
            weight=_to_float(m.group("weight")),
            unit=m.group("unit").lower(),
            repetitions=int(_to_float(m.group("reps"))),
        )

    m = _REPS_RE.match(raw)
    if m:
        return ParsedSet(set_number=0, repetitions=int(_to_float(m.group("reps"))))

    m = _TIME_RE.match(raw)
    if m and (m.group("h") or m.group("m") or m.group("s")):
        hours = int(m.group("h")) if m.group("h") else 0
        minutes = int(m.group("m")) if m.group("m") else 0
        seconds = _to_float(m.group("s")) if m.group("s") else 0
        total = hours * 3600 + minutes * 60 + seconds
        return ParsedSet(set_number=0, duration_seconds=int(round(total)))

    # Formato não reconhecido: preserva o texto original como observação,
    # sem inventar valores numéricos.
    return ParsedSet(set_number=0, notes=raw)


def _parse_date_line(line: str) -> Optional[str]:
    m = _DATE_LINE_RE.match(line)
    if not m:
        return None

    month_key = m.group("month").strip().lower().rstrip(".")
    month = _MONTHS.get(month_key)
    if not month:
        return None

    day = int(m.group("day"))
    year = int(m.group("year"))
    hour = int(m.group("hour"))
    minute = int(m.group("minute"))
    ampm = (m.group("ampm") or "").lower().replace(".", "")

    if ampm == "pm" and hour != 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0

    try:
        # Componentes já são o horário LOCAL (America/Sao_Paulo) em que o
        # treino aconteceu — construímos o datetime diretamente nesse fuso
        # e extraímos a data de calendário dele, sem passar por UTC, para
        # que a conversão nunca desloque o dia (ver seção "Corrigir fuso
        # horário" dos requisitos).
        dt = local_datetime(year, month, day, hour, minute)
    except ValueError:
        return None

    return dt.date().isoformat()


def _split_blocks(text: str) -> List[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", normalized.strip())
    return [b.strip("\n") for b in blocks if b.strip()]


def _is_source_block(block: str) -> bool:
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if not lines:
        return False
    return any(l.startswith("@") for l in lines) or any(_URL_RE.search(l) for l in lines)


def _parse_exercise_block(block: str, order: int) -> Optional[ParsedExercise]:
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    if not lines:
        return None

    name = _strip_emoji(lines[0])
    if not name:
        return None

    rest_lines = lines[1:]
    set_type = None
    if rest_lines:
        type_match = _TYPE_LINE_RE.match(rest_lines[0])
        if type_match:
            set_type = type_match.group("type").strip()
            rest_lines = rest_lines[1:]

    sets: List[ParsedSet] = []
    for line in rest_lines:
        set_match = _SET_LINE_RE.match(line)
        if not set_match:
            continue
        parsed_set = _parse_set_value(set_match.group("rest"))
        parsed_set.set_number = int(set_match.group("num"))
        sets.append(parsed_set)

    if not sets:
        return None

    return ParsedExercise(
        exercise_name=name,
        exercise_order=order,
        set_type=set_type,
        sets=sets,
    )


def parse_workout_text(text: str) -> ParsedWorkout:
    if not text or not text.strip():
        raise WorkoutParseError(
            "Não foi possível interpretar o treino. "
            "Verifique se o texto está no formato exportado pelo Hevy."
        )

    blocks = _split_blocks(text)
    if not blocks:
        raise WorkoutParseError(
            "Não foi possível interpretar o treino. "
            "Verifique se o texto está no formato exportado pelo Hevy."
        )

    header_lines = [l.strip() for l in blocks[0].splitlines() if l.strip()]
    name = _strip_emoji(header_lines[0]) if header_lines else ""

    workout_date = None
    for line in header_lines[1:]:
        workout_date = _parse_date_line(line)
        if workout_date:
            break
    # Alguns exports colocam nome e data na mesma linha isolada dentro do
    # primeiro bloco — tenta a primeira linha também como fallback.
    if not workout_date and header_lines:
        workout_date = _parse_date_line(header_lines[0])

    source = None
    source_url = None
    body_blocks = blocks[1:]
    if body_blocks and _is_source_block(body_blocks[-1]):
        source_block = body_blocks[-1]
        body_blocks = body_blocks[:-1]
        url_match = _URL_RE.search(source_block)
        if url_match:
            source_url = url_match.group(0).strip()
        if "hevyapp" in source_block.lower() or (source_url and "hevy.com" in source_url.lower()):
            source = "hevy"

    exercises: List[ParsedExercise] = []
    for idx, block in enumerate(body_blocks):
        exercise = _parse_exercise_block(block, order=idx)
        if exercise:
            exercises.append(exercise)

    set_count = sum(len(ex.sets) for ex in exercises)

    if not name or not workout_date or not exercises or set_count == 0:
        raise WorkoutParseError(
            "Não foi possível interpretar o treino. "
            "Verifique se o texto está no formato exportado pelo Hevy."
        )

    return ParsedWorkout(
        name=name,
        workout_date=workout_date,
        source=source,
        source_url=source_url,
        exercises=exercises,
        exercise_count=len(exercises),
        set_count=set_count,
    )
