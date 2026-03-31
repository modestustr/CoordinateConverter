# services/system.py
from typing import List
from core.crs import get_all_system_names, resolve_crs_code

def get_validated_systems() -> List[str]:
    """Sistemin desteklediği geçerli sistemleri döner."""
    valid = []
    for name in get_all_system_names():
        try:
            resolve_crs_code(name)
            valid.append(name)
        except Exception:
            continue
    return sorted(valid)