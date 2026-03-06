import traceback
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from api.middleware.auth_middleware import get_current_user
from api.models.schemas import GenerateResponse, JobStatus
from api.services.supabase_client import get_service_client
from api.services.engine_bridge import run_generation_for_user

router = APIRouter(prefix="/newsletters", tags=["newsletters"])


@router.get("")
async def list_newsletters(user: dict = Depends(get_current_user), limit: int = 20, offset: int = 0):
    client = get_service_client()
    result = (
        client.table("newsletters")
        .select("id, subject, headline, status, quality_score, sent_at, items")
        .eq("user_id", user["id"])
        .order("sent_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    newsletters = []
    for n in (result.data if result and result.data else []):
        newsletters.append({
            **n,
            "item_count": len(n.get("items", [])),
        })
    return newsletters


@router.get("/generate/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, user: dict = Depends(get_current_user)):
    client = get_service_client()
    try:
        result = (
            client.table("generation_jobs")
            .select("*")
            .eq("id", job_id)
            .eq("user_id", user["id"])
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatus(
        id=result.data["id"],
        status=result.data["status"],
        newsletter_id=result.data.get("newsletter_id"),
        error=result.data.get("error"),
        created_at=result.data["created_at"],
    )


@router.post("/generate", response_model=GenerateResponse)
async def generate_newsletter(background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    try:
        client = get_service_client()

        # Check for already-running job
        running = None
        try:
            running = (
                client.table("generation_jobs")
                .select("id")
                .eq("user_id", user["id"])
                .in_("status", ["pending", "running"])
                .maybe_single()
                .execute()
            )
        except Exception:
            pass

        if running and running.data:
            return GenerateResponse(job_id=running.data["id"], status="already_running")

        # Create job
        job = (
            client.table("generation_jobs")
            .insert({"user_id": user["id"], "status": "pending"})
            .execute()
        )
        job_id = job.data[0]["id"]

        # Run in background
        background_tasks.add_task(run_generation_for_user, user["id"], job_id)

        return GenerateResponse(job_id=job_id, status="pending")
    except Exception as e:
        print(f"Generate error: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise


@router.get("/{newsletter_id}")
async def get_newsletter(newsletter_id: str, user: dict = Depends(get_current_user)):
    client = get_service_client()
    try:
        result = (
            client.table("newsletters")
            .select("*")
            .eq("id", newsletter_id)
            .eq("user_id", user["id"])
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Newsletter not found")
    return result.data
