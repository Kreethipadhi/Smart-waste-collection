from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import bins, vehicles, sensors, orchestration, plans, recycling, reports, kpis
from app.agents.orchestrator import orchestrator

app = FastAPI(
    title="Smart Waste Collection & Recycling Optimization System",
    description="Multi-Agent AI Decision Support Platform featuring IoT Telemetry, Ridge ML Forecasting, OR-Tools CVRP, and Human-in-the-Loop Operations",
    version="2.0.0",
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(bins.router)
app.include_router(vehicles.router)
app.include_router(sensors.router)
app.include_router(orchestration.router)
app.include_router(plans.router)
app.include_router(recycling.router)
app.include_router(reports.router)
app.include_router(kpis.router)


@app.on_event("startup")
def startup_event():
    # Pre-run multi-agent pipeline on system boot
    try:
        orchestrator.run_pipeline()
    except Exception as e:
        print(f"Startup multi-agent run warning: {e}")


@app.get("/")
def root():
    return {
        "system": "Agentic AI Smart Waste Collection & Recycling Optimization Platform",
        "status": "OPERATIONAL",
        "version": "2.0.0",
        "docs_url": "/docs",
        "agents_count": 8,
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
