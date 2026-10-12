from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.models import Vehicle, VehicleStatus, SmartBin, WasteType


class VehicleCapacityAgent(BaseAgent):
    """
    Agent 4: Vehicle & Capacity Management Agent
    Monitors fleet telemetry, fuel/battery reserves, payload capacity ceilings,
    and enforces strict waste-stream compatibility matrices.
    """

    def __init__(self):
        super().__init__(
            name="Vehicle & Capacity Management Agent",
            role="Fleet Telemetry, Payload Capacity Enforcement, and Waste Compatibility Mapping",
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        vehicles: List[Vehicle] = state.get("vehicles", [])
        candidates: List[SmartBin] = state.get("candidates_for_dispatch", [])

        # Filter available active vehicles
        available_vehicles = [
            v for v in vehicles
            if v.status in (VehicleStatus.IDLE, VehicleStatus.COLLECTING) and v.fuel_level_pct >= 20.0
        ]

        # Calculate demand payload by waste type
        demand_by_type: Dict[WasteType, float] = {}
        for b in candidates:
            demand_by_type[b.waste_type] = demand_by_type.get(b.waste_type, 0.0) + b.current_weight_kg

        # Calculate fleet capacity by waste type
        capacity_by_type: Dict[WasteType, float] = {}
        for v in available_vehicles:
            for wt in v.supported_waste_types:
                capacity_by_type[wt] = capacity_by_type.get(wt, 0.0) + v.max_payload_kg

        # Check compatibility and capacity feasibility
        feasibility_audit = {}
        for wt, needed_kg in demand_by_type.items():
            avail_kg = capacity_by_type.get(wt, 0.0)
            is_feasible = avail_kg >= needed_kg
            feasibility_audit[wt.value] = {
                "demand_kg": round(needed_kg, 1),
                "fleet_capacity_kg": round(avail_kg, 1),
                "feasible": is_feasible,
                "surplus_margin_kg": round(avail_kg - needed_kg, 1),
            }

        self.log(
            action="FLEET_CAPACITY_EVALUATED",
            details={
                "active_fleet_count": len(available_vehicles),
                "total_demand_kg": round(sum(demand_by_type.values()), 1),
                "compatibility_feasibility": feasibility_audit,
            },
            level="INFO",
        )

        state["available_vehicles"] = available_vehicles
        state["capacity_audit"] = feasibility_audit
        return state
