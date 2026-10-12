from datetime import datetime, timezone
from typing import Dict, List, Tuple
from app.models import SmartBin, SensorHealth, BinStatus, SensorIngestPayload


class SensorAnomalyDetector:
    """
    Validates IoT smart bin telemetry and flags sensor anomalies:
    - Out of range (fill < 0% or > 100%, weight < 0kg)
    - Spike anomaly (sudden unrealistic increase > 45% in one step)
    - Stale readings (identical telemetry over extended periods)
    - Tilt/Tumble anomaly (tilt > 15 degrees)
    - Thermal hazard (> 55 C)
    - Low battery (< 20%)
    """

    @staticmethod
    def validate_and_audit(bin_obj: SmartBin, payload: SensorIngestPayload) -> Tuple[bool, List[str], SensorHealth]:
        flags: List[str] = []
        health = SensorHealth.OK
        is_valid = True

        # 1. Range Validation
        if payload.fill_pct < 0 or payload.fill_pct > 100:
            flags.append(f"OUT_OF_RANGE_FILL: {payload.fill_pct}% is invalid (expected 0-100%).")
            health = SensorHealth.ANOMALOUS
            is_valid = False

        if payload.weight_kg < 0:
            flags.append(f"OUT_OF_RANGE_WEIGHT: {payload.weight_kg}kg cannot be negative.")
            health = SensorHealth.ANOMALOUS
            is_valid = False

        if payload.weight_kg > (bin_obj.capacity_kg * 1.6):
            flags.append(f"OVER_CAPACITY_WEIGHT: {payload.weight_kg}kg exceeds max physical limit ({bin_obj.capacity_kg}kg).")
            health = SensorHealth.ANOMALOUS
            is_valid = False

        # 2. Sudden Spike Detection
        delta_fill = payload.fill_pct - bin_obj.current_fill_pct
        if delta_fill > 45.0 and bin_obj.current_fill_pct > 0:
            flags.append(f"SPIKE_ANOMALY: Sudden fill surge of +{delta_fill:.1f}% detected in single interval.")
            health = SensorHealth.SPIKE

        # 3. Tilt / Physical Tamper Detection
        tilt = payload.tilt_angle_deg if payload.tilt_angle_deg is not None else bin_obj.tilt_angle_deg
        if tilt > 15.0:
            flags.append(f"TILT_ANOMALY: Bin tilt angle is {tilt:.1f}° (possible tipping or collision).")
            health = SensorHealth.TILTED

        # 4. Thermal Safety / Hazard
        temp = payload.temperature_c if payload.temperature_c is not None else bin_obj.temperature_c
        if temp > 55.0:
            flags.append(f"THERMAL_HAZARD: Temperature {temp:.1f}°C indicates smoldering combustion or direct fire risk!")
            health = SensorHealth.ANOMALOUS

        # 5. Stale reading detection
        if len(bin_obj.historical_readings) >= 4:
            recent_fills = [r.get("fill_pct", 0) for r in bin_obj.historical_readings[-4:]]
            if all(abs(f - payload.fill_pct) < 0.05 for f in recent_fills) and payload.fill_pct > 20.0:
                flags.append("STALE_TELEMETRY: Ultrasonic sensor reporting zero variance across last 4 cycles.")
                health = SensorHealth.STALE

        # 6. Battery Warning
        battery = payload.battery_pct if payload.battery_pct is not None else bin_obj.battery_pct
        if battery < 20.0:
            flags.append(f"LOW_BATTERY: Power cell at {battery:.1f}%. Maintenance required.")

        return is_valid, flags, health
