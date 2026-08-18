import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
PORT = int(os.getenv("PORT", "8000"))

if not SUPABASE_URL or not SUPABASE_KEY:
    # Não derruba a aplicação, mas deixa claro no log que falta configuração.
    print("AVISO: SUPABASE_URL e/ou SUPABASE_KEY não configurados no .env")
