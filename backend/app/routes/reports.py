from fastapi import APIRouter
from fastapi.responses import Response
from app.database import db
from app.services.pdf_generator import PDFReportGenerator
from app.agents.orchestrator import orchestrator

router = APIRouter(prefix="/api/reports", tags=["Operational PDF Reports"])


@router.get("/pdf")
def download_pdf_report():
    plan = db.active_plan
    if not plan:
        res = orchestrator.run_pipeline()
        plan = res.get("action_plan")

    bins = db.get_all_bins()
    vehicles = db.get_all_vehicles()

    pdf_bytes = PDFReportGenerator.generate_operational_report(
        plan=plan,
        bins=bins,
        vehicles=vehicles,
    )

    db.log_agent_action(
        agent_name="System Orchestrator",
        action="OPERATIONAL_PDF_GENERATED",
        details={"plan_id": plan.plan_id if plan else None, "file_size_bytes": len(pdf_bytes)},
        level="INFO",
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=SmartWaste_Operations_Report_{plan.plan_id if plan else 'latest'}.pdf"
        },
    )
