import time
from typing import Any, Dict, List, Optional
from app.database import db, DEPOT
from app.models import CollectionPlan, VehicleStatus
from app.agents.bin_monitoring_agent import BinMonitoringAgent
from app.agents.waste_forecasting_agent import WasteForecastingAgent
from app.agents.collection_priority_agent import CollectionPriorityAgent
from app.agents.vehicle_capacity_agent import VehicleCapacityAgent
from app.agents.route_optimization_agent import RouteOptimizationAgent
from app.agents.recycling_segregation_agent import RecyclingSegregationAgent
from app.agents.operations_critic_agent import OperationsCriticAgent
from app.agents.operations_planning_agent import OperationsPlanningAgent
from app.services.iot_simulator import IoTSensorSimulator


class MultiAgentOrchestrator:
    """
    Coordinates multi-agent AI execution, pipeline flow, and dynamic replanning triggers.
    Orchestrates the 8 specialized agents with shared state, timing telemetry, and HITL lifecycle.
    """

    def __init__(self):
        self.agent_1_monitor = BinMonitoringAgent()
        self.agent_2_forecast = WasteForecastingAgent()
        self.agent_3_priority = CollectionPriorityAgent()
        self.agent_4_capacity = VehicleCapacityAgent()
        self.agent_5_routing = RouteOptimizationAgent()
        self.agent_6_recycling = RecyclingSegregationAgent()
        self.agent_7_critic = OperationsCriticAgent()
        self.agent_8_planning = OperationsPlanningAgent()

    def run_pipeline(self, custom_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Runs the complete end-to-end multi-agent orchestration cycle."""
        state: Dict[str, Any] = custom_state or {
            "bins": db.get_all_bins(),
            "vehicles": db.get_all_vehicles(),
            "depot": db.depot,
            "pipeline_started_at": time.time(),
        }

        pipeline_steps = [
            ("monitoring", self.agent_1_monitor),
            ("forecasting", self.agent_2_forecast),
            ("prioritization", self.agent_3_priority),
            ("capacity", self.agent_4_capacity),
            ("routing", self.agent_5_routing),
            ("recycling", self.agent_6_recycling),
            ("critic", self.agent_7_critic),
            ("planning", self.agent_8_planning),
        ]

        step_telemetry = []

        for step_name, agent in pipeline_steps:
            t0 = time.time()
            try:
                state = agent.run(state)
                duration_ms = round((time.time() - t0) * 1000, 2)
                step_telemetry.append({
                    "step": step_name,
                    "agent": agent.name,
                    "status": "SUCCESS",
                    "duration_ms": duration_ms,
                })
            except Exception as e:
                duration_ms = round((time.time() - t0) * 1000, 2)
                step_telemetry.append({
                    "step": step_name,
                    "agent": agent.name,
                    "status": "ERROR",
                    "error": str(e),
                    "duration_ms": duration_ms,
                })
                # Re-raise or proceed depending on severity
                raise e

        state["pipeline_telemetry"] = step_telemetry
        state["total_pipeline_ms"] = round((time.time() - state["pipeline_started_at"]) * 1000, 2)
        return state

    def trigger_dynamic_replan(
        self,
        trigger_type: str,
        target_bin_id: Optional[str] = None,
        failed_vehicle_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> CollectionPlan:
        """
        Dynamically adjusts states based on real-time operational events and triggers instant replanning:
        - Emergency critical bin overflow
        - Vehicle mechanical breakdown
        - Traffic/congestion route diversion
        """
        db.log_agent_action(
            agent_name="System Orchestrator",
            action="DYNAMIC_REPLAN_TRIGGERED",
            details={
                "trigger_type": trigger_type,
                "target_bin_id": target_bin_id,
                "failed_vehicle_id": failed_vehicle_id,
                "notes": notes,
            },
            level="ALERT",
        )

        # 1. Handle Critical Bin Injection
        if trigger_type == "CRITICAL_BIN" and target_bin_id:
            IoTSensorSimulator.inject_emergency_spike(target_bin_id, target_fill=99.0)

        # 2. Handle Vehicle Breakdown
        if trigger_type == "VEHICLE_BREAKDOWN" and failed_vehicle_id:
            vehicle = db.get_vehicle(failed_vehicle_id)
            if vehicle:
                vehicle.status = VehicleStatus.MAINTENANCE
                vehicle.current_payload_kg = 0.0
                db.update_vehicle(vehicle)
                db.log_agent_action(
                    agent_name="Vehicle & Capacity Management Agent",
                    action="VEHICLE_TAKEN_OFFLINE",
                    details={"vehicle_id": failed_vehicle_id, "reason": "Mechanical failure alert"},
                    level="ALERT",
                )

        # Execute full multi-agent pipeline with updated state
        result_state = self.run_pipeline()
        return result_state["action_plan"]


# Global orchestrator instance
orchestrator = MultiAgentOrchestrator()
