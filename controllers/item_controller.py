from supabase import Client
from models.item_model import ItemCreate, ItemUpdate
from typing import Optional


class ItemController:

    def __init__(self, db_client: Client):

        self.db = db_client
        self.table_name = "items"


    def _validate_domain(
        self,
        table: str,
        value: str
    ):

        response = (
            self.db
            .table(table)
            .select("name")
            .eq("name", value)
            .execute()
        )

        if not response.data:
            raise Exception(
                f"Valor inválido '{value}' para {table}"
            )


    def create_item(
        self,
        item_data: ItemCreate
    ):

        self._validate_domain(
            "task_groups",
            item_data.grupo
        )

        self._validate_domain(
            "task_categories",
            item_data.categoria
        )

        self._validate_domain(
            "task_statuses",
            item_data.status
        )


        response = (
            self.db
            .table(self.table_name)
            .insert(
                item_data.model_dump()
            )
            .execute()
        )


        if not response.data:
            raise Exception(
                "Erro ao criar tarefa"
            )


        return response.data[0]



    def get_items(
        self,
        grupo: Optional[str] = None,
        status: Optional[str] = None,
        categoria: Optional[str] = None
    ):

        query = (
            self.db
            .table(self.table_name)
            .select("*")
        )


        if grupo:
            query = query.eq(
                "grupo",
                grupo
            )

        if status:
            query = query.eq(
                "status",
                status
            )

        if categoria:
            query = query.eq(
                "categoria",
                categoria
            )


        response = query.execute()

        return response.data



    def get_item(
        self,
        item_id: int
    ):

        response = (
            self.db
            .table(self.table_name)
            .select("*")
            .eq("id", item_id)
            .execute()
        )


        if not response.data:
            raise Exception(
                f"Tarefa {item_id} não encontrada"
            )


        return response.data[0]



    # Status finais que precisam manter items.daily_tasks sincronizados.
    # Roteados pela RPC sync_item_status (ver migration de Tarefas de Hoje),
    # que atualiza items.status e, se existir um registro pendente/em
    # execução em daily_tasks para hoje, sincroniza-o também, na mesma
    # transação do Postgres.
    _FINAL_STATUSES_SYNCED = ("Concluída", "Cancelado")


    def update_item(
        self,
        item_id: int,
        item_data: ItemUpdate
    ):

        data = item_data.model_dump(
            exclude_unset=True
        )


        if "grupo" in data:
            self._validate_domain(
                "task_groups",
                data["grupo"]
            )


        if "categoria" in data:
            self._validate_domain(
                "task_categories",
                data["categoria"]
            )


        if "status" in data:
            self._validate_domain(
                "task_statuses",
                data["status"]
            )


        new_status = data.pop("status", None)
        result_row = None

        if new_status in self._FINAL_STATUSES_SYNCED:
            rpc_response = (
                self.db
                .rpc(
                    "sync_item_status",
                    {
                        "p_item_id": item_id,
                        "p_new_status": new_status
                    }
                )
                .execute()
            )

            rpc_data = rpc_response.data
            if isinstance(rpc_data, list):
                rpc_data = rpc_data[0] if rpc_data else None

            if not rpc_data:
                raise Exception(
                    f"Tarefa {item_id} não encontrada"
                )

            result_row = rpc_data

        elif new_status is not None:
            # Status não-final (ex.: "Preparada" -> "Em andamento" pelo
            # timer): segue o caminho de update normal, sem envolver
            # daily_tasks.
            data["status"] = new_status


        if data:
            response = (
                self.db
                .table(self.table_name)
                .update(data)
                .eq("id", item_id)
                .execute()
            )


            if not response.data:
                raise Exception(
                    f"Tarefa {item_id} não encontrada"
                )


            result_row = response.data[0]


        if result_row is None:
            # Nenhum campo restante para atualizar (ex.: PUT só com status
            # final, já resolvido inteiramente pela RPC acima).
            result_row = self.get_item(item_id)


        return result_row



    def delete_item(
        self,
        item_id: int
    ):

        try:
            response = (
                self.db
                .table(self.table_name)
                .delete()
                .eq("id", item_id)
                .execute()
            )
        except Exception as e:
            # daily_tasks.item_id referencia items(id) ON DELETE RESTRICT:
            # se a tarefa já tiver histórico em Tarefas de Hoje, o Postgres
            # bloqueia a exclusão. Traduzimos o erro cru de FK numa mensagem
            # compreensível, sem alterar a regra em si.
            msg = str(e)
            if "foreign key" in msg.lower() or "23503" in msg:
                raise Exception(
                    "Não é possível excluir: esta tarefa possui histórico "
                    "em Tarefas de Hoje."
                )
            raise


        if not response.data:
            raise Exception(
                f"Tarefa {item_id} não encontrada"
            )


        return True