from typing import Dict, List, Optional
from app.models import CVAnalysisResponse, WasteType


SAMPLE_PRESETS = {
    "clean_recyclables": {
        "waste_type": "RECYCLABLE",
        "items": [
            {"label": "PET Bottle (Clear)", "confidence": 0.96, "category": "Plastic #1", "is_contaminant": False},
            {"label": "HDPE Jug (Milk/Detergent)", "confidence": 0.94, "category": "Plastic #2", "is_contaminant": False},
            {"label": "Corrugated Cardboard", "confidence": 0.98, "category": "Paper/Cardboard", "is_contaminant": False},
            {"label": "Aluminum Soda Can", "confidence": 0.95, "category": "Metal", "is_contaminant": False},
        ],
        "contamination_pct": 3.2,
        "purity_score_pct": 96.8,
        "recommendation": "High Purity (Grade A). Route directly to primary optical sorting line at Materials Recovery Facility.",
    },
    "contaminated_plastics": {
        "waste_type": "RECYCLABLE",
        "items": [
            {"label": "PET Water Bottle", "confidence": 0.91, "category": "Plastic #1", "is_contaminant": False},
            {"label": "Greasy Pizza Box (Soiled)", "confidence": 0.93, "category": "Organics Contaminant", "is_contaminant": True},
            {"label": "Lithium-Ion Battery Pack", "confidence": 0.89, "category": "Hazardous Flammable", "is_contaminant": True},
            {"label": "Single-Use Plastic Film Bag", "confidence": 0.87, "category": "Tangler Contaminant", "is_contaminant": True},
        ],
        "contamination_pct": 34.5,
        "purity_score_pct": 65.5,
        "recommendation": "Critical Contamination Alert: Lithium battery and grease present! Divert from standard compactor to manual decontamination sorting.",
    },
    "organic_compost": {
        "waste_type": "ORGANIC",
        "items": [
            {"label": "Fruit Peels & Coffee Grounds", "confidence": 0.97, "category": "Organic Food Waste", "is_contaminant": False},
            {"label": "Yard Clippings", "confidence": 0.92, "category": "Green Waste", "is_contaminant": False},
            {"label": "Styrofoam Container", "confidence": 0.95, "category": "Expanded Polystyrene Contaminant", "is_contaminant": True},
        ],
        "contamination_pct": 8.0,
        "purity_score_pct": 92.0,
        "recommendation": "Standard Composting Grade. Remove Styrofoam container at receiving hopper.",
    },
    "general_municipal": {
        "waste_type": "GENERAL",
        "items": [
            {"label": "Mixed Composite Wrapper", "confidence": 0.88, "category": "Non-Recyclable", "is_contaminant": False},
            {"label": "Sanitary Tissue Waste", "confidence": 0.91, "category": "Municipal Solid", "is_contaminant": False},
            {"label": "Unsorted Municipal Debris", "confidence": 0.86, "category": "General Residual", "is_contaminant": False},
        ],
        "contamination_pct": 0.0,
        "purity_score_pct": 100.0,
        "recommendation": "Standard General Waste. Proceed to Waste-to-Energy or sanitary landfill stream.",
    },
}


class WasteVisionClassifier:
    """
    Simulates AI Computer Vision model (YOLOv8-WasteSeg / ViT) for automated waste classification,
    contamination detection, and material purity scoring.
    """

    @classmethod
    def analyze_sample(
        cls,
        bin_id: str,
        sample_type: Optional[str] = None,
        waste_type_hint: Optional[str] = None,
    ) -> CVAnalysisResponse:
        key = sample_type or "clean_recyclables"
        if key not in SAMPLE_PRESETS:
            if waste_type_hint == "ORGANIC":
                key = "organic_compost"
            elif waste_type_hint == "GENERAL":
                key = "general_municipal"
            elif waste_type_hint == "RECYCLABLE":
                key = "clean_recyclables"
            else:
                key = "clean_recyclables"

        data = SAMPLE_PRESETS[key]
        is_contaminated = data["contamination_pct"] > 15.0

        return CVAnalysisResponse(
            bin_id=bin_id,
            waste_type=data["waste_type"],
            detected_items=data["items"],
            contamination_pct=data["contamination_pct"],
            purity_score_pct=data["purity_score_pct"],
            is_contaminated=is_contaminated,
            recommendation=data["recommendation"],
            model_version="YOLOv8-WasteSeg-v2.4",
        )
