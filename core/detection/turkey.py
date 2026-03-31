# core/detection/turkey.py
from .base import DetectionStrategy
from typing import Tuple, Dict, Any

class TurkeyStrategy(DetectionStrategy):
    priority = 10  # Bölgesel stratejiler genel stratejilerden (World) önce çalışmalı

    def detect_swap(self, x: float, y: float) -> Tuple[float, float]:
        """Türkiye koordinatları için Lat/Lon yer değiştirme kontrolü."""
        is_x_in_tr_lat = 35.0 <= x <= 43.0
        is_y_in_tr_lon = 25.0 <= y <= 46.0
        
        if is_x_in_tr_lat and is_y_in_tr_lon:
            if x > y: # Lat > Lon (Typical TR user error)
                return y, x
        return x, y

    def suggest_crs(self, x: float, y: float) -> Dict[str, Any]:
        """Koordinatlar Türkiye içindeyse uygun CRS önerir."""
        if 25.0 <= x <= 46.0 and 35.0 <= y <= 43.0:
             return {
                 "system": "WGS84",
                 "confidence": 0.85,
                 "reason": "Koordinatlar Türkiye bounding box içerisinde (Lat: 36-42, Lon: 26-45)."
             }
        return {"system": None, "confidence": 0, "reason": None}