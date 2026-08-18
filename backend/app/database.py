from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY

db: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
