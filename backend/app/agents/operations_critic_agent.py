from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.models import CollectionPlan, SmartBin, VehicleRoute


class OperationsCriticAgent(BaseAgent):
    """
    Agent 8: Operations Reviewer & Critic Agent
    Autonomous validator acting as the safety and compliance watchdog.
    Verifies that generated collection plans respect vehicle weight ratings,
    fulfill critical SLA requirements, and flags any schedule anomalies
    prior to Human-in-the-Loop review.
    """

    def __init__(self):
        super().__init__(
            name="Operations Reviewer / Critic Agent",
            role="Plan Validation, SLA Compliance Verification, and Replanning Triggers",
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        routes: List[VehicleRoute] = state.get("optimized_routes", [])
        bins: List[SmartBin] = state.get("bins", [])
        vehicles = {v.id: v for v in state.get("vehicles", [])}

        critical_bins = [b for b in bins if b.current_fill_pct >= 85.0]
        scheduled_bin_ids = set()
        for r in routes:
            scheduled_bin_ids.update(r.bin_ids)

        violations = []
        warnings = []
        passes = []

        # 1. Capacity Overload Check
        for r in routes:
            veh = vehicles.get(r.vehicle_id)
            if veh:
                if r.total_waste_kg > veh.max_payload_kg:
                    violations.append(
                        f"OVERLOAD_VIOLATION: Route {r.route_id} assigns {r.total_waste_kg}kg exceeding vehicle {veh.name} rating ({veh.max_payload_kg}kg)"
                    )
                else:
                    passes.append(f"Route {r.route_id}: Payload {r.total_waste_kg}kg <= {veh.max_payload_kg}kg safe.")

        # 2. Critical Bin Coverage SLA Check
        missed_critical = [b for b in critical_bins if b.id not in scheduled_bin_ids]
        if missed_critical:
            warnings.append(
                f"SLA_WARNING: {len(missed_critical)} critical bins (>85% fill) unserviced in current cycle: {[b.id for b in missed_critical]}"
            )
        else:
            passes.append("100% of critical threshold bins scheduled for collection.")

        # 3. Route Duration Safety Check
        for r in routes:
            if r.estimated_duration_min > 240.0:
                warnings.append(f"FATIGUE_WARNING: Route {r.route_id} estimated at {r.estimated_duration_min:.0f} mins (>4 hrs).")
            else:
                passes.append(f"Route {r.route_id} within driver shift window ({r.estimated_duration_min:.0f} mins).")

        is_approved_by_critic = len(violations) == 0
        critic_score = max(0, 100 - (len(violations) * 35) - (len(warnings) * 10))

        review = {
            "critic_score": critic_score,
            "is_valid": is_approved_by_critic,
            "violations": violations,
            "warnings": warnings,
            "checks_passed": passes,
            "recommendation": "Ready for Human Approval" if is_approved_by_critic else "Auto-Replanning Triggered",
        }

        self.log(
            action="CRITIC_PLAN_AUDIT",
            details={
                "critic_score": critic_score,
                "passed": is_approved_by_critic,
                "violations_count": len(violations),
                "warnings_count": len(warnings),
            },
            level="SUCCESS" if is_approved_by_critic else "ALERT",
        )

        state["critic_review"] = review
        return state
