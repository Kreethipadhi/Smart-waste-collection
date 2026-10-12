from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.models import SmartBin, WasteType, SensorHealth


class CollectionPriorityAgent(BaseAgent):
    """
    Agent 3: Collection Priority Agent
    Calculates multi-criteria priority scores (0-100) combining real-time fill level,
    predicted overflow risk, waste-type degradation characteristics (odor/health),
    and hardware health metrics with explainable rationale.
    """

    def __init__(self):
        super().__init__(
            name="Collection Priority Agent",
            role="Multi-Criteria Collection Prioritization and Explainable Urgency Scoring",
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        bins: List[SmartBin] = state.get("bins", [])
        prioritized_bins: List[SmartBin] = []
        high_urgency_list: List[Dict[str, Any]] = []

        for b in bins:
            reasons = []
            score = 0.0

            # 1. Base Fill Level Component (up to 50 pts)
            fill_component = (b.current_fill_pct / 100.0) * 50.0
            score += fill_component

            # Direct Critical Threshold Bonus
            if b.current_fill_pct >= 85.0:
                score += 25.0
                reasons.append(f"Severe fill level ({b.current_fill_pct:.1f}% >= 85%)")
            elif b.current_fill_pct >= 70.0:
                score += 15.0
                reasons.append(f"Elevated fill level ({b.current_fill_pct:.1f}%)")

            # 2. Predictive Urgency Component (up to 20 pts)
            if b.hours_to_overflow <= 6.0:
                score += 20.0
                reasons.append(f"Imminent overflow within {b.hours_to_overflow:.1f} hours")
            elif b.hours_to_overflow <= 12.0:
                score += 12.0
                reasons.append(f"Projected overflow in {b.hours_to_overflow:.1f} hours")
            elif b.hours_to_overflow <= 24.0:
                score += 6.0

            # 3. Waste Type Sensitivity Component (up to 15 pts)
            if b.waste_type == WasteType.HAZARDOUS:
                score += 15.0
                reasons.append("Hazardous waste: strict municipal safety protocol")
            elif b.waste_type == WasteType.ORGANIC:
                score += 12.0
                reasons.append("Organic waste: decomposition and odor risk escalation")
            elif b.waste_type == WasteType.RECYCLABLE:
                score += 6.0
            else:
                score += 4.0

            # 4. Hardware Anomaly / Tilt Component (up to 15 pts)
            if b.sensor_health == SensorHealth.TILTED:
                score += 15.0
                reasons.append("Bin physical tilt / rollover detected")
            elif b.sensor_health == SensorHealth.ANOMALOUS:
                score += 12.0
                reasons.append("Thermal/Sensor telemetry anomaly flagged")

            final_score = round(min(100.0, max(0.0, score)), 1)
            b.collection_priority = final_score
            b.priority_reasons = reasons

            prioritized_bins.append(b)

            # Collection dispatch candidate threshold
            if final_score >= 50.0 or b.current_fill_pct >= 75.0:
                high_urgency_list.append({
                    "id": b.id,
                    "name": b.name,
                    "score": final_score,
                    "fill_pct": b.current_fill_pct,
                    "waste_type": b.waste_type.value,
                    "reasons": reasons,
                })

        # Sort candidate bins in descending priority
        prioritized_bins.sort(key=lambda x: x.collection_priority, reverse=True)
        high_urgency_list.sort(key=lambda x: x["score"], reverse=True)

        self.log(
            action="PRIORITIZATION_COMPLETED",
            details={
                "evaluated_bins": len(prioritized_bins),
                "candidates_for_dispatch": len(high_urgency_list),
                "top_candidate": high_urgency_list[0] if high_urgency_list else None,
            },
            level="INFO",
        )

        state["bins"] = prioritized_bins
        state["candidates_for_dispatch"] = [b for b in prioritized_bins if b.collection_priority >= 50.0 or b.current_fill_pct >= 75.0]
        return state
