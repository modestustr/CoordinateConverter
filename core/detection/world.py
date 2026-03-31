from typing import Any, Dict, Tuple

from .base import DetectionStrategy


class GlobalStrategy(DetectionStrategy):
    priority = 1

    def detect_swap(self, x: float, y: float) -> Tuple[float, float]:
        if abs(x) <= 90 and abs(y) > 90:
            return y, x
        return x, y

    def suggest_crs(self, x: float, y: float) -> Dict[str, Any]:
        if -180 <= x <= 180 and -90 <= y <= 90:
            return {
                "system": "WGS84",
                "confidence": 0.5,
                "reason": "Koordinatlar global WGS84 coğrafi sınırları içinde.",
                "reason_key": "resolver.global_bbox_reason",
            }
        return {"system": None, "confidence": 0, "reason": "Sınır dışında.", "reason_key": None}
