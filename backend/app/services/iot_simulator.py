import random
from datetime import datetime, timezone
from typing import Dict, List, Optional
from app.models import SmartBin, SensorIngestPayload, BinStatus, SensorHealth
from app.database import db


class IoTSensorSimulator:
    """Simulates real-time IoT sensor telemetry streams and edge scenarios."""

    @classmethod
    def simulate_telemetry_tick(cls) -> List[Dict]:
        """Advances time for all smart bins, accumulating waste realistically."""
        now = datetime.now(timezone.utc).isoformat()
        results = []

        for bin_obj in db.get_all_bins():
            if bin_obj.status == BinStatus.OFFLINE:
                continue

            # Diurnal fill increment: between 0.8% and 3.5%
            delta_fill = round(random.uniform(0.8, 3.5), 1)
            new_fill = min(100.0, round(bin_obj.current_fill_pct + delta_fill, 1))

            # Proportional weight increment
            weight_ratio = new_fill / 100.0
            new_weight = round(bin_obj.capacity_kg * weight_ratio, 1)

            # Minor battery drain
            new_battery = max(5.0, round(bin_obj.battery_pct - 0.05, 1))

            reading = {
                "timestamp": now,
                "fill_pct": new_fill,
                "weight_kg": new_weight,
                "battery_pct": new_battery,
                "temperature_c": round(22.0 + (new_fill * 0.04), 1),
                "tilt_angle_deg": bin_obj.tilt_angle_deg,
            }

            bin_obj.current_fill_pct = new_fill
            bin_obj.current_weight_kg = new_weight
            bin_obj.battery_pct = new_battery
            bin_obj.last_reading_at = now
            bin_obj.historical_readings.append(reading)

            if len(bin_obj.historical_readings) > 30:
                bin_obj.historical_readings.pop(0)

            # Update status
            if new_fill >= 85.0:
                bin_obj.status = BinStatus.CRITICAL
            elif new_fill >= 70.0:
                bin_obj.status = BinStatus.WARNING
            else:
                bin_obj.status = BinStatus.NORMAL

            db.update_bin(bin_obj)
            results.append({"bin_id": bin_obj.id, "fill_pct": new_fill, "weight_kg": new_weight})

        return results

    @classmethod
    def inject_emergency_spike(cls, bin_id: str, target_fill: float = 98.0) -> Optional[SmartBin]:
        bin_obj = db.get_bin(bin_id)
        if not bin_obj:
            return None

        now = datetime.now(timezone.utc).isoformat()
        bin_obj.current_fill_pct = target_fill
        bin_obj.current_weight_kg = round(bin_obj.capacity_kg * (target_fill / 100.0), 1)
        bin_obj.status = BinStatus.CRITICAL
        bin_obj.last_reading_at = now
        bin_obj.historical_readings.append({
            "timestamp": now,
            "fill_pct": target_fill,
            "weight_kg": bin_obj.current_weight_kg,
            "battery_pct": bin_obj.battery_pct,
            "temperature_c": 26.5,
            "tilt_angle_deg": 1.2,
        })
        db.update_bin(bin_obj)
        return bin_obj

    @classmethod
    def mark_collected(cls, bin_ids: List[str]) -> List[SmartBin]:
        """Simulates physical collection: empties bin and timestamps last_collected_at."""
        now = datetime.now(timezone.utc).isoformat()
        updated = []
        for bid in bin_ids:
            bin_obj = db.get_bin(bid)
            if bin_obj:
                bin_obj.current_fill_pct = 4.0
                bin_obj.current_weight_kg = 5.0
                bin_obj.status = BinStatus.NORMAL
                bin_obj.last_collected_at = now
                bin_obj.last_reading_at = now
                bin_obj.collection_priority = 5.0
                bin_obj.priority_reasons = ["Recently cleared and sanitized"]
                bin_obj.historical_readings.append({
                    "timestamp": now,
                    "fill_pct": 4.0,
                    "weight_kg": 5.0,
                    "battery_pct": bin_obj.battery_pct,
                    "temperature_c": 20.0,
                    "tilt_angle_deg": 0.5,
                })
                db.update_bin(bin_obj)
                updated.append(bin_obj)
        return updated
