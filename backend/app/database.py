import copy
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from app.models import (
    SmartBin,
    WasteType,
    BinStatus,
    SensorHealth,
    Vehicle,
    VehicleStatus,
    Depot,
    CollectionPlan,
    ApprovalStatus,
    AgentLogEntry,
)

# Coordinates center around a representative metropolitan district (San Francisco Downtown / Financial / Waterfront)
DEPOT = Depot(
    id="DEPOT-01",
    name="Central City Eco-Depot & Fleet Hub",
    latitude=37.7840,
    longitude=-122.4010,
    depot_type="MAIN_DEPOT",
)

RECYCLING_PLANT = Depot(
    id="DEPOT-02",
    name="Bay Area Materials Recovery Facility (MRF)",
    latitude=37.7910,
    longitude=-122.3920,
    depot_type="RECYCLING_PLANT",
)

INITIAL_VEHICLES = [
    Vehicle(
        id="VEH-101",
        name="EcoCompactor Alpha (General)",
        model="Volvo FE Electric 27t",
        status=VehicleStatus.IDLE,
        latitude=37.7840,
        longitude=-122.4010,
        supported_waste_types=[WasteType.GENERAL],
        max_payload_kg=1200.0,
        current_payload_kg=0.0,
        fuel_level_pct=92.0,
        efficiency_km_per_liter=4.2,
    ),
    Vehicle(
        id="VEH-102",
        name="CleanStream Beta (Recyclables)",
        model="Mack LR Electric",
        status=VehicleStatus.IDLE,
        latitude=37.7840,
        longitude=-122.4010,
        supported_waste_types=[WasteType.RECYCLABLE],
        max_payload_kg=950.0,
        current_payload_kg=0.0,
        fuel_level_pct=88.0,
        efficiency_km_per_liter=4.0,
    ),
    Vehicle(
        id="VEH-103",
        name="BioHauler Gamma (Organics)",
        model="BYD 8R Heavy Truck",
        status=VehicleStatus.IDLE,
        latitude=37.7840,
        longitude=-122.4010,
        supported_waste_types=[WasteType.ORGANIC],
        max_payload_kg=800.0,
        current_payload_kg=0.0,
        fuel_level_pct=76.0,
        efficiency_km_per_liter=3.8,
    ),
    Vehicle(
        id="VEH-104",
        name="SafeGuard Delta (Hazardous / Multi)",
        model="Isuzu NRR Clean Diesel",
        status=VehicleStatus.IDLE,
        latitude=37.7840,
        longitude=-122.4010,
        supported_waste_types=[WasteType.HAZARDOUS, WasteType.GENERAL],
        max_payload_kg=650.0,
        current_payload_kg=0.0,
        fuel_level_pct=95.0,
        efficiency_km_per_liter=5.0,
    ),
]

def generate_historical_series(base_fill: float, base_weight: float, trend: float = 2.0) -> List[Dict]:
    now = datetime.now(timezone.utc)
    series = []
    for h in range(24, 0, -2):
        ts = (now - timedelta(hours=h)).isoformat()
        # back-calculate realistic progressive fill
        fill = max(5.0, min(100.0, base_fill - (h * trend * 0.7)))
        wt = max(5.0, min(150.0, base_weight * (fill / max(1.0, base_fill))))
        series.append({
            "timestamp": ts,
            "fill_pct": round(fill, 1),
            "weight_kg": round(wt, 1),
            "battery_pct": 96.0 - (h * 0.1),
            "temperature_c": round(21.0 + (fill * 0.05), 1),
            "tilt_angle_deg": 0.8
        })
    return series

INITIAL_BINS = [
    # General Waste Bins
    SmartBin(
        id="BIN-001",
        name="Market St Plaza General",
        zone="Downtown Commercial",
        latitude=37.7892,
        longitude=-122.4014,
        waste_type=WasteType.GENERAL,
        capacity_kg=150.0,
        current_fill_pct=92.5,
        current_weight_kg=138.0,
        status=BinStatus.CRITICAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(92.5, 138.0, trend=3.2),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=70.0,
        contamination_pct=30.0,
    ),
    SmartBin(
        id="BIN-002",
        name="Powell St Station General",
        zone="Downtown Transit",
        latitude=37.7844,
        longitude=-122.4079,
        waste_type=WasteType.GENERAL,
        capacity_kg=160.0,
        current_fill_pct=88.0,
        current_weight_kg=140.0,
        status=BinStatus.CRITICAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(88.0, 140.0, trend=2.8),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=65.0,
        contamination_pct=35.0,
    ),
    SmartBin(
        id="BIN-003",
        name="Union Square North General",
        zone="Retail District",
        latitude=37.7880,
        longitude=-122.4075,
        waste_type=WasteType.GENERAL,
        capacity_kg=150.0,
        current_fill_pct=78.5,
        current_weight_kg=117.0,
        status=BinStatus.WARNING,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(78.5, 117.0, trend=2.5),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=75.0,
        contamination_pct=25.0,
    ),
    SmartBin(
        id="BIN-004",
        name="Embarcadero Promenade General",
        zone="Waterfront",
        latitude=37.7955,
        longitude=-122.3937,
        waste_type=WasteType.GENERAL,
        capacity_kg=150.0,
        current_fill_pct=42.0,
        current_weight_kg=63.0,
        status=BinStatus.NORMAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(42.0, 63.0, trend=1.1),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=80.0,
        contamination_pct=20.0,
    ),

    # Recyclable Waste Bins
    SmartBin(
        id="BIN-005",
        name="Salesforce Park Recyclable",
        zone="Tech Campus",
        latitude=37.7897,
        longitude=-122.3969,
        waste_type=WasteType.RECYCLABLE,
        capacity_kg=120.0,
        current_fill_pct=89.0,
        current_weight_kg=106.0,
        status=BinStatus.CRITICAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(89.0, 106.0, trend=3.5),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=94.5,
        contamination_pct=5.5,
    ),
    SmartBin(
        id="BIN-006",
        name="Financial Tower Plaza Recyclable",
        zone="Downtown Commercial",
        latitude=37.7925,
        longitude=-122.4005,
        waste_type=WasteType.RECYCLABLE,
        capacity_kg=120.0,
        current_fill_pct=84.0,
        current_weight_kg=98.0,
        status=BinStatus.CRITICAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(84.0, 98.0, trend=2.7),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=91.0,
        contamination_pct=9.0,
    ),
    SmartBin(
        id="BIN-007",
        name="Ferry Building Recyclable",
        zone="Waterfront",
        latitude=37.7958,
        longitude=-122.3918,
        waste_type=WasteType.RECYCLABLE,
        capacity_kg=130.0,
        current_fill_pct=72.0,
        current_weight_kg=85.0,
        status=BinStatus.WARNING,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(72.0, 85.0, trend=2.0),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=88.0,
        contamination_pct=12.0,
    ),
    SmartBin(
        id="BIN-008",
        name="Howard St Tech Hub Recyclable",
        zone="Tech Campus",
        latitude=37.7865,
        longitude=-122.3980,
        waste_type=WasteType.RECYCLABLE,
        capacity_kg=120.0,
        current_fill_pct=35.0,
        current_weight_kg=40.0,
        status=BinStatus.NORMAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(35.0, 40.0, trend=0.9),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=96.0,
        contamination_pct=4.0,
    ),

    # Organic Waste Bins
    SmartBin(
        id="BIN-009",
        name="Mission Food Hall Organics",
        zone="Culinary District",
        latitude=37.7818,
        longitude=-122.4055,
        waste_type=WasteType.ORGANIC,
        capacity_kg=140.0,
        current_fill_pct=94.0,
        current_weight_kg=131.0,
        status=BinStatus.CRITICAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(94.0, 131.0, trend=4.1),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=95.0,
        contamination_pct=5.0,
    ),
    SmartBin(
        id="BIN-010",
        name="Yerba Buena Gardens Organics",
        zone="Cultural District",
        latitude=37.7860,
        longitude=-122.4025,
        waste_type=WasteType.ORGANIC,
        capacity_kg=140.0,
        current_fill_pct=81.0,
        current_weight_kg=110.0,
        status=BinStatus.CRITICAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(81.0, 110.0, trend=2.6),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=93.0,
        contamination_pct=7.0,
    ),
    SmartBin(
        id="BIN-011",
        name="Civic Center Cafe Organics",
        zone="Civic Center",
        latitude=37.7795,
        longitude=-122.4130,
        waste_type=WasteType.ORGANIC,
        capacity_kg=140.0,
        current_fill_pct=48.0,
        current_weight_kg=65.0,
        status=BinStatus.NORMAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(48.0, 65.0, trend=1.5),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=91.0,
        contamination_pct=9.0,
    ),

    # Hazardous & Specialized Bins
    SmartBin(
        id="BIN-012",
        name="SOMA Health Clinic Hazardous",
        zone="Medical District",
        latitude=37.7780,
        longitude=-122.4040,
        waste_type=WasteType.HAZARDOUS,
        capacity_kg=80.0,
        current_fill_pct=86.0,
        current_weight_kg=68.0,
        status=BinStatus.CRITICAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(86.0, 68.0, trend=1.8),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=99.0,
        contamination_pct=1.0,
    ),

    # Anomaly Demo Bins (Sensor anomaly, stale data, tilt)
    SmartBin(
        id="BIN-013",
        name="2nd St Corridor (Spike Anomaly)",
        zone="Commercial",
        latitude=37.7875,
        longitude=-122.3995,
        waste_type=WasteType.GENERAL,
        capacity_kg=150.0,
        current_fill_pct=15.0,
        current_weight_kg=22.0,
        status=BinStatus.NORMAL,
        sensor_health=SensorHealth.OK,
        historical_readings=generate_historical_series(15.0, 22.0, trend=0.5),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=80.0,
        contamination_pct=20.0,
    ),
    SmartBin(
        id="BIN-014",
        name="Folsom St Battery/Tilt Warning",
        zone="South of Market",
        latitude=37.7820,
        longitude=-122.3990,
        waste_type=WasteType.RECYCLABLE,
        capacity_kg=120.0,
        current_fill_pct=55.0,
        current_weight_kg=65.0,
        battery_pct=14.0,  # low battery flag
        tilt_angle_deg=22.5,  # tilt warning
        status=BinStatus.WARNING,
        sensor_health=SensorHealth.TILTED,
        historical_readings=generate_historical_series(55.0, 65.0, trend=1.0),
        last_reading_at=datetime.now(timezone.utc).isoformat(),
        recycling_purity_pct=89.0,
        contamination_pct=11.0,
    ),
]


class DatabaseStore:
    def __init__(self):
        self.depot = copy.deepcopy(DEPOT)
        self.recycling_plant = copy.deepcopy(RECYCLING_PLANT)
        self.bins: Dict[str, SmartBin] = {b.id: copy.deepcopy(b) for b in INITIAL_BINS}
        self.vehicles: Dict[str, Vehicle] = {v.id: copy.deepcopy(v) for v in INITIAL_VEHICLES}
        self.active_plan: Optional[CollectionPlan] = None
        self.agent_logs: List[AgentLogEntry] = []
        self.plan_history: List[CollectionPlan] = []
        self._init_seed_log()

    def _init_seed_log(self):
        now = datetime.now(timezone.utc).isoformat()
        self.agent_logs.append(
            AgentLogEntry(
                id="LOG-001",
                timestamp=now,
                agent_name="System Orchestrator",
                action="SYSTEM_INIT",
                details={"status": "online", "bins_tracked": len(self.bins), "fleet_size": len(self.vehicles)},
                level="INFO",
            )
        )

    def reset(self):
        self.bins = {b.id: copy.deepcopy(b) for b in INITIAL_BINS}
        self.vehicles = {v.id: copy.deepcopy(v) for v in INITIAL_VEHICLES}
        self.active_plan = None
        self.agent_logs.clear()
        self.plan_history.clear()
        self._init_seed_log()

    def get_bin(self, bin_id: str) -> Optional[SmartBin]:
        return self.bins.get(bin_id)

    def get_all_bins(self) -> List[SmartBin]:
        return list(self.bins.values())

    def update_bin(self, smart_bin: SmartBin):
        self.bins[smart_bin.id] = smart_bin

    def get_vehicle(self, vehicle_id: str) -> Optional[Vehicle]:
        return self.vehicles.get(vehicle_id)

    def get_all_vehicles(self) -> List[Vehicle]:
        return list(self.vehicles.values())

    def update_vehicle(self, vehicle: Vehicle):
        self.vehicles[vehicle.id] = vehicle

    def log_agent_action(self, agent_name: str, action: str, details: Dict, level: str = "INFO"):
        entry = AgentLogEntry(
            id=f"LOG-{len(self.agent_logs) + 1:04d}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            agent_name=agent_name,
            action=action,
            details=details,
            level=level,
        )
        self.agent_logs.insert(0, entry)
        if len(self.agent_logs) > 300:
            self.agent_logs = self.agent_logs[:300]
        return entry

    def get_logs(self, limit: int = 50) -> List[AgentLogEntry]:
        return self.agent_logs[:limit]


# Global database instance
db = DatabaseStore()
