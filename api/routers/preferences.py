import traceback

from fastapi import APIRouter, Depends
from middleware.auth_middleware import get_current_user
from models.schemas import PreferencesUpdate
from services.supabase_client import get_service_client

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("")
async def get_preferences(user: dict = Depends(get_current_user)):
    client = get_service_client()
    try:
        result = client.table("user_preferences").select("*").eq("user_id", user["id"]).maybe_single().execute()
    except Exception:
        result = None
    if not result or not result.data:
        return {"user_id": user["id"], "interests": [], "experience_level": "intermediate"}
    return result.data


@router.put("")
async def update_preferences(prefs: PreferencesUpdate, user: dict = Depends(get_current_user)):
    try:
        client = get_service_client()
        data = prefs.model_dump()

        # Check if preferences already exist
        existing = None
        try:
            existing = client.table("user_preferences").select("id").eq("user_id", user["id"]).maybe_single().execute()
        except Exception:
            pass

        if existing and existing.data:
            result = client.table("user_preferences").update(data).eq("user_id", user["id"]).execute()
        else:
            data["user_id"] = user["id"]
            result = client.table("user_preferences").insert(data).execute()

        return result.data[0] if result.data else data
    except Exception as e:
        print(f"Preferences error: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise
