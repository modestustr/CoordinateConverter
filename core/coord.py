# core/coord.py
import logging
from functools import lru_cache
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from pyproj import CRS, Transformer

from core.crs import DYNAMIC_UTM_KEY, ErrorCode, resolve_crs_code
from core.utm import detect_utm_zone, get_wgs84_utm_epsg, get_wgs84_utm_epsg_vec

logger = logging.getLogger(__name__)

WGS84 = "EPSG:4326"


class SanityCheckResult(Dict):
    """Contract for sanity check responses."""

    valid: bool
    error_code: ErrorCode
    message: str
    context: Optional[str]


class CoordConverter:
    DEFAULT_TOLERANCE_METRIC = 0.1
    DEFAULT_TOLERANCE_GEO = 1e-7

    def _has_nan(self, x, y):
        try:
            x_isna = pd.isna(x).any() if not np.isscalar(x) else pd.isna(x)
            y_isna = pd.isna(y).any() if not np.isscalar(y) else pd.isna(y)
            return bool(x_isna or y_isna)
        except Exception:
            return True

    @lru_cache(maxsize=256)
    def get_crs_obj(self, crs_input: str):
        """Return a normalized CRS object."""
        code = resolve_crs_code(crs_input)
        return CRS(code)

    def get_transformer(self, src: str, tgt: str):
        """Return a cached transformer using normalized CRS codes."""
        s_code = resolve_crs_code(src)
        t_code = resolve_crs_code(tgt)
        return self._get_transformer_cached(s_code, t_code)

    @lru_cache(maxsize=512)
    def _get_transformer_cached(self, s_code: str, t_code: str):
        """Cache actual transformer instances by normalized CRS codes."""
        return Transformer.from_crs(s_code, t_code, always_xy=True)

    def _to_wgs84(self, x, y, s_code: str):
        if s_code == WGS84:
            return x, y
        transformer = self._get_transformer_cached(s_code, WGS84)
        return transformer.transform(x, y)

    def _resolve_dynamic_utm(self, x: float, y: float, src_code: str) -> str:
        """Resolve the dynamic WGS84 UTM target from input coordinates."""
        lon, lat = self._to_wgs84(x, y, src_code)
        return resolve_crs_code(get_wgs84_utm_epsg(lon, lat))

    def _create_sanity_result(
        self,
        valid: bool,
        code: ErrorCode = ErrorCode.SUCCESS,
        message: str = "",
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "valid": valid,
            "error_code": code,
            "message": message,
            "context": context,
        }

    def transform_point(
        self, x: float, y: float, src: str, tgt: str
    ) -> Tuple[float, float, str]:
        if self._has_nan(x, y):
            raise ValueError(f"[{ErrorCode.NAN_COORDINATE.value}] NaN koordinat verisi")

        s_code = resolve_crs_code(src)
        t_code = resolve_crs_code(tgt)

        if s_code == DYNAMIC_UTM_KEY:
            raise ValueError(
                f"[{ErrorCode.DYNAMIC_SOURCE_FORBIDDEN.value}] "
                "Kaynak sistem 'Dinamik UTM' olamaz."
            )

        if t_code == DYNAMIC_UTM_KEY:
            t_code = self._resolve_dynamic_utm(x, y, s_code)

        transformer = self._get_transformer_cached(s_code, t_code)
        rx, ry = transformer.transform(x, y)
        return rx, ry, t_code

    def sanity_check(self, x: float, y: float, crs_key: str) -> Dict[str, Any]:
        try:
            if self._has_nan(x, y):
                return self._create_sanity_result(
                    False, ErrorCode.NAN_COORDINATE, "NaN koordinat"
                )

            code = resolve_crs_code(crs_key)
            if code == DYNAMIC_UTM_KEY:
                return self._create_sanity_result(True)

            crs = self.get_crs_obj(code)

            if crs.is_geographic:
                if not (-180 <= x <= 180 and -90 <= y <= 90):
                    return self._create_sanity_result(
                        False,
                        ErrorCode.INVALID_GEO_RANGE,
                        "Geçersiz coğrafi aralık",
                    )

            lon, lat = self._to_wgs84(x, y, code)

            area = crs.area_of_use
            if area:
                if not (
                    area.west <= lon <= area.east and area.south <= lat <= area.north
                ):
                    return self._create_sanity_result(
                        False,
                        ErrorCode.OUT_OF_BOUNDS,
                        f"Kapsama alanı dışında ({area.name})",
                        context=area.name,
                    )

            return self._create_sanity_result(True)

        except Exception as e:
            return self._create_sanity_result(
                False, ErrorCode.RESOLUTION_ERROR, str(e)
            )

    def transform_dataframe(
        self, df: pd.DataFrame, x_col: str, y_col: str, src: str, tgt: str
    ) -> pd.DataFrame:
        s_code = resolve_crs_code(src)
        t_code = resolve_crs_code(tgt)

        if s_code == DYNAMIC_UTM_KEY:
            raise ValueError(
                f"[{ErrorCode.DYNAMIC_SOURCE_FORBIDDEN.value}] "
                "Kaynak sistem 'Dinamik UTM' olamaz."
            )

        res = df.copy()
        raw_x = df[x_col]
        raw_y = df[y_col]

        # Coerce invalid text to NaN so we can keep processing the rest of the file.
        numeric_x = pd.to_numeric(raw_x, errors="coerce")
        numeric_y = pd.to_numeric(raw_y, errors="coerce")
        in_x = numeric_x.to_numpy(dtype=float)
        in_y = numeric_y.to_numpy(dtype=float)

        target_x = np.full(len(df), np.nan)
        target_y = np.full(len(df), np.nan)
        status = np.full(len(df), "OK", dtype=object)
        error_codes = np.full(len(df), "", dtype=object)
        error_messages = np.full(len(df), "", dtype=object)

        invalid_numeric_mask = (
            (numeric_x.isna() & raw_x.notna()) | (numeric_y.isna() & raw_y.notna())
        ).to_numpy(dtype=bool)
        nan_mask = np.isnan(in_x) | np.isnan(in_y)
        missing_mask = nan_mask & ~invalid_numeric_mask

        if invalid_numeric_mask.any():
            status[invalid_numeric_mask] = "ERROR"
            error_codes[invalid_numeric_mask] = ErrorCode.INVALID_FORMAT.value
            error_messages[invalid_numeric_mask] = "Sayisal olmayan koordinat degeri."

        if missing_mask.any():
            status[missing_mask] = "ERROR"
            error_codes[missing_mask] = ErrorCode.NAN_COORDINATE.value
            error_messages[missing_mask] = "Eksik veya NaN koordinat verisi."

        transformable_mask = ~(invalid_numeric_mask | missing_mask)
        validated_mask = np.zeros(len(df), dtype=bool)

        # Apply the same validation contract used by single-point conversions.
        for idx in np.where(transformable_mask)[0]:
            check = self.sanity_check(float(in_x[idx]), float(in_y[idx]), src)
            if check["valid"]:
                validated_mask[idx] = True
                continue

            status[idx] = "ERROR"
            code = check.get("error_code", ErrorCode.RESOLUTION_ERROR)
            error_codes[idx] = code.value if isinstance(code, ErrorCode) else str(code)
            error_messages[idx] = check.get(
                "message", "Koordinat dogrulamasi basarisiz."
            )

        if t_code == DYNAMIC_UTM_KEY:
            if validated_mask.any():
                lon, lat = self._to_wgs84(
                    in_x[validated_mask], in_y[validated_mask], s_code
                )
                epsg_arr = get_wgs84_utm_epsg_vec(lon, lat)

                for epsg in np.unique(epsg_arr):
                    sub_mask = epsg_arr == epsg
                    valid_indices = np.where(validated_mask)[0]
                    target_indices = valid_indices[sub_mask]
                    global_mask = np.zeros(len(df), dtype=bool)
                    global_mask[target_indices] = True

                    transformer = self._get_transformer_cached(s_code, str(epsg))
                    tx, ty = transformer.transform(
                        in_x[global_mask], in_y[global_mask]
                    )
                    target_x[global_mask] = tx
                    target_y[global_mask] = ty
        else:
            if validated_mask.any():
                transformer = self._get_transformer_cached(s_code, t_code)
                nx, ny = transformer.transform(
                    in_x[validated_mask], in_y[validated_mask]
                )
                target_x[validated_mask] = nx
                target_y[validated_mask] = ny

        non_finite_mask = validated_mask & ~(
            np.isfinite(target_x) & np.isfinite(target_y)
        )
        if non_finite_mask.any():
            target_x[non_finite_mask] = np.nan
            target_y[non_finite_mask] = np.nan
            status[non_finite_mask] = "ERROR"
            error_codes[non_finite_mask] = ErrorCode.RESOLUTION_ERROR.value
            error_messages[non_finite_mask] = "Donusum sonucu sonlu degil."

        res[f"Hedef_{x_col}"] = target_x
        res[f"Hedef_{y_col}"] = target_y
        res["Durum"] = status
        res["Hata_Kodu"] = error_codes
        res["Hata_Mesaji"] = error_messages
        return res

    def verify_conversion(
        self, x: float, y: float, src: str, tgt: str
    ) -> Tuple[bool, tuple, tuple]:
        try:
            tx, ty, real_tgt = self.transform_point(x, y, src, tgt)
            rx, ry, _ = self.transform_point(tx, ty, real_tgt, src)

            diff = (abs(x - rx), abs(y - ry))

            s_code = resolve_crs_code(src)
            is_geo = self.get_crs_obj(s_code).is_geographic
            tol = (
                self.DEFAULT_TOLERANCE_GEO if is_geo else self.DEFAULT_TOLERANCE_METRIC
            )

            return max(diff) < tol, diff, (rx, ry)

        except Exception:
            return False, (0, 0), (0, 0)

    def get_transformer_info(
        self, src: str, tgt: str, x: float = None, y: float = None
    ) -> Dict[str, Any]:
        """Return metadata about the transformation."""
        try:
            s_code = resolve_crs_code(src)
            t_code = resolve_crs_code(tgt)

            if s_code == DYNAMIC_UTM_KEY:
                return {"description": "Dinamik UTM kaynak olamaz", "accuracy": -1}

            if t_code == DYNAMIC_UTM_KEY and x is not None:
                resolved = self._resolve_dynamic_utm(x, y, s_code)

                epsg = int(resolved.split(":")[1])
                zone = epsg % 100
                hemi = "N" if 32600 <= epsg < 32700 else "S"

                return {
                    "description": f"UTM Zone {zone}{hemi}",
                    "accuracy": -1,
                }

            if t_code == DYNAMIC_UTM_KEY:
                return {"description": "Dinamik UTM", "accuracy": -1}

            transformer = self.get_transformer(s_code, t_code)

            return {
                "description": transformer.description,
                "accuracy": transformer.accuracy,
            }

        except Exception as e:
            return {"description": str(e), "accuracy": -1}

    def get_utm_zone_info(self, lon: float) -> int:
        return detect_utm_zone(lon) if lon is not None else 0
