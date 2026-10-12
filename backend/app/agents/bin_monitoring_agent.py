from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.models import BinStatus, SensorHealth, SmartBin
from app.services.anomaly_detector import SensorAnomalyDetector


class BinMonitoringAgent(BaseAgent):
    """
    Agent 1: Smart Bin Monitoring Agent
    Responsible for sensor telemetry ingestion, data validation,
    physical tilt/temperature monitoring, anomaly detection, and alert generation.
    """

    def __init__(self):
        super().__init__(
            name="Smart Bin Monitoring Agent",
            role="IoT Sensor Telemetry Ingestion, Data Validation, and Edge Anomaly Detection",
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        bins: List[SmartBin] = state.get("bins", [])
        validated_bins: List[SmartBin] = []
        alerts_raised = []

        for b in bins:
            # Check physical tilt
            if b.tilt_angle_deg > 15.0:
                b.sensor_health = SensorHealth.TILTED
                b.status = BinStatus.WARNING
                if "TILT_WARNING" not in b.anomaly_flags:
                    b.anomaly_flags.append(f"TILT_WARNING: Sensor tilt is {b.tilt_angle_deg:.1f}°")
                alerts_raised.append(f"{b.id}: Tilted ({b.tilt_angle_deg:.1f}°)")

            # Check thermal hazard
            if b.temperature_c > 55.0:
                b.sensor_health = SensorHealth.ANOMALOUS
                b.status = BinStatus.CRITICAL
                if "THERMAL_HAZARD" not in b.anomaly_flags:
                    b.anomaly_flags.append(f"THERMAL_HAZARD: Temperature {b.temperature_c:.1f}°C")
                alerts_raised.append(f"{b.id}: Thermal Hazard ({b.temperature_c:.1f}°C)")

            # Check fill thresholds
            if b.current_fill_pct >= 85.0:
                b.status = BinStatus.CRITICAL
                alerts_raised.append(f"{b.id}: Critical fill {b.current_fill_pct:.1f}%")
            elif b.current_fill_pct >= 70.0:
                b.status = BinStatus.WARNING
            else:
                b.status = BinStatus.NORMAL

            # Low battery warning
            if b.battery_pct < 15.0:
                if "LOW_BATTERY" not in b.anomaly_flags:
                    b.anomaly_flags.append(f"LOW_BATTERY: {b.battery_pct:.1f}% remaining")

            validated_bins.append(b)

        level = "ALERT" if alerts_raised else "INFO"
        self.log(
            action="TELEMETRY_AUDIT_COMPLETE",
            details={
                "total_monitored": len(validated_bins),
                "critical_bins": sum(1 for b in validated_bins if b.status == BinStatus.CRITICAL),
                "warning_bins": sum(1 for b in validated_bins if b.status == BinStatus.WARNING),
                "anomalies_detected": sum(1 for b in validated_bins if b.sensor_health != SensorHealth.OK),
                "alerts": alerts_raised[:5],
            },
            level=level,
        )

        state["bins"] = validated_bins
        state["monitoring_alerts"] = alerts_raised
        return state
