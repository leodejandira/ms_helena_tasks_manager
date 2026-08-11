from supabase import Client
from typing import Optional
from datetime import date, datetime
from zoneinfo import ZoneInfo

from models.daily_task_model import DailyTaskCreate, DailyTaskReorderRequest


# "Hoje" para este sistema é sempre definido no fuso do Brasil, independente
# de onde o servidor (Render) esteja rodando. Usa zoneinfo (stdlib do Python
# 3.9+), sem dependência adicional.
SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def get_today_sao_paulo() -> date:
    return datetime.now(SAO_PAULO_TZ).date()


class DailyTaskController:

    def __init__(self, db_client: Client):
        self.db = db_client
        self.table_name = "daily_tasks"

    def _item_exists(self, item_id: int) -> bool:
        response = (
            self.db
            .table("items")
            .select("id")
            .eq("id", item_id)
            .execute()
        )
        return bool(response.data)

    def _unwrap_rpc(self, response, daily_task_id: int):
        """
        PostgREST sempre envolve o retorno de uma função RPC em uma lista,
        mesmo quando a função retorna uma única linha. Trata os dois formatos
        defensivamente.
        """
        data = response.data

        if not data:
            raise Exception(f"Registro diário {daily_task_id} não encontrado")

        if isinstance(data, list):
            if not data:
                raise Exception(f"Registro diário {daily_task_id} não encontrado")
            return data[0]

        return data

    def create_daily_task(self, data: DailyTaskCreate):
        task_date = data.task_date or get_today_sao_paulo()

        if not self._item_exists(data.item_id):
            raise Exception(f"Tarefa {data.item_id} não encontrada")

        # Adiciona ao final da lista do dia.
        existing = (
            self.db
            .table(self.table_name)
            .select("order_index")
            .eq("task_date", task_date.isoformat())
            .order("order_index", desc=True)
            .limit(1)
            .execute()
        )
        next_order = (existing.data[0]["order_index"] + 1) if existing.data else 0

        payload = {
            "item_id": data.item_id,
            "task_date": task_date.isoformat(),
            "order_index": next_order,
        }

        try:
            response = (
                self.db
                .table(self.table_name)
                .insert(payload)
                .execute()
            )
        except Exception as e:
            msg = str(e)
            if "uq_daily_tasks_item_date" in msg or "duplicate key" in msg.lower():
                raise Exception("Esta tarefa já está nas tarefas de hoje.")
            raise

        if not response.data:
            raise Exception("Erro ao adicionar tarefa às tarefas de hoje")

        return response.data[0]

    def get_daily_tasks(self, task_date: Optional[date] = None):
        target_date = task_date or get_today_sao_paulo()

        response = (
            self.db
            .table(self.table_name)
            .select("*")
            .eq("task_date", target_date.isoformat())
            .order("order_index")
            .execute()
        )

        return response.data

    def delete_daily_task(self, daily_task_id: int):
        """
        Remove apenas a associação diária. Nunca exclui a tarefa original
        em `items` - isso é responsabilidade exclusiva de DELETE /items/{id}.
        """
        response = (
            self.db
            .table(self.table_name)
            .delete()
            .eq("id", daily_task_id)
            .execute()
        )

        if not response.data:
            raise Exception(f"Registro diário {daily_task_id} não encontrado")

        return True

    def reorder_daily_tasks(self, data: DailyTaskReorderRequest):
        task_date = data.task_date
        ids = [item.id for item in data.items]

        if not ids:
            return []

        # Garante que nenhum id pertence a outra data (segurança/validação).
        existing = (
            self.db
            .table(self.table_name)
            .select("id")
            .eq("task_date", task_date.isoformat())
            .in_("id", ids)
            .execute()
        )

        existing_ids = {row["id"] for row in existing.data}
        invalid_ids = [i for i in ids if i not in existing_ids]
        if invalid_ids:
            raise Exception(
                f"IDs inválidos para a data {task_date.isoformat()}: {invalid_ids}"
            )

        updated = []
        for item in data.items:
            response = (
                self.db
                .table(self.table_name)
                .update({"order_index": item.order_index})
                .eq("id", item.id)
                .execute()
            )
            if response.data:
                updated.append(response.data[0])

        return updated

    def complete_daily_task(self, daily_task_id: int):
        """
        Delegado à RPC `complete_daily_task`: atualiza daily_tasks e items
        (quando aplicável) na mesma transação do Postgres. O timestamp é
        gerado pelo servidor (now() dentro da função SQL) - nunca confia
        em timestamp vindo do frontend.
        """
        response = self.db.rpc(
            "complete_daily_task",
            {"p_daily_task_id": daily_task_id}
        ).execute()

        return self._unwrap_rpc(response, daily_task_id)

    def cancel_daily_task(self, daily_task_id: int):
        """
        Delegado à RPC `cancel_daily_task`, mesma lógica de consistência
        atômica de complete_daily_task, para o cenário de cancelamento.
        """
        response = self.db.rpc(
            "cancel_daily_task",
            {"p_daily_task_id": daily_task_id}
        ).execute()

        return self._unwrap_rpc(response, daily_task_id)
