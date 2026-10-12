from typing import Optional
from fastapi import APIRouter
from app.agents.orchestrator import orchestrator
from app.database import db
from app.models import DynamicReplanRequest

router = APIRouter(prefix="/api/agents", tags=["Multi-Agent Orchestration"])


@router.post("/run")
def run_multi_agent_pipeline():
    """Executes the complete 8-agent AI decision pipeline."""
    result = orchestrator.run_pipeline()
    return {
        "status": "COMPLETED",
        "total_duration_ms": result.get("total_pipeline_ms", 0.0),
        "telemetry": result.get("pipeline_telemetry", []),
        "plan_id": result.get("action_plan").plan_id if result.get("action_plan") else None,
        "critic_evaluation": result.get("critic_review", {}),
        "scheduled_bins": result.get("action_plan").total_bins_scheduled if result.get("action_plan") else 0,
    }


@router.get("/logs")
def get_agent_audit_logs(limit: int = 50):
    """Retrieves real-time execution logs and reasoning trails across all agents."""
    return db.get_logs(limit=limit)


@router.post("/replan")
def trigger_dynamic_replanning(payload: DynamicReplanRequest):
    """Dynamically replans collection routes in response to an edge event."""
    new_plan = orchestrator.trigger_dynamic_replan(
        trigger_type=payload.trigger_type,
        target_bin_id=payload.target_bin_id,
        failed_vehicle_id=payload.failed_vehicle_id,
        notes=payload.notes,
    )
    return {
        "message": "Dynamic replan executed successfully",
        "trigger": payload.trigger_type,
        "plan": new_plan,
    }
