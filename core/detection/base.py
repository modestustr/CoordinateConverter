# core/detection/base.py
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class DetectionStrategy(ABC):
    priority: int = 0  # Düşük öncelik varsayılan

    @abstractmethod
    def detect_swap(self, x: float, y: float) -> Tuple[float, float]:
        pass

    @abstractmethod
    def suggest_crs(self, x: float, y: float) -> Dict[str, Any]:
        pass