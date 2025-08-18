import pandas as pd
from typing import Optional, Dict, Any

class MetricsService:
    def __init__(self, csv_path: str):
        df = pd.read_csv(csv_path)
        # cache group stats for fast lookups
        self.by_soil = df.groupby("Soil Type").agg(
            H_mean=("Humidity", "mean"),
            H_p25=("Humidity", lambda s: s.quantile(0.25)),
            H_p75=("Humidity", lambda s: s.quantile(0.75)),
            M_mean=("Moisture", "mean"),
            M_p25=("Moisture", lambda s: s.quantile(0.25)),
            M_p75=("Moisture", lambda s: s.quantile(0.75)),
            Count=("Humidity", "size")
        )
        self.by_crop = df.groupby("Crop Type").agg(
            H_mean=("Humidity", "mean"),
            H_p25=("Humidity", lambda s: s.quantile(0.25)),
            H_p75=("Humidity", lambda s: s.quantile(0.75)),
            M_mean=("Moisture", "mean"),
            M_p25=("Moisture", lambda s: s.quantile(0.25)),
            M_p75=("Moisture", lambda s: s.quantile(0.75)),
            Count=("Humidity", "size")
        )
        self.overall = df.agg({"Humidity":["mean","median","min","max"], "Moisture":["mean","median","min","max"]})

    @staticmethod
    def _band_status(value: Optional[float], p25: Optional[float], p75: Optional[float]) -> str:
        if value is None or p25 is None or p75 is None:
            return "unknown"
        if value < p25: return "low"
        if value > p75: return "high"
        return "adequate"

    def metrics_block(
        self,
        humidity_now: Optional[float],
        moisture_now_top: Optional[float],
        soil_type: Optional[str] = None,
        crop_type: Optional[str] = None
    ) -> Dict[str, Any]:
        soil_row = self.by_soil.loc[soil_type] if soil_type in self.by_soil.index else None
        crop_row = self.by_crop.loc[crop_type] if crop_type in self.by_crop.index else None

        def pick(r, hcol, mcol):
            if r is None: return (None, None, None, None)
            return float(r[hcol+"_"+"p25"]), float(r[hcol+"_"+"p75"]), float(r[mcol+"_"+"p25"]), float(r[mcol+"_"+"p75"])

        # Try crop‑specific first, else soil‑specific
        H_p25 = H_p75 = M_p25 = M_p75 = None
        if crop_row is not None:
            H_p25, H_p75, M_p25, M_p75 = crop_row["H_p25"], crop_row["H_p75"], crop_row["M_p25"], crop_row["M_p75"]
        elif soil_row is not None:
            H_p25, H_p75, M_p25, M_p75 = soil_row["H_p25"], soil_row["H_p75"], soil_row["M_p25"], soil_row["M_p75"]

        return {
            "inputs": {
                "soil_type": soil_type,
                "crop_type": crop_type,
                "humidity_now_pct": humidity_now,
                "soil_moisture_top_m3m3": moisture_now_top
            },
            "targets": {
                "humidity_p25": None if H_p25 is None else round(H_p25, 2),
                "humidity_p75": None if H_p75 is None else round(H_p75, 2),
                "moisture_p25": None if M_p25 is None else round(M_p25, 3),
                "moisture_p75": None if M_p75 is None else round(M_p75, 3)
            },
            "status": {
                "humidity_status": self._band_status(humidity_now, H_p25, H_p75),
                "moisture_status": self._band_status(moisture_now_top, M_p25, M_p75)
            }
        }
