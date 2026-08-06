import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_db_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Credenciais do Supabase não configuradas no .env")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# Instância única exportada
db = get_db_client()