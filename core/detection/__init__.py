# core/detection/__init__.py
from .base import DetectionStrategy
from .world import GlobalStrategy
from .turkey import TurkeyStrategy
from .projection import ProjectionStrategy

# Açık kayıt (Explicit Registry) ile flakiness önlenir
STRATEGY_REGISTRY = [
    TurkeyStrategy,
    ProjectionStrategy,
    GlobalStrategy,
]

def get_all_strategies():
    """Mevcut tüm stratejileri öncelik sırasına göre döner."""
    strategies = [cls() for cls in STRATEGY_REGISTRY]
    return sorted(strategies, key=lambda x: x.priority, reverse=True)

__all__ = ["DetectionStrategy", "GlobalStrategy", "TurkeyStrategy", "ProjectionStrategy", "get_all_strategies"]