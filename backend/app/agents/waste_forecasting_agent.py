from typing import Any, Dict, List
from app.agents.base_agent import BaseAgent
from app.models import SmartBin
from app.services.ml_forecaster import WasteGenerationForecaster


class WasteForecastingAgent(BaseAgent):
    """
    Agent 2: Waste Generation Forecasting Agent
    Uses Ridge Regression and time-series feature engineering to forecast future fill levels,
    estimate fill velocity (%/hour), and predict hours until bin overflow.
    """

    def __init__(self):
        super().__init__(
            name="Waste Generation Forecasting Agent",
            role="Predictive ML Fill-Level Modeling and Time-to-Overflow Forecasting",
        )

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        bins: List[SmartBin] = state.get("bins", [])
        forecast_results = {}
        impending_overflows = []

        for b in bins:
            p6, p12, p24, h_overflow, rate = WasteGenerationForecaster.forecast_bin(
                b.historical_readings, b.current_fill_pct
            )

            b.predicted_fill_6h = p6
            b.predicted_fill_12h = p12
            b.predicted_fill_24h = p24
            b.hours_to_overflow = h_overflow

            forecast_results[b.id] = {
                "predicted_6h": p6,
                "predicted_12h": p12,
                "predicted_24h": p24,
                "hours_to_overflow": h_overflow,
                "fill_rate_pct_hr": rate,
            }

            # Predict overflow risk within 12 hours
            if h_overflow <= 12.0:
                impending_overflows.append({
                    "bin_id": b.id,
                    "name": b.name,
                    "hours_to_overflow": h_overflow,
                    "fill_rate": rate,
                })

        self.log(
            action="FORECAST_MODELS_CONVERGED",
            details={
                "model": "Ridge Regression with Temporal L2 Regularization",
                "justification": WasteGenerationForecaster.MODEL_JUSTIFICATION,
                "bins_forecasted": len(bins),
                "overflows_within_12h": len(impending_overflows),
                "high_risk_bins": [o["bin_id"] for o in impending_overflows[:5]],
            },
            level="WARNING" if impending_overflows else "INFO",
        )

        state["bins"] = bins
        state["forecasts"] = forecast_results
        state["impending_overflows"] = impending_overflows
        return state
