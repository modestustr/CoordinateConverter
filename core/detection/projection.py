# core/detection/projection.py
from .base import DetectionStrategy
from typing import Tuple, Dict, Any

class ProjectionStrategy(DetectionStrategy):
    priority = 5  # Projeksiyon tespiti orta öncelik

    def detect_swap(self, x: float, y: float) -> Tuple[float, float]:
        # Easting/Northing systems standardly use X, Y. No swapping needed.
        return x, y

    def suggest_crs(self, x: float, y: float) -> Dict[str, Any]:
        if 100000 <= abs(x) <= 1000000 and 0 <= abs(y) <= 10000000:
            return {
                "system": "DYNAMIC_WGS84_UTM",
                "confidence": 0.8,
                "reason": "Koordinatlar metrik projeksiyon aralığında (Easting: 100k-1M)."
            }
        return {"system": None, "confidence": 0, "reason": "Projeksiyon sınırları dışında."}