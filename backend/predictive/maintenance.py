"""Predictive maintenance stub.
If H2O is available and a MOJO path exists, load it; otherwise, return random probability.
"""
from __future__ import annotations

import os
import random
from pathlib import Path

try:
    import h2o  # type: ignore

    H2O_AVAILABLE = True
except ImportError:
    H2O_AVAILABLE = False


class HealthPredictor:
    def __init__(self, mojo_path: str | None = None):
        self.use_h2o = H2O_AVAILABLE and (mojo_path or Path("model/equipment_failure.mojo").exists())
        if self.use_h2o:
            h2o.init(nthreads=1, max_mem_size="1G")
            path = mojo_path or "model/equipment_failure.mojo"
            self.model = h2o.import_mojo(path)  # type: ignore
        else:
            self.model = None

    def predict(self, sensor_dict: dict) -> float:
        if self.use_h2o and self.model is not None:  # pragma: no cover
            frame = h2o.H2OFrame([sensor_dict])  # type: ignore
            prob = float(self.model.predict(frame).as_data_frame().iloc[0, 0])  # type: ignore
        else:
            # simple heuristic: higher vibration/temperature -> higher risk
            base = 0.1 + 0.005 * sensor_dict.get("temperature", 70)
            base += 0.5 * sensor_dict.get("vibration", 0)
            prob = min(max(base, 0), 1)
        return prob 