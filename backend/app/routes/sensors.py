from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import db
from app.models import SensorIngestPayload, SmartBin, BinStatus, SensorHealth
from app.services.anomaly_detector import SensorAnomalyDetector
from app.services.iot_simulator import IoTSensorSimulator

router = APIRouter(prefix="/api/sensors", tags=["IoT Sensors & Telemetry"])


class SpikeRequest(BaseModel):
    bin_id: str
    target_fill_pct: Optional[float] = 98.0


class MarkCollectedRequest(BaseModel):
    bin_ids: List[str]


@router.post("/ingest")
def ingest_sensor_reading(payload: SensorIngestPayload):
    bin_obj = db.get_bin(payload.bin_id)
    if not bin_obj:
        raise HTTPException(status_code=404, detail=f"Bin {payload.bin_id} not found")

    is_valid, flags, health = SensorAnomalyDetector.validate_and_audit(bin_obj, payload)

    now = payload.timestamp or datetime.now(timezone.utc).isoformat()

    # Even if flagged, we log the event and update state accordingly
    bin_obj.current_fill_pct = max(0.0, min(100.0, payload.fill_pct))
    bin_obj.current_weight_kg = max(0.0, payload.weight_kg)
    if payload.battery_pct is not None:
        bin_obj.battery_pct = payload.battery_pct
    if payload.temperature_c is not None:
        bin_obj.temperature_c = payload.temperature_c
    if payload.tilt_angle_deg is not None:
        bin_obj.tilt_angle_deg = payload.tilt_angle_deg

    bin_obj.sensor_health = health
    bin_obj.anomaly_flags = flags
    bin_obj.last_reading_at = now

    # Status classification
    if health in (SensorHealth.TILTED, SensorHealth.ANOMALOUS):
        bin_obj.status = BinStatus.WARNING
    elif bin_obj.current_fill_pct >= 85.0:
        bin_obj.status = BinStatus.CRITICAL
    elif bin_obj.current_fill_pct >= 70.0:
        bin_obj.status = BinStatus.WARNING
    else:
        bin_obj.status = BinStatus.NORMAL

    # Store historical series
    bin_obj.historical_readings.append({
        "timestamp": now,
        "fill_pct": bin_obj.current_fill_pct,
        "weight_kg": bin_obj.current_weight_kg,
        "battery_pct": bin_obj.battery_pct,
        "temperature_c": bin_obj.temperature_c,
        "tilt_angle_deg": bin_obj.tilt_angle_deg,
    })
    if len(bin_obj.historical_readings) > 30:
        bin_obj.historical_readings.pop(0)

    db.update_bin(bin_obj)

    level = "ALERT" if flags else "INFO"
    db.log_agent_action(
        agent_name="Smart Bin Monitoring Agent",
        action="SENSOR_DATA_INGESTED",
        details={
            "bin_id": bin_obj.id,
            "fill_pct": bin_obj.current_fill_pct,
            "weight_kg": bin_obj.current_weight_kg,
            "health": health.value,
            "anomaly_flags": flags,
        },
        level=level,
    )

    return {
        "status": "ACCEPTED" if is_valid else "QUARANTINED_WITH_FLAGS",
        "bin_id": bin_obj.id,
        "fill_pct": bin_obj.current_fill_pct,
        "health": health.value,
        "anomaly_flags": flags,
    }


@router.post("/simulate-tick")
def simulate_telemetry_tick():
    results = IoTSensorSimulator.simulate_telemetry_tick()
    db.log_agent_action(
        agent_name="Smart Bin Monitoring Agent",
        action="TELEMETRY_STREAM_ADVANCED",
        details={"updated_bins_count": len(results)},
        level="INFO",
    )
    return {"message": "Advanced simulated time by 1 tick", "updates": results}


@router.post("/inject-spike")
def inject_critical_spike(payload: SpikeRequest):
    updated_bin = IoTSensorSimulator.inject_emergency_spike(payload.bin_id, payload.target_fill_pct or 98.0)
    if not updated_bin:
        raise HTTPException(status_code=404, detail=f"Bin {payload.bin_id} not found")

    db.log_agent_action(
        agent_name="Smart Bin Monitoring Agent",
        action="EMERGENCY_SPIKE_SIMULATED",
        details={"bin_id": payload.bin_id, "new_fill_pct": updated_bin.current_fill_pct},
        level="ALERT",
    )
    return {"message": f"Emergency spike injected into {payload.bin_id}", "bin": updated_bin}


@router.post("/mark-collected")
def mark_collected(payload: MarkCollectedRequest):
    updated = IoTSensorSimulator.mark_collected(payload.bin_ids)
    db.log_agent_action(
        agent_name="Waste Operations & Action Planning Agent",
        action="BINS_COLLECTED_AND_EMPTIED",
        details={"bins_serviced": [b.id for b in updated]},
        level="SUCCESS",
    )
    return {"message": f"Successfully serviced and emptied {len(updated)} bins", "cleared_bins": [b.id for b in updated]}
