from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class WasteType(str, Enum):
    GENERAL = "GENERAL"
    RECYCLABLE = "RECYCLABLE"
    ORGANIC = "ORGANIC"
    HAZARDOUS = "HAZARDOUS"


class BinStatus(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"
    MAINTENANCE = "MAINTENANCE"


class SensorHealth(str, Enum):
    OK = "OK"
    ANOMALOUS = "ANOMALOUS"
    STALE = "STALE"
    SPIKE = "SPIKE"
    DRIFT = "DRIFT"
    TILTED = "TILTED"


class VehicleStatus(str, Enum):
    IDLE = "IDLE"
    EN_ROUTE = "EN_ROUTE"
    COLLECTING = "COLLECTING"
    RETURNING_TO_DEPOT = "RETURNING_TO_DEPOT"
    MAINTENANCE = "MAINTENANCE"


class ApprovalStatus(str, Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"


class SensorReading(BaseModel):
    timestamp: str
    fill_pct: float
    weight_kg: float
    battery_pct: float = 95.0
    temperature_c: float = 24.0
    tilt_angle_deg: float = 1.0


class SmartBin(BaseModel):
    id: str
    name: str
    zone: str = "Downtown"
    latitude: float
    longitude: float
    waste_type: WasteType = WasteType.GENERAL
    capacity_kg: float = 150.0
    current_fill_pct: float = 0.0
    current_weight_kg: float = 0.0
    battery_pct: float = 95.0
    temperature_c: float = 24.0
    tilt_angle_deg: float = 0.5
    sensor_health: SensorHealth = SensorHealth.OK
    status: BinStatus = BinStatus.NORMAL
    last_collected_at: Optional[str] = None
    last_reading_at: Optional[str] = None
    predicted_fill_6h: float = 0.0
    predicted_fill_12h: float = 0.0
    predicted_fill_24h: float = 0.0
    hours_to_overflow: float = 48.0
    collection_priority: float = 0.0
    priority_reasons: List[str] = Field(default_factory=list)
    anomaly_flags: List[str] = Field(default_factory=list)
    historical_readings: List[Dict[str, Any]] = Field(default_factory=list)
    recycling_purity_pct: float = 92.0
    contamination_pct: float = 8.0


class Vehicle(BaseModel):
    id: str
    name: str
    model: str = "EcoCompactor 5000"
    status: VehicleStatus = VehicleStatus.IDLE
    latitude: float
    longitude: float
    supported_waste_types: List[WasteType] = Field(
        default_factory=lambda: [WasteType.GENERAL, WasteType.RECYCLABLE]
    )
    max_payload_kg: float = 1200.0
    current_payload_kg: float = 0.0
    fuel_level_pct: float = 88.0
    efficiency_km_per_liter: float = 3.5
    current_route_id: Optional[str] = None


class Depot(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    depot_type: str = "MAIN_DEPOT"


class RouteWaypoint(BaseModel):
    bin_id: Optional[str] = None
    name: str
    latitude: float
    longitude: float
    action: str  # "START_DEPOT", "COLLECT", "END_DEPOT"
    waste_amount_kg: float = 0.0
    cumulative_weight_kg: float = 0.0
    estimated_arrival_minutes: float = 0.0


class VehicleRoute(BaseModel):
    route_id: str
    vehicle_id: str
    vehicle_name: str
    waste_type: WasteType
    waypoints: List[RouteWaypoint] = Field(default_factory=list)
    bin_ids: List[str] = Field(default_factory=list)
    total_distance_km: float = 0.0
    estimated_duration_min: float = 0.0
    total_waste_kg: float = 0.0
    capacity_utilization_pct: float = 0.0


class CollectionPlan(BaseModel):
    plan_id: str
    created_at: str
    status: ApprovalStatus = ApprovalStatus.PENDING_APPROVAL
    routes: List[VehicleRoute] = Field(default_factory=list)
    total_bins_scheduled: int = 0
    total_waste_kg: float = 0.0
    total_distance_km: float = 0.0
    estimated_co2_kg: float = 0.0
    approver_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    critic_review: Optional[Dict[str, Any]] = None


class AgentLogEntry(BaseModel):
    id: str
    timestamp: str
    agent_name: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)
    level: str = "INFO"  # INFO, WARNING, ALERT, SUCCESS


class SensorIngestPayload(BaseModel):
    bin_id: str
    fill_pct: float
    weight_kg: float
    battery_pct: Optional[float] = 95.0
    temperature_c: Optional[float] = 23.0
    tilt_angle_deg: Optional[float] = 1.0
    timestamp: Optional[str] = None


class CVAnalysisRequest(BaseModel):
    bin_id: str
    sample_type: Optional[str] = "mixed_plastics"
    image_base64: Optional[str] = None


class CVAnalysisResponse(BaseModel):
    bin_id: str
    waste_type: str
    detected_items: List[Dict[str, Any]]
    contamination_pct: float
    purity_score_pct: float
    is_contaminated: bool
    recommendation: str
    model_version: str = "YOLOv8-WasteSeg-v2.4"


class PlanActionRequest(BaseModel):
    action: str  # "APPROVE", "REJECT", "MODIFY", "DISPATCH"
    notes: Optional[str] = None
    reviewed_by: Optional[str] = "Operations Lead"
    modified_routes: Optional[List[VehicleRoute]] = None


class DynamicReplanRequest(BaseModel):
    trigger_type: str  # "CRITICAL_BIN", "VEHICLE_BREAKDOWN", "ROUTE_CONGESTION"
    target_bin_id: Optional[str] = None
    failed_vehicle_id: Optional[str] = None
    notes: Optional[str] = None
