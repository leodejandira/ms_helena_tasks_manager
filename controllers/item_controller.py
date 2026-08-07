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


        return response.data[0]



    def delete_item(
        self,
        item_id: int
    ):

        response = (
            self.db
            .table(self.table_name)
            .delete()
            .eq("id", item_id)
            .execute()
        )


        if not response.data:
            raise Exception(
                f"Tarefa {item_id} não encontrada"
            )


        return True