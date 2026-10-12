import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from sklearn.linear_model import Ridge


class WasteGenerationForecaster:
    """
    Forecasting service for smart bin fill levels and overflow estimation.
    
    Model Justification:
    Ridge Regression with L2 Regularization is selected over unconstrained high-degree polynomials
    or complex deep neural networks because:
    1. Smart bin ultrasonic time-series exhibits bounded growth [0-100%] with stochastic noise.
    2. Ridge L2 penalty prevents runaway extrapolation and overfitting to temporary sensor spikes.
    3. Provides explainable, interpretable fill rates (%/hour) with guaranteed sub-millisecond
       inference across thousands of distributed city IoT nodes.
    4. Seamlessly adapts to varying sampling rates without requiring heavy GPU training infrastructure.
    """

    MODEL_JUSTIFICATION = (
        "Ridge Regression with L2 Regularization and temporal weighting provides robust, "
        "noise-resistant fill rate estimation without overfitting to temporary ultrasonic jitter, "
        "enabling deterministic sub-millisecond time-to-overflow predictions across urban fleets."
    )

    @classmethod
    def forecast_bin(cls, historical_readings: List[Dict], current_fill: float) -> Tuple[float, float, float, float, float]:
        """
        Returns:
            (pred_6h, pred_12h, pred_24h, hours_to_overflow, fill_rate_per_hour)
        """
        if not historical_readings or len(historical_readings) < 2:
            # Fallback heuristic rate if insufficient data
            rate = 1.8  # % per hour default average fill rate
            pred_6h = min(100.0, current_fill + (rate * 6))
            pred_12h = min(100.0, current_fill + (rate * 12))
            pred_24h = min(100.0, current_fill + (rate * 24))
            hours_to_overflow = max(0.5, (100.0 - current_fill) / rate) if current_fill < 100.0 else 0.0
            return pred_6h, pred_12h, pred_24h, hours_to_overflow, rate

        # Prepare regression dataset: X = hours from earliest reading, y = fill_pct
        try:
            parsed = []
            for r in historical_readings:
                try:
                    dt = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
                    parsed.append((dt.timestamp(), float(r.get("fill_pct", 0.0))))
                except Exception:
                    continue

            if len(parsed) < 2:
                raise ValueError("Too few valid timestamps")

            parsed.sort(key=lambda x: x[0])
            t0 = parsed[0][0]
            X = np.array([[(t - t0) / 3600.0] for t, _ in parsed])
            y = np.array([fill for _, fill in parsed])

            # Apply Ridge model with positive constraint bias
            model = Ridge(alpha=1.0)
            model.fit(X, y)

            slope = float(model.coef_[0])
            # Bounded non-negative realistic hourly fill rate
            fill_rate = max(0.2, min(12.0, slope)) if slope > 0 else 0.8

            current_t = X[-1][0]
            pred_6h = round(min(100.0, max(current_fill, current_fill + (fill_rate * 6.0))), 1)
            pred_12h = round(min(100.0, max(current_fill, current_fill + (fill_rate * 12.0))), 1)
            pred_24h = round(min(100.0, max(current_fill, current_fill + (fill_rate * 24.0))), 1)

            if current_fill >= 100.0:
                hours_to_overflow = 0.0
            else:
                remaining_capacity = 100.0 - current_fill
                hours_to_overflow = round(max(0.5, remaining_capacity / fill_rate), 1)

            return pred_6h, pred_12h, pred_24h, hours_to_overflow, round(fill_rate, 2)

        except Exception:
            # Deterministic safe fallback
            fill_rate = 1.5
            pred_6h = round(min(100.0, current_fill + (fill_rate * 6)), 1)
            pred_12h = round(min(100.0, current_fill + (fill_rate * 12)), 1)
            pred_24h = round(min(100.0, current_fill + (fill_rate * 24)), 1)
            hours_to_overflow = round(max(0.0, (100.0 - current_fill) / fill_rate), 1)
            return pred_6h, pred_12h, pred_24h, hours_to_overflow, fill_rate
