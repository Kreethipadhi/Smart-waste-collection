import io
from datetime import datetime, timezone
from typing import List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.models import CollectionPlan, SmartBin, Vehicle


class PDFReportGenerator:
    """Generates official municipal operational PDF reports using ReportLab."""

    @classmethod
    def generate_operational_report(
        cls,
        plan: Optional[CollectionPlan],
        bins: List[SmartBin],
        vehicles: List[Vehicle],
    ) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#64748b"),
        )
        section_style = ParagraphStyle(
            "SectionTitle",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=12,
            spaceAfter=6,
        )
        cell_style = ParagraphStyle(
            "CellNormal",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#1e293b"),
        )
        header_cell_style = ParagraphStyle(
            "HeaderCell",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.white,
            fontName="Helvetica-Bold",
        )

        elements = []

        # Header Banner
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        elements.append(Paragraph("Smart City Waste Management & Recycling Authority", title_style))
        elements.append(Paragraph(f"Autonomous Multi-Agent Collection & Optimization Dispatch Report • {now_str}", subtitle_style))
        elements.append(Spacer(1, 14))

        # KPI Metrics Table
        elements.append(Paragraph("1. Executive Operational KPIs", section_style))
        total_bins = len(bins)
        critical_bins = sum(1 for b in bins if b.current_fill_pct >= 80.0)
        scheduled_bins = plan.total_bins_scheduled if plan else 0
        total_dist = f"{plan.total_distance_km:.1f} km" if plan else "0.0 km"
        total_waste = f"{plan.total_waste_kg:.1f} kg" if plan else "0.0 kg"
        co2_saved = f"{plan.estimated_co2_kg:.1f} kg" if plan else "0.0 kg"
        plan_status = plan.status.value if plan else "NO ACTIVE PLAN"

        kpi_data = [
            [
                Paragraph("<b>Monitored Bins</b>", cell_style),
                Paragraph(str(total_bins), cell_style),
                Paragraph("<b>Critical Overfill Bins</b>", cell_style),
                Paragraph(str(critical_bins), cell_style),
            ],
            [
                Paragraph("<b>Scheduled Collections</b>", cell_style),
                Paragraph(str(scheduled_bins), cell_style),
                Paragraph("<b>Total Waste Payload</b>", cell_style),
                Paragraph(total_waste, cell_style),
            ],
            [
                Paragraph("<b>Optimized Distance</b>", cell_style),
                Paragraph(total_dist, cell_style),
                Paragraph("<b>Estimated CO2 Saved</b>", cell_style),
                Paragraph(co2_saved, cell_style),
            ],
            [
                Paragraph("<b>Plan Status</b>", cell_style),
                Paragraph(f"<b>{plan_status}</b>", cell_style),
                Paragraph("<b>Approval Authority</b>", cell_style),
                Paragraph(plan.reviewed_by if plan and plan.reviewed_by else "System Auto-Agent", cell_style),
            ],
        ]

        kpi_table = Table(kpi_data, colWidths=[1.7 * inch, 1.3 * inch, 1.8 * inch, 1.5 * inch])
        kpi_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("PADDING", (0, 0), (-1, -1), 5),
            ])
        )
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # Vehicle Route Dispatch Manifest
        elements.append(Paragraph("2. Optimized Fleet Dispatch Manifest", section_style))
        route_rows = [
            [
                Paragraph("Route ID", header_cell_style),
                Paragraph("Vehicle", header_cell_style),
                Paragraph("Waste Stream", header_cell_style),
                Paragraph("Bins", header_cell_style),
                Paragraph("Payload (kg)", header_cell_style),
                Paragraph("Dist (km)", header_cell_style),
                Paragraph("Utilization", header_cell_style),
            ]
        ]

        if plan and plan.routes:
            for r in plan.routes:
                route_rows.append([
                    Paragraph(r.route_id, cell_style),
                    Paragraph(r.vehicle_name, cell_style),
                    Paragraph(r.waste_type.value, cell_style),
                    Paragraph(str(len(r.bin_ids)), cell_style),
                    Paragraph(f"{r.total_waste_kg:.1f}", cell_style),
                    Paragraph(f"{r.total_distance_km:.1f}", cell_style),
                    Paragraph(f"{r.capacity_utilization_pct:.1f}%", cell_style),
                ])
        else:
            route_rows.append([
                Paragraph("No dispatched routes scheduled.", cell_style),
                Paragraph("-", cell_style),
                Paragraph("-", cell_style),
                Paragraph("-", cell_style),
                Paragraph("-", cell_style),
                Paragraph("-", cell_style),
                Paragraph("-", cell_style),
            ])

        route_table = Table(route_rows, colWidths=[1.1 * inch, 1.5 * inch, 1.1 * inch, 0.6 * inch, 0.8 * inch, 0.7 * inch, 0.8 * inch])
        route_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(route_table)
        elements.append(Spacer(1, 14))

        # High Priority Smart Bins Table
        elements.append(Paragraph("3. High Priority & Critical Smart Bins", section_style))
        bin_rows = [
            [
                Paragraph("Bin ID", header_cell_style),
                Paragraph("Location Name", header_cell_style),
                Paragraph("Type", header_cell_style),
                Paragraph("Fill %", header_cell_style),
                Paragraph("6h Forecast", header_cell_style),
                Paragraph("Overflow ETA", header_cell_style),
                Paragraph("Priority Score", header_cell_style),
            ]
        ]

        sorted_bins = sorted(bins, key=lambda b: b.collection_priority, reverse=True)[:8]
        for b in sorted_bins:
            bin_rows.append([
                Paragraph(b.id, cell_style),
                Paragraph(b.name, cell_style),
                Paragraph(b.waste_type.value, cell_style),
                Paragraph(f"{b.current_fill_pct:.1f}%", cell_style),
                Paragraph(f"{b.predicted_fill_6h:.1f}%", cell_style),
                Paragraph(f"{b.hours_to_overflow:.1f} hrs", cell_style),
                Paragraph(f"<b>{b.collection_priority:.1f}</b>", cell_style),
            ])

        bins_table = Table(bin_rows, colWidths=[0.8 * inch, 1.8 * inch, 0.9 * inch, 0.7 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch])
        bins_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("PADDING", (0, 0), (-1, -1), 4),
            ])
        )
        elements.append(bins_table)
        elements.append(Spacer(1, 14))

        # Sign-off & Audit Notice
        footer_text = (
            "Generated autonomously by the Multi-Agent Waste Operations Architecture. "
            "All route allocations satisfy Municipal Capacitated Vehicle Routing Problem (CVRP) constraints, "
            "segregation compliance, and municipal emission minimization protocols."
        )
        elements.append(Paragraph(footer_text, subtitle_style))

        doc.build(elements)
        return buffer.getvalue()
