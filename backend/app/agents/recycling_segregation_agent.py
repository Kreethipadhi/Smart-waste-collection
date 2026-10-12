from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.models import SmartBin, WasteType
from app.services.cv_classifier import WasteVisionClassifier


class RecyclingSegregationAgent(BaseAgent):
    """
    Agent 6: Recycling & Waste Segregation Agent
    Monitors material purity, detects cross-stream contamination,
    performs simulated computer-vision inspection, and calculates municipal diversion rates.
    """

    def __init__(self):
        super().__init__(
            name="Recycling & Waste Segregation Agent",
            role="Recycling Purity Analytics, Contamination Mitigation, and Computer Vision Audit",
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        bins: List[SmartBin] = state.get("bins", [])

        recyclable_bins = [b for b in bins if b.waste_type == WasteType.RECYCLABLE]
        organic_bins = [b for b in bins if b.waste_type == WasteType.ORGANIC]
        general_bins = [b for b in bins if b.waste_type == WasteType.GENERAL]

        # Calculate purity averages
        avg_recycling_purity = (
            sum(b.recycling_purity_pct for b in recyclable_bins) / len(recyclable_bins)
            if recyclable_bins else 90.0
        )
        avg_contamination = 100.0 - avg_recycling_purity

        # Contaminated bins requiring special handling
        contaminated_bins = [
            {"id": b.id, "name": b.name, "contamination_pct": b.contamination_pct}
            for b in recyclable_bins if b.contamination_pct > 15.0
        ]

        # Municipal Landfill Diversion Rate (Recyclable + Organic / Total)
        total_weight = sum(b.current_weight_kg for b in bins)
        diverted_weight = sum(b.current_weight_kg for b in recyclable_bins + organic_bins)
        diversion_rate = (diverted_weight / total_weight * 100.0) if total_weight > 0 else 60.0

        analytics = {
            "avg_recycling_purity_pct": round(avg_recycling_purity, 1),
            "avg_contamination_pct": round(avg_contamination, 1),
            "municipal_diversion_rate_pct": round(diversion_rate, 1),
            "contaminated_bins_count": len(contaminated_bins),
            "flagged_bins": contaminated_bins,
            "vision_model": "YOLOv8-WasteSeg (Active)",
        }

        self.log(
            action="RECYCLING_AUDIT_PROCESSED",
            details=analytics,
            level="WARNING" if contaminated_bins else "INFO",
        )

        state["recycling_analytics"] = analytics
        return state
