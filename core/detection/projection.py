from typing import Any, Dict, Tuple

from .base import DetectionStrategy


class ProjectionStrategy(DetectionStrategy):
    priority = 5

    def detect_swap(self, x: float, y: float) -> Tuple[float, float]:
        return x, y

    def suggest_crs(self, x: float, y: float) -> Dict[str, Any]:
        if 100000 <= abs(x) <= 1000000 and 0 <= abs(y) <= 10000000:
            return {
                "system": "DYNAMIC_WGS84_UTM",
                "confidence": 0.8,
                "reason": "Koordinatlar metrik projeksiyon aralığında görünüyor.",
                "reason_key": "resolver.projection_reason",
            }
        return {
            "system": None,
            "confidence": 0,
            "reason": "Projeksiyon sınırları dışında.",
            "reason_key": None,
        }
