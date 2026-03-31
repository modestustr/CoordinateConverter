# core/utm.py
"""UTM Specific Utilities."""
import numpy as np

def detect_utm_zone(lon: float) -> int:
    """Calculate theoretical UTM zone based on longitude."""
    return int((lon + 180) / 6) + 1

def get_wgs84_utm_epsg(lon: float, lat: float) -> str:
    """Generate dynamic EPSG code for WGS84 UTM."""
    zone = detect_utm_zone(lon)
    prefix = "326" if lat >= 0 else "327"
    return f"EPSG:{prefix}{zone:02d}"

def get_wgs84_utm_epsg_vec(lon_arr: np.ndarray, lat_arr: np.ndarray) -> np.ndarray:
    """Vectorized version of EPSG generation for large datasets."""
    # NumPy ile hızlı zone ve prefix hesaplama
    zones = ((lon_arr + 180) / 6).astype(int) + 1
    prefixes = np.where(lat_arr >= 0, 32600, 32700)
    epsg_codes = prefixes + zones
    
    # Vektörize string birleştirme
    return np.char.add("EPSG:", epsg_codes.astype(str))