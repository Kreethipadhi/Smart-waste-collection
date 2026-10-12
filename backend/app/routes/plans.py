from fastapi import APIRouter, HTTPException
from app.database import db
from app.models import CollectionPlan, PlanActionRequest, ApprovalStatus, VehicleStatus
from app.agents.orchestrator import orchestrator
from app.services.iot_simulator import IoTSensorSimulator

router = APIRouter(prefix="/api/plans", tags=["Collection Plans & HITL Approvals"])


@router.get("/active", response_model=CollectionPlan)
def get_active_plan():
    if not db.active_plan:
        # Run pipeline once if no plan exists yet
        result = orchestrator.run_pipeline()
        return result["action_plan"]
    return db.active_plan


@router.post("/action")
def act_on_plan(payload: PlanActionRequest):
    if not db.active_plan:
        raise HTTPException(status_code=400, detail="No active plan available to act upon")

    action = payload.action.upper()
    plan = db.active_plan

    if action == "APPROVE":
        plan.status = ApprovalStatus.APPROVED
        plan.reviewed_by = payload.reviewed_by or "Municipal Operations Supervisor"
        plan.approver_notes = payload.notes or "Collection plan approved without alterations."
        db.log_agent_action(
            agent_name="Waste Operations & Action Planning Agent",
            action="HITL_PLAN_APPROVED",
            details={"plan_id": plan.plan_id, "approved_by": plan.reviewed_by, "notes": plan.approver_notes},
            level="SUCCESS",
        )

    elif action == "REJECT":
        plan.status = ApprovalStatus.REJECTED
        plan.reviewed_by = payload.reviewed_by or "Municipal Operations Supervisor"
        plan.approver_notes = payload.notes or "Plan rejected. Replanning required."
        db.log_agent_action(
            agent_name="Waste Operations & Action Planning Agent",
            action="HITL_PLAN_REJECTED",
            details={"plan_id": plan.plan_id, "reason": plan.approver_notes},
            level="ALERT",
        )

    elif action == "MODIFY":
        plan.status = ApprovalStatus.MODIFIED
        if payload.modified_routes:
            plan.routes = payload.modified_routes
            plan.total_bins_scheduled = sum(len(r.bin_ids) for r in plan.routes)
            plan.total_waste_kg = round(sum(r.total_waste_kg for r in plan.routes), 1)
            plan.total_distance_km = round(sum(r.total_distance_km for r in plan.routes), 2)
        plan.reviewed_by = payload.reviewed_by or "Operations Specialist"
        plan.approver_notes = payload.notes or "Plan routes modified manually by supervisor."
        db.log_agent_action(
            agent_name="Waste Operations & Action Planning Agent",
            action="HITL_PLAN_MODIFIED",
            details={"plan_id": plan.plan_id, "notes": plan.approver_notes},
            level="INFO",
        )

    elif action == "DISPATCH":
        # Put fleet in EN_ROUTE / COLLECTING status
        plan.status = ApprovalStatus.EXECUTING
        all_serviced_bins = []
        for r in plan.routes:
            veh = db.get_vehicle(r.vehicle_id)
            if veh:
                veh.status = VehicleStatus.COLLECTING
                veh.current_route_id = r.route_id
                veh.current_payload_kg = r.total_waste_kg
                db.update_vehicle(veh)
            all_serviced_bins.extend(r.bin_ids)

        db.log_agent_action(
            agent_name="Waste Operations & Action Planning Agent",
            action="FLEET_DISPATCHED_TO_ROUTES",
            details={"plan_id": plan.plan_id, "active_routes": len(plan.routes), "total_bins": len(all_serviced_bins)},
            level="SUCCESS",
        )

    elif action == "COMPLETE":
        # Simulates physical completion of collection
        plan.status = ApprovalStatus.COMPLETED
        all_serviced_bins = []
        for r in plan.routes:
            veh = db.get_vehicle(r.vehicle_id)
            if veh:
                veh.status = VehicleStatus.IDLE
                veh.current_route_id = None
                veh.current_payload_kg = 0.0
                db.update_vehicle(veh)
            all_serviced_bins.extend(r.bin_ids)

        # Empty bins in DB
        IoTSensorSimulator.mark_collected(all_serviced_bins)

        db.log_agent_action(
            agent_name="Waste Operations & Action Planning Agent",
            action="DISPATCH_COMPLETED_AND_DEPOT_RETURNED",
            details={"plan_id": plan.plan_id, "bins_cleared": len(all_serviced_bins)},
            level="SUCCESS",
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

    db.active_plan = plan
    return {"message": f"Plan action {action} applied successfully", "plan": plan}
