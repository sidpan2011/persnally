from fastapi import Request, HTTPException
from api.services.supabase_client import get_service_client
import traceback


async def get_current_user(request: Request) -> dict:
    """Extract and verify user from Supabase JWT in Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.removeprefix("Bearer ")
    client = get_service_client()

    try:
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {
            "id": str(user_response.user.id),
            "email": user_response.user.email,
            "token": token,
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth error: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=f"Authentication failed: {type(e).__name__}")
