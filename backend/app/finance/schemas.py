from typing import Optional
# IMPORTANTE: importar com alias. Um campo do modelo também se chama "date",
# e o Pydantic v2 resolve as anotações via typing.get_type_hints() usando o
# namespace da própria classe. Como "date: Optional[date] = None" registra um
# atributo de classe "date" (o valor default, None) ANTES da resolução do
# tipo, a anotação "date" era resolvida para esse atributo (None) em vez do
# tipo importado — todo payload com uma data válida quebrava a validação
# com "Input should be None" (o bug do 422 em POST /api/expenses).
from datetime import date as date_type
from pydantic import BaseModel

EXPENSE_TYPES = [
    "Entrada", "Mercado semanal", "Transporte", "Carro", "Manutenção da casa",
    "Lazer", "Saúde", "Pagamento de dívida", "Reserva", "Pessoal",
    "Estudos/Carreira", "Gato", "Comida fora do planejado",
    "Contas recorrentes", "Outros", "Angelo", "Relacionamento",
]


class ExpenseCreate(BaseModel):
    name: str
    type: str
    amount: float
    notes: Optional[str] = None
    date: Optional[date_type] = None


class ExpenseUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    amount: Optional[float] = None
    notes: Optional[str] = None
    date: Optional[date_type] = None
