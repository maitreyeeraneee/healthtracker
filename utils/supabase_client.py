from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None


def get_supabase():
    """Create the Supabase client only when persistence is used."""
    global supabase
    if supabase is None and SUPABASE_URL and SUPABASE_KEY:
        from supabase import create_client

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return supabase


def _clean_payload(payload):
    """Remove unset values so optional Supabase columns can use defaults."""
    return {key: value for key, value in payload.items() if value is not None}


def insert_row(table_name, payload):
    """Best-effort insert that keeps Streamlit UI working if Supabase is unavailable."""
    client = get_supabase()
    if client is None:
        return None
    try:
        return client.table(table_name).insert(_clean_payload(payload)).execute()
    except Exception:
        return None


def upsert_row(table_name, payload, on_conflict=None):
    """Best-effort upsert for profile/target/streak records."""
    client = get_supabase()
    if client is None:
        return None
    try:
        query = client.table(table_name).upsert(_clean_payload(payload), on_conflict=on_conflict)
        return query.execute()
    except Exception:
        return None
