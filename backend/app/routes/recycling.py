from fastapi import APIRouter
from app.models import CVAnalysisRequest, CVAnalysisResponse
from app.services.cv_classifier import WasteVisionClassifier
from app.database import db
from app.agents.recycling_segregation_agent import RecyclingSegregationAgent

router = APIRouter(prefix="/api/recycling", tags=["Recycling & Computer Vision"])


@router.post("/cv-analyze", response_model=CVAnalysisResponse)
def analyze_waste_sample(payload: CVAnalysisRequest):
    bin_obj = db.get_bin(payload.bin_id)
    waste_type_hint = bin_obj.waste_type.value if bin_obj else None

    result = WasteVisionClassifier.analyze_sample(
        bin_id=payload.bin_id,
        sample_type=payload.sample_type,
        waste_type_hint=waste_type_hint,
    )

    db.log_agent_action(
        agent_name="Recycling & Waste Segregation Agent",
        action="CV_INSPECTION_EXECUTED",
        details={
            "bin_id": payload.bin_id,
            "sample_type": payload.sample_type,
            "detected_items_count": len(result.detected_items),
            "contamination_pct": result.contamination_pct,
            "is_contaminated": result.is_contaminated,
        },
        level="WARNING" if result.is_contaminated else "INFO",
    )

    return result


@router.get("/metrics")
def get_recycling_metrics():
    agent = RecyclingSegregationAgent()
    temp_state = {"bins": db.get_all_bins()}
    state = agent.run(temp_state)
    return state.get("recycling_analytics", {})
