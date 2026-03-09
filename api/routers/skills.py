"""Skills API - Skill map, gap analysis, and career intelligence."""
import traceback
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from middleware.auth_middleware import get_current_user
from services.supabase_client import get_service_client
from services.career_bridge import run_skill_analysis

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/snapshot")
async def get_latest_snapshot(user: dict = Depends(get_current_user)):
    """Get the most recent skill snapshot for the current user."""
    client = get_service_client()
    result = (
        client.table("skill_snapshots")
        .select("*")
        .eq("user_id", user["id"])
        .order("snapshot_date", desc=True)
        .limit(1)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        return None
    return result.data


@router.get("/history")
async def get_skill_history(user: dict = Depends(get_current_user), limit: int = 10):
    """Get skill snapshots over time for trend visualization."""
    client = get_service_client()
    result = (
        client.table("skill_snapshots")
        .select("id, snapshot_date, skills, languages, domains, experience_level, career_stage, specialization, summary")
        .eq("user_id", user["id"])
        .order("snapshot_date", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data if result and result.data else []


@router.get("/gaps")
async def get_skill_gaps(user: dict = Depends(get_current_user)):
    """Get identified skill gaps."""
    client = get_service_client()
    result = (
        client.table("skill_gaps")
        .select("*")
        .eq("user_id", user["id"])
        .neq("status", "dismissed")
        .order("gap_score", desc=True)
        .execute()
    )
    return result.data if result and result.data else []


@router.patch("/gaps/{gap_id}")
async def update_skill_gap(gap_id: str, body: dict, user: dict = Depends(get_current_user)):
    """Update gap status (learning, achieved, dismissed)."""
    client = get_service_client()
    allowed_statuses = {"identified", "learning", "achieved", "dismissed"}
    new_status = body.get("status")
    if new_status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {allowed_statuses}")

    result = (
        client.table("skill_gaps")
        .update({"status": new_status, "updated_at": "now()"})
        .eq("id", gap_id)
        .eq("user_id", user["id"])
        .execute()
    )
    return result.data[0] if result.data else {"updated": True}


@router.post("/analyze")
async def trigger_skill_analysis(
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """Trigger a fresh skill analysis. Returns a job ID for polling."""
    try:
        client = get_service_client()

        # Check for already-running analysis
        running = None
        try:
            running = (
                client.table("analysis_jobs")
                .select("id")
                .eq("user_id", user["id"])
                .eq("job_type", "skill_analysis")
                .in_("status", ["pending", "running"])
                .maybe_single()
                .execute()
            )
        except Exception:
            pass

        if running and running.data:
            return {"job_id": running.data["id"], "status": "already_running"}

        # Create job
        job = (
            client.table("analysis_jobs")
            .insert({"user_id": user["id"], "job_type": "skill_analysis", "status": "pending"})
            .execute()
        )
        job_id = job.data[0]["id"]

        # Run in background
        background_tasks.add_task(run_skill_analysis, user["id"], job_id)

        return {"job_id": job_id, "status": "pending"}

    except Exception as e:
        print(f"Skill analysis trigger error: {type(e).__name__}: {e}")
        traceback.print_exc()
        raise


@router.get("/analyze/{job_id}")
async def get_analysis_status(job_id: str, user: dict = Depends(get_current_user)):
    """Check the status of a skill analysis job."""
    client = get_service_client()
    try:
        result = (
            client.table("analysis_jobs")
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
    return {
        "id": result.data["id"],
        "status": result.data["status"],
        "job_type": result.data["job_type"],
        "result_summary": result.data.get("result_summary"),
        "error": result.data.get("error"),
        "created_at": result.data["created_at"],
    }
