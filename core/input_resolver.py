# core/input_resolver.py
import re
from typing import Dict, Any, Tuple, Optional
from core.detection import get_all_strategies

# Enterprise Confidence Thresholds
CONFIDENCE_AUTO_ACCEPT = 0.8
CONFIDENCE_SUGGEST = 0.5


class InputResolver:
    """
    Domain Intelligence Layer: Ham veriyi anlamlı bir Coordinate nesnesine (x, y) dönüştürür.
    """
    def __init__(self):
        # Stratejileri registry üzerinden dinamik al
        self.strategies = get_all_strategies()

    def resolve(self, raw_input: str) -> Dict[str, Any]:
        raw_input = raw_input.strip()
        ix, iy = self._parse_coords(raw_input)

        if ix is None or iy is None:
            return {
                "x": None,
                "y": None,
                "suggestion": {
                    "system": None,
                    "confidence": 0,
                    "reason": "Geçersiz format.",
                },
                "is_valid": False,
            }

        # Akıllı normalizasyon (Swap/Takas tespiti)
        final_x, final_y = self._apply_strategies_swap(ix, iy)

        # Puanlama bazlı en iyi sistem önerisi (Confidence Scoring)
        best_suggestion = self._get_best_suggestion(final_x, final_y)

        return {
            "x": final_x,
            "y": final_y,
            "suggestion": best_suggestion,
            "is_valid": True,
        }

    def _parse_coords(self, raw_input: str) -> Tuple[Optional[float], Optional[float]]:
        """Gelişmiş metin parçalama: DMS ve DD formatlarını ayırt eder."""
        # DMS pattern (Suffix destekli)
        pattern = r"(\d+(?:\.\d+)?)\s*[°\s]*\s*(?:(\d+)\s*[′'\s]\s*)?(?:(\d+(?:\.\d+)?)\s*[″\"\s]\s*)?([NSEWnsew])"
        matches = re.findall(pattern, raw_input)

        if len(matches) == 2:
            lon, lat = None, None
            for groups in matches:
                d_val = float(groups[0])
                m_val = float(groups[1]) if groups[1] and groups[1].strip() else 0.0
                s_val = float(groups[2]) if groups[2] and groups[2].strip() else 0.0
                h_val = groups[3].upper()
                dd = d_val + (m_val / 60.0) + (s_val / 3600.0)
                if h_val in ["S", "W"]: 
                    dd = -dd
                if h_val in ["N", "S"]: 
                    lat = dd
                if h_val in ["E", "W"]: 
                    lon = dd
            if lon is not None and lat is not None:
                return lon, lat

        # Sayısal ayırma (DD veya Projeksiyon)
        try:
            parts = [p.strip() for p in raw_input.replace(",", " ").split()]
            if len(parts) >= 2:
                return float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            pass

        return None, None

    def _apply_strategies_swap(self, x: float, y: float) -> Tuple[float, float]:
        fx, fy = x, y
        for strategy in self.strategies:
            nx, ny = strategy.detect_swap(fx, fy)
            if (nx, ny) != (fx, fy):
                return nx, ny
        return fx, fy

    def _get_best_suggestion(self, x: float, y: float) -> Dict[str, Any]:
        suggestions = []
        for strategy in self.strategies:
            sug = strategy.suggest_crs(x, y)
            if sug.get("system"):
                suggestions.append(sug)

        if not suggestions:
            return {"system": None, "confidence": 0, "reason": "Eşleşen sistem bulunamadı."}

        return max(suggestions, key=lambda s: s["confidence"])