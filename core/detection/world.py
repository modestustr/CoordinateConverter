# core/detection/world.py
from .base import DetectionStrategy
from typing import Tuple, Dict, Any

class GlobalStrategy(DetectionStrategy):
    priority = 1  # En düşük öncelik, en son kontrol edilir

    def detect_swap(self, x: float, y: float) -> Tuple[float, float]:
        # Swaps only if x is clearly latitude and y is clearly longitude
        if abs(x) <= 90 and abs(y) > 90:
            return y, x
        return x, y

    def suggest_crs(self, x: float, y: float) -> Dict[str, Any]:
        if -180 <= x <= 180 and -90 <= y <= 90:
            return {
                "system": "WGS84",
                "confidence": 0.5,
                "reason": "Koordinatlar global WGS84 coğrafi sınırları içerisinde."
            }
        return {"system": None, "confidence": 0, "reason": "Sınır dışı."}