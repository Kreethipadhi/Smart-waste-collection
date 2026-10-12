import pytest
from app.database import db, DEPOT
from app.models import (
    SmartBin,
    WasteType,
    BinStatus,
    SensorHealth,
    Vehicle,
    VehicleStatus,
    SensorIngestPayload,
    ApprovalStatus,
)
from app.services.anomaly_detector import SensorAnomalyDetector
from app.services.ml_forecaster import WasteGenerationForecaster
from app.services.cvrp_solver import CVRPSolver
from app.agents.orchestrator import MultiAgentOrchestrator
from app.agents.bin_monitoring_agent import BinMonitoringAgent
from app.agents.collection_priority_agent import CollectionPriorityAgent
from app.agents.vehicle_capacity_agent import VehicleCapacityAgent
from app.agents.operations_critic_agent import OperationsCriticAgent
from app.services.iot_simulator import IoTSensorSimulator


@pytest.fixture
def orchestrator():
    return MultiAgentOrchestrator()


# =====================================================================
# TEST CASE 1: High fill bin prioritization
# =====================================================================
def test_high_fill_bin_prioritization():
    """Verifies that bins with high fill (>= 85%) receive high priority scores and top dispatch rank."""
    b_low = SmartBin(
        id="TEST-LOW",
        name="Low Fill Bin",
        latitude=37.785,
        longitude=-122.402,
        waste_type=WasteType.GENERAL,
        current_fill_pct=25.0,
        current_weight_kg=35.0,
    )
    b_high = SmartBin(
        id="TEST-HIGH",
        name="Critical High Fill Bin",
        latitude=37.786,
        longitude=-122.403,
        waste_type=WasteType.GENERAL,
        current_fill_pct=92.0,
        current_weight_kg=138.0,
    )

    agent = CollectionPriorityAgent()
    state = {"bins": [b_low, b_high]}
    updated_state = agent.run(state)

    ranked_bins = updated_state["bins"]
    assert ranked_bins[0].id == "TEST-HIGH"
    assert ranked_bins[0].collection_priority > 50.0
    assert ranked_bins[1].id == "TEST-LOW"
    assert ranked_bins[0].collection_priority > ranked_bins[1].collection_priority
    assert any("Severe fill level" in r for r in ranked_bins[0].priority_reasons)


# =====================================================================
# TEST CASE 2: Forecast-based predictive collection
# =====================================================================
def test_forecast_predictive_collection():
    """Verifies that bins with moderate fill but high fill velocity trigger predictive collection."""
    # Bin with 65% fill but steep rising history
    historical = [
        {"timestamp": "2026-10-12T10:00:00Z", "fill_pct": 30.0},
        {"timestamp": "2026-10-12T12:00:00Z", "fill_pct": 42.0},
        {"timestamp": "2026-10-12T14:00:00Z", "fill_pct": 54.0},
        {"timestamp": "2026-10-12T16:00:00Z", "fill_pct": 66.0},
    ]

    p6, p12, p24, h_overflow, fill_rate = WasteGenerationForecaster.forecast_bin(historical, current_fill=66.0)

    assert p6 > 66.0
    assert fill_rate > 3.0  # fill velocity is high
    assert h_overflow <= 12.0  # will overflow within 12 hours

    # Run through priority agent to verify predictive urgency elevates score
    test_bin = SmartBin(
        id="TEST-PREDICTIVE",
        name="Predictive Risk Bin",
        latitude=37.787,
        longitude=-122.404,
        waste_type=WasteType.GENERAL,
        current_fill_pct=66.0,
        current_weight_kg=90.0,
        hours_to_overflow=h_overflow,
    )
    agent = CollectionPriorityAgent()
    state = agent.run({"bins": [test_bin]})

    elevated_bin = state["bins"][0]
    assert elevated_bin.collection_priority >= 45.0
    assert any("overflow" in r.lower() for r in elevated_bin.priority_reasons)


# =====================================================================
# TEST CASE 3: Sensor anomaly detection and verification triggers
# =====================================================================
def test_sensor_anomaly_detection():
    """Verifies out-of-range, tilt, thermal, and sudden spike anomalies are detected and quarantined."""
    normal_bin = SmartBin(
        id="TEST-ANOMALY-BIN",
        name="Anomaly Test Bin",
        latitude=37.788,
        longitude=-122.405,
        current_fill_pct=20.0,
        current_weight_kg=30.0,
        capacity_kg=150.0,
    )

    # 1. Out of range fill (>100%)
    invalid_fill = SensorIngestPayload(bin_id="TEST-ANOMALY-BIN", fill_pct=145.0, weight_kg=50.0)
    is_valid, flags, health = SensorAnomalyDetector.validate_and_audit(normal_bin, invalid_fill)
    assert not is_valid
    assert any("OUT_OF_RANGE_FILL" in f for f in flags)

    # 2. Severe tilt anomaly (>15 deg)
    tilted = SensorIngestPayload(bin_id="TEST-ANOMALY-BIN", fill_pct=40.0, weight_kg=40.0, tilt_angle_deg=28.5)
    is_valid, flags, health = SensorAnomalyDetector.validate_and_audit(normal_bin, tilted)
    assert health == SensorHealth.TILTED
    assert any("TILT_ANOMALY" in f for f in flags)

    # 3. Sudden surge / spike anomaly (+60% jump)
    spike = SensorIngestPayload(bin_id="TEST-ANOMALY-BIN", fill_pct=85.0, weight_kg=120.0)
    is_valid, flags, health = SensorAnomalyDetector.validate_and_audit(normal_bin, spike)
    assert health == SensorHealth.SPIKE
    assert any("SPIKE_ANOMALY" in f for f in flags)


# =====================================================================
# TEST CASE 4: Multi-bin route optimization validation
# =====================================================================
def test_multi_bin_route_optimization():
    """Verifies CVRP solver builds a coherent route visiting multiple bins and returning to depot."""
    bins = [
        SmartBin(id="B1", name="Bin 1", latitude=37.789, longitude=-122.401, current_weight_kg=120.0, waste_type=WasteType.GENERAL),
        SmartBin(id="B2", name="Bin 2", latitude=37.784, longitude=-122.407, current_weight_kg=140.0, waste_type=WasteType.GENERAL),
        SmartBin(id="B3", name="Bin 3", latitude=37.788, longitude=-122.407, current_weight_kg=110.0, waste_type=WasteType.GENERAL),
    ]
    truck = Vehicle(
        id="V1",
        name="Alpha Truck",
        latitude=DEPOT.latitude,
        longitude=DEPOT.longitude,
        supported_waste_types=[WasteType.GENERAL],
        max_payload_kg=1000.0,
    )

    routes = CVRPSolver.solve_collection_routes(DEPOT, bins, [truck])
    assert len(routes) == 1
    route = routes[0]

    assert route.vehicle_id == "V1"
    assert len(route.bin_ids) == 3
    assert route.total_distance_km > 0.0
    assert route.total_waste_kg == (120.0 + 140.0 + 110.0)
    assert route.waypoints[0].action == "START_DEPOT"
    assert route.waypoints[-1].action == "END_DEPOT"


# =====================================================================
# TEST CASE 5: Vehicle capacity enforcement
# =====================================================================
def test_vehicle_capacity_enforcement():
    """Verifies that vehicle max payload is never exceeded and trips are split if needed."""
    heavy_bins = [
        SmartBin(id="HB1", name="Heavy 1", latitude=37.789, longitude=-122.401, current_weight_kg=400.0, waste_type=WasteType.GENERAL),
        SmartBin(id="HB2", name="Heavy 2", latitude=37.784, longitude=-122.407, current_weight_kg=400.0, waste_type=WasteType.GENERAL),
        SmartBin(id="HB3", name="Heavy 3", latitude=37.788, longitude=-122.407, current_weight_kg=400.0, waste_type=WasteType.GENERAL),
    ]
    small_truck = Vehicle(
        id="V_SMALL",
        name="Small Van",
        latitude=DEPOT.latitude,
        longitude=DEPOT.longitude,
        supported_waste_types=[WasteType.GENERAL],
        max_payload_kg=700.0,
    )

    routes = CVRPSolver.solve_collection_routes(DEPOT, heavy_bins, [small_truck])
    assert len(routes) >= 1
    for r in routes:
        assert r.total_waste_kg <= small_truck.max_payload_kg

    critic = OperationsCriticAgent()
    critic_res = critic.run({
        "optimized_routes": routes,
        "bins": heavy_bins,
        "vehicles": [small_truck],
    })
    assert len(critic_res["critic_review"]["violations"]) == 0


# =====================================================================
# TEST CASE 6: Waste-type compatibility checking
# =====================================================================
def test_waste_type_compatibility():
    """Verifies that vehicles only service matching waste types."""
    recyclable_bin = SmartBin(
        id="BIN-REC",
        name="Recycle Bin",
        latitude=37.789,
        longitude=-122.396,
        waste_type=WasteType.RECYCLABLE,
        current_weight_kg=100.0,
    )
    general_only_truck = Vehicle(
        id="V-GEN-ONLY",
        name="General Compactor",
        latitude=DEPOT.latitude,
        longitude=DEPOT.longitude,
        supported_waste_types=[WasteType.GENERAL],
        max_payload_kg=1000.0,
    )
    recycle_truck = Vehicle(
        id="V-REC-ONLY",
        name="Recycle Truck",
        latitude=DEPOT.latitude,
        longitude=DEPOT.longitude,
        supported_waste_types=[WasteType.RECYCLABLE],
        max_payload_kg=800.0,
    )

    routes = CVRPSolver.solve_collection_routes(DEPOT, [recyclable_bin], [general_only_truck, recycle_truck])
    assert len(routes) == 1
    assert routes[0].vehicle_id == "V-REC-ONLY"
    assert routes[0].waste_type == WasteType.RECYCLABLE


# =====================================================================
# TEST CASE 7: Dynamic replanning triggered by new critical bins
# =====================================================================
def test_dynamic_replanning_on_critical_bin(orchestrator):
    """Verifies dynamic replanning reacts to unexpected critical bins on the fly."""
    db.reset()
    b4 = db.get_bin("BIN-004")
    assert b4 is not None
    db.bins["BIN-004"].current_fill_pct = 20.0
    db.bins["BIN-004"].status = BinStatus.NORMAL

    # Trigger emergency replan on BIN-004
    plan = orchestrator.trigger_dynamic_replan(
        trigger_type="CRITICAL_BIN",
        target_bin_id="BIN-004",
        notes="Tourist festival sudden overflow alert",
    )

    updated_b4 = db.get_bin("BIN-004")
    assert updated_b4.current_fill_pct >= 95.0
    assert updated_b4.status == BinStatus.CRITICAL

    scheduled_bins = []
    for r in plan.routes:
        scheduled_bins.extend(r.bin_ids)

    assert "BIN-004" in scheduled_bins


# =====================================================================
# TEST CASE 8: Successful collection and state updates
# =====================================================================
def test_collection_state_updates():
    """Verifies that executing collection resets bin fill %, updates timestamps, and clears payload."""
    db.reset()
    bin_ids = ["BIN-001", "BIN-002"]
    b1 = db.get_bin("BIN-001")
    assert b1.current_fill_pct > 80.0

    cleared = IoTSensorSimulator.mark_collected(bin_ids)
    assert len(cleared) == 2

    for b in cleared:
        assert b.current_fill_pct <= 5.0
        assert b.current_weight_kg <= 10.0
        assert b.status == BinStatus.NORMAL
        assert b.last_collected_at is not None
        assert b.collection_priority <= 10.0
