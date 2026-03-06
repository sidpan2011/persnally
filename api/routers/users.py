from fastapi import APIRouter, Depends
from api.middleware.auth_middleware import get_current_user
from api.models.schemas import UserUpdate
from api.services.supabase_client import get_service_client

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    client = get_service_client()
    result = client.table("users").select("*").eq("id", user["id"]).single().execute()
    return result.data


@router.patch("/me")
async def update_me(update: UserUpdate, user: dict = Depends(get_current_user)):
    client = get_service_client()
    data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not data:
        return {"message": "No fields to update"}
    result = client.table("users").update(data).eq("id", user["id"]).execute()
    return result.data[0] if result.data else {"message": "Updated"}
