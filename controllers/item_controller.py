from supabase import Client
from models.item_model import ItemCreate, ItemUpdate
from typing import Optional

class ItemController:
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table_name = "items"

    def _validate_domain(self, table: str, value: str):
        response = self.db.table(table).select("name").eq("name", value).execute()
        # Se a lista de dados vier vazia, o valor não existe na tabela de domínio
        if not response.data:
            raise Exception(f"Valor inválido '{value}' para a tabela de domínio '{table}'.")

    def create_item(self, item_data: ItemCreate) -> dict:
        # Validando contra as novas tabelas seguras
        self._validate_domain("task_groups", item_data.grupo)
        self._validate_domain("task_categories", item_data.categoria)
        self._validate_domain("task_statuses", item_data.status)

        response = self.db.table(self.table_name).insert(item_data.model_dump()).execute()
        if not response.data:
            raise Exception("Erro ao inserir item no Supabase")
        return response.data[0]

    def get_items(self, grupo: Optional[str] = None, status: Optional[str] = None, categoria: Optional[str] = None) -> list[dict]:
        query = self.db.table(self.table_name).select("*")
        
        if grupo:
            query = query.eq("grupo", grupo)
        if status:
            query = query.eq("status", status)
        if categoria:
            query = query.eq("categoria", categoria)
            
        response = query.execute()
        return response.data

    def update_item(self, item_id: int, item_data: ItemUpdate) -> dict:
        data_dict = item_data.model_dump(exclude_unset=True)
        
        if "grupo" in data_dict:
            self._validate_domain("task_groups", data_dict["grupo"])
        if "categoria" in data_dict:
            self._validate_domain("task_categories", data_dict["categoria"])
        if "status" in data_dict:
            self._validate_domain("task_statuses", data_dict["status"])

        response = self.db.table(self.table_name).update(data_dict).eq("id", item_id).execute()
        if not response.data:
            raise Exception(f"Item com ID {item_id} não encontrado para atualização")
        return response.data[0]

    def delete_item(self, item_id: int) -> bool:
        response = self.db.table(self.table_name).delete().eq("id", item_id).execute()
        if not response.data:
            raise Exception(f"Item com ID {item_id} não encontrado para exclusão")
        return True