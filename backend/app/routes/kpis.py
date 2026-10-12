from fastapi import APIRouter
from app.database import db
from app.models import BinStatus, VehicleStatus, WasteType

router = APIRouter(prefix="/api/kpis", tags=["KPIs & System Status"])


@router.get("")
def get_kpis():
    bins = db.get_all_bins()
    vehicles = db.get_all_vehicles()
    plan = db.active_plan

    total_bins = len(bins)
    critical_bins = sum(1 for b in bins if b.status == BinStatus.CRITICAL or b.current_fill_pct >= 85.0)
    warning_bins = sum(1 for b in bins if b.status == BinStatus.WARNING or (70.0 <= b.current_fill_pct < 85.0))
    normal_bins = sum(1 for b in bins if b.status == BinStatus.NORMAL and b.current_fill_pct < 70.0)

    # Fleet metrics
    active_fleet = sum(1 for v in vehicles if v.status != VehicleStatus.MAINTENANCE)
    collecting_fleet = sum(1 for v in vehicles if v.status == VehicleStatus.COLLECTING)

    # Weights
    total_waste_in_field = sum(b.current_weight_kg for b in bins)
    recyclable_weight = sum(b.current_weight_kg for b in bins if b.waste_type in (WasteType.RECYCLABLE, WasteType.ORGANIC))
    diversion_rate = (recyclable_weight / total_waste_in_field * 100.0) if total_waste_in_field > 0 else 64.0

    # Recycling purity
    recyclable_bins = [b for b in bins if b.waste_type == WasteType.RECYCLABLE]
    avg_purity = (sum(b.recycling_purity_pct for b in recyclable_bins) / len(recyclable_bins)) if recyclable_bins else 91.0

    return {
        "bins": {
            "total": total_bins,
            "critical": critical_bins,
            "warning": warning_bins,
            "normal": normal_bins,
        },
        "fleet": {
            "total": len(vehicles),
            "active": active_fleet,
            "collecting": collecting_fleet,
        },
        "waste": {
            "total_field_kg": round(total_waste_in_field, 1),
            "diversion_rate_pct": round(diversion_rate, 1),
            "avg_purity_pct": round(avg_purity, 1),
        },
        "active_plan": {
            "plan_id": plan.plan_id if plan else None,
            "status": plan.status.value if plan else "NO_PLAN",
            "scheduled_bins": plan.total_bins_scheduled if plan else 0,
            "total_distance_km": plan.total_distance_km if plan else 0.0,
            "total_waste_kg": plan.total_waste_kg if plan else 0.0,
            "estimated_co2_kg": plan.estimated_co2_kg if plan else 0.0,
        },
    }


@router.post("/reset")
def reset_system_state():
    """Resets database to pristine demo state."""
    db.reset()
    return {"message": "System state reset successfully"}
