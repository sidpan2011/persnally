from supabase import create_client, Client
from api.config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY


def get_service_client() -> Client:
    """Supabase client with service_role key (bypasses RLS)."""
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_anon_client() -> Client:
    """Supabase client with anon key (respects RLS)."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_user_client(access_token: str) -> Client:
    """Supabase client authenticated as a specific user."""
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    client.auth.set_session(access_token, "")
    return client
