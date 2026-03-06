import httpx
from fastapi import APIRouter, Depends, HTTPException
from api.middleware.auth_middleware import get_current_user
from api.services.supabase_client import get_service_client

router = APIRouter(prefix="/github", tags=["github"])


@router.get("/profile")
async def get_github_profile(user: dict = Depends(get_current_user)):
    """Fetch GitHub profile using the user's stored token."""
    client = get_service_client()
    account = (
        client.table("connected_accounts")
        .select("*")
        .eq("user_id", user["id"])
        .eq("provider", "github")
        .maybe_single()
        .execute()
    )
    if not account.data:
        raise HTTPException(status_code=404, detail="GitHub not connected")

    token = account.data["access_token"]
    async with httpx.AsyncClient() as http:
        resp = await http.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="GitHub API error")
        gh_user = resp.json()

    return {
        "username": gh_user.get("login"),
        "name": gh_user.get("name"),
        "avatar_url": gh_user.get("avatar_url"),
        "bio": gh_user.get("bio"),
        "public_repos": gh_user.get("public_repos"),
        "followers": gh_user.get("followers"),
    }


@router.post("/connect")
async def connect_github(body: dict, user: dict = Depends(get_current_user)):
    """Store GitHub connection details after OAuth."""
    client = get_service_client()

    data = {
        "user_id": user["id"],
        "provider": "github",
        "provider_uid": str(body.get("provider_uid", "")),
        "username": body.get("username", ""),
        "access_token": body.get("access_token", ""),
        "scopes": body.get("scopes", []),
    }

    # Upsert
    result = (
        client.table("connected_accounts")
        .upsert(data, on_conflict="user_id,provider")
        .execute()
    )

    return {"connected": True, "username": data["username"]}
