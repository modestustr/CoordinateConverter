from typing import Any, Dict, Tuple

from .base import DetectionStrategy


class TurkeyStrategy(DetectionStrategy):
    priority = 10

    def detect_swap(self, x: float, y: float) -> Tuple[float, float]:
        is_x_in_tr_lat = 35.0 <= x <= 43.0
        is_y_in_tr_lon = 25.0 <= y <= 46.0

        if is_x_in_tr_lat and is_y_in_tr_lon and x > y:
            return y, x
        return x, y

    def suggest_crs(self, x: float, y: float) -> Dict[str, Any]:
        if 25.0 <= x <= 46.0 and 35.0 <= y <= 43.0:
            return {
                "system": "WGS84",
                "confidence": 0.85,
                "reason": "Koordinatlar Türkiye sınırları içinde görünüyor.",
                "reason_key": "resolver.turkey_bbox_reason",
            }
        return {"system": None, "confidence": 0, "reason": None, "reason_key": None}
