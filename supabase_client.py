"""
Client pro supabase
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
SECRET_ACCESS_KEY = os.environ.get("SECRET_ACCESS_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Vyhodíme chybu při startu – aspoň hned víš, že chybí proměnné
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase_anon: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_service: Client = create_client(SUPABASE_URL, SECRET_ACCESS_KEY)

