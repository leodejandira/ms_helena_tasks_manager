"""
Utilitários de timezone compartilhados por todos os módulos (tasks, habits,
finance, workouts).

Contexto do bug corrigido aqui:
- O código antigo usava `datetime.utcnow().isoformat()` (naive, sem
  informação de fuso) para `created_at`/`updated_at`. Uma string ISO sem
  offset pode ser reinterpretada como horário LOCAL por quem a lê (o
  Postgres, o navegador via `new Date(...)`, etc.), deslocando o instante
  gravado por até 3 horas.
- O código antigo também usava `date.today()` (data do fuso do SERVIDOR) em
  vez da data do fuso do usuário. O Render roda os containers em UTC, então
  entre 21h e 23:59 no horário de Brasília (`America/Sao_Paulo`, UTC-3) já é
  o dia seguinte em UTC — qualquer registro feito nesse período (tarefa,
  hábito, gasto, treino) era salvo com a data de amanhã.

Regra geral adotada no projeto a partir desta correção:
- Instantes (quando algo aconteceu) -> sempre timezone-aware em UTC,
  serializados com offset explícito (`now_utc_iso`).
- Dias de calendário (quando é "hoje" para o usuário, ou a data de um
  treino) -> sempre calculados no fuso `America/Sao_Paulo`
  (`today_local` / `today_local_str`), nunca com `date.today()` puro nem
  derivados de uma conversão para UTC que possa cruzar a meia-noite.
"""

from datetime import datetime, date as date_type
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Sao_Paulo")
UTC_TZ = ZoneInfo("UTC")


def now_utc_iso() -> str:
    """Instante atual em UTC, com offset explícito (+00:00).

    Usar sempre no lugar de `datetime.utcnow().isoformat()` para colunas de
    instante (`created_at`, `updated_at`, `completed_at`, etc.)."""
    return datetime.now(UTC_TZ).isoformat()


def today_local() -> date_type:
    """Data de calendário 'hoje' no fuso America/Sao_Paulo.

    Usar sempre no lugar de `date.today()` puro para qualquer 'dia de hoje'
    visível ao usuário (prancheta do dia, hábitos do dia, gasto sem data
    informada, etc.), já que o servidor roda em UTC."""
    return datetime.now(LOCAL_TZ).date()


def today_local_str() -> str:
    return today_local().isoformat()


def to_local(dt: datetime) -> datetime:
    """Converte um datetime para America/Sao_Paulo.

    Se `dt` não tiver timezone (naive), assume que já está em UTC antes de
    converter — nunca assume horário local do servidor."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC_TZ)
    return dt.astimezone(LOCAL_TZ)


def local_datetime(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    """Constrói um datetime já ciente do fuso America/Sao_Paulo a partir de
    componentes soltos (ex.: extraídos de um texto de treino do Hevy).

    Importante: para obter a DATA de calendário (dia) a partir do resultado,
    use `.date()` diretamente neste datetime local — nunca converta para UTC
    primeiro, pois isso pode empurrar o dia para frente ou para trás."""
    return datetime(year, month, day, hour, minute, second, tzinfo=LOCAL_TZ)
