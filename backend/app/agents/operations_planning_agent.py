from datetime import datetime, timezone
from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.database import db
from app.models import CollectionPlan, ApprovalStatus, VehicleRoute


class OperationsPlanningAgent(BaseAgent):
    """
    Agent 7: Waste Operations & Action Planning Agent
    Aggregates multi-agent intelligence into an actionable municipal CollectionPlan,
    coordinates the Human-in-the-Loop approval gate, and manages route dispatch.
    """

    def __init__(self):
        super().__init__(
            name="Waste Operations & Action Planning Agent",
            role="Plan Aggregation, HITL Approval Lifecycle Management, and Operational Dispatch",
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        routes: List[VehicleRoute] = state.get("optimized_routes", [])
        critic_review = state.get("critic_review", {})

        now_str = datetime.now(timezone.utc).isoformat()
        total_bins = sum(len(r.bin_ids) for r in routes)
        total_waste = round(sum(r.total_waste_kg for r in routes), 1)
        total_dist = round(sum(r.total_distance_km for r in routes), 2)
        co2_saved = round(state.get("co2_saved_kg", total_dist * 0.45), 2)

        plan_id = f"PLAN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        plan = CollectionPlan(
            plan_id=plan_id,
            created_at=now_str,
            status=ApprovalStatus.PENDING_APPROVAL,
            routes=routes,
            total_bins_scheduled=total_bins,
            total_waste_kg=total_waste,
            total_distance_km=total_dist,
            estimated_co2_kg=co2_saved,
            critic_review=critic_review,
        )

        db.active_plan = plan
        db.plan_history.append(plan)

        self.log(
            action="ACTION_PLAN_SUBMITTED_FOR_HITL",
            details={
                "plan_id": plan_id,
                "status": plan.status.value,
                "scheduled_bins": total_bins,
                "total_routes": len(routes),
                "total_waste_kg": total_waste,
                "co2_saved_kg": co2_saved,
            },
            level="SUCCESS",
        )

        state["action_plan"] = plan
        return state
