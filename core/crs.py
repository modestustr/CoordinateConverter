"""CRS utilities and metadata handling."""

from enum import Enum
from typing import Any, Dict

from pyproj import CRS as _CRS

# Constants
DYNAMIC_UTM_KEY = "DYNAMIC_WGS84_UTM"


# Enterprise Confidence Thresholds
CONFIDENCE_THRESHOLD_AUTO = 0.8
CONFIDENCE_THRESHOLD_SUGGEST = 0.5


class ErrorCode(Enum):
    INVALID_FORMAT = "INVALID_FORMAT"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"
    INVALID_GEO_RANGE = "INVALID_GEO_RANGE"
    RESOLUTION_ERROR = "RESOLUTION_ERROR"
    NAN_COORDINATE = "NAN_COORDINATE"
    DYNAMIC_SOURCE_FORBIDDEN = "DYNAMIC_SOURCE_FORBIDDEN"
    SUCCESS = "SUCCESS"


class CRSResolutionError(Exception):
    def __init__(self, message: str, code: ErrorCode = ErrorCode.RESOLUTION_ERROR):
        super().__init__(message)
        self.code = code


def get_all_system_names() -> list:
    """Return a sorted list of all available system names."""
    from data.systems import SYSTEM_DATABASE  # type: ignore

    return sorted(SYSTEM_DATABASE.keys())


def resolve_crs_code(key: str) -> str:
    """Map user-friendly keys to Proj/EPSG codes."""
    from data.systems import SYSTEM_DATABASE  # type: ignore

    code = SYSTEM_DATABASE.get(key, key)

    if code in ["WGS84", "EPSG:4326"]:
        return "EPSG:4326"
    if code in ["GOOGLE", "EPSG:3857"]:
        return "EPSG:3857"
    if code == DYNAMIC_UTM_KEY:
        return DYNAMIC_UTM_KEY

    try:
        if code.startswith("EPSG:"):
            _CRS.from_user_input(code)
            return code
        _CRS.from_user_input(code)
        _CRS.from_user_input(code)
        return code
    except Exception as e:
        raise CRSResolutionError(f"Hatalı CRS Tanımı: {key} ({str(e)})")


def get_crs_unit_info(key: str) -> Dict[str, Any]:
    """Extract metadata from a CRS."""
    try:
        code = resolve_crs_code(key)
        if code == DYNAMIC_UTM_KEY:
            return {
                "unit": "metre",
                "is_geo": False,
                "x_label": "Easting (X)",
                "y_label": "Northing (Y)",
                "name": "WGS84 UTM (Dinamik)",
            }

        crs_obj = _CRS(code)
        axis_x = crs_obj.axis_info[0]
        axis_y = crs_obj.axis_info[1]

        # The app consistently uses always_xy=True, so geographic axes should
        # be shown as longitude/latitude regardless of EPSG native axis order.
        if crs_obj.is_geographic:
            return {
                "unit": axis_x.unit_name,
                "is_geo": True,
                "x_label": "Boylam (Longitude)",
                "y_label": "Enlem (Latitude)",
                "name": crs_obj.name,
            }

        return {
            "unit": axis_x.unit_name,
            "is_geo": False,
            "x_label": axis_x.name,
            "y_label": axis_y.name,
            "name": crs_obj.name,
        }
    except Exception:
        return {
            "unit": "Birim yok",
            "is_geo": False,
            "x_label": "X",
            "y_label": "Y",
            "name": "Bilinmiyor",
        }


def format_to_dms_string(dd: float, is_lat: bool = True) -> str:
    """Convert decimal degrees to a DMS string."""
    is_positive = dd >= 0
    dd_abs = abs(dd)
    total_seconds = round(dd_abs * 3600, 2)
    minutes, seconds = divmod(total_seconds, 60)
    degrees, minutes = divmod(minutes, 60)
    suffix = ("N" if is_positive else "S") if is_lat else ("E" if is_positive else "W")
    return f"{int(degrees):02d}°{int(minutes):02d}′{seconds:05.2f}″{suffix}"


def convert_unit(value: float, unit: str) -> float:
    """Perform simple unit conversion for display purposes."""
    u = unit.lower()
    if u in ["kilometre", "kilometer"]:
        return value / 1000
    if u in ["foot", "feet"]:
        return value * 3.280839895
    return value
