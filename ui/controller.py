# ui/controller.py
import logging
import uuid
from typing import Any, Dict, List, Tuple

import pandas as pd

from core.crs import ErrorCode, get_crs_unit_info
from core.input_resolver import InputResolver
from services.batch import process_batch_transform
from services.device.gps import get_device_location
from services.export import export_history_to_csv
from services.system import get_validated_systems

DYNAMIC_UTM_KEY = "DYNAMIC_WGS84_UTM"
logger = logging.getLogger(__name__)


class AppController:
    def __init__(self, engine):
        self.engine = engine
        self.resolver = InputResolver()

    def get_system_list(self) -> List[str]:
        """Return the validated system list for the UI."""
        return get_validated_systems()

    def get_input_details(self, raw_input: str) -> Dict[str, Any]:
        """Delegate input parsing and suggestion logic to the resolver."""
        details = self.resolver.resolve(raw_input)

        if details["suggestion"]["system"] == "WGS84":
            details["suggestion"]["system"] = "*GPS (WGS84) (deg)"
        elif details["suggestion"]["system"] == DYNAMIC_UTM_KEY:
            details["suggestion"]["system"] = "WGS84 / UTM (Dinamik)"

        return details

    def parse_input_coords(self, raw_input: str) -> Tuple[float | None, float | None]:
        """Parse raw input and return coordinates as (lon, lat)."""
        details = self.get_input_details(raw_input)
        return details["x"], details["y"]

    def transform_batch(
        self, df: pd.DataFrame, x_col: str, y_col: str, src: str, tgt: str
    ) -> pd.DataFrame:
        """Delegate batch transformation to the service layer."""
        return process_batch_transform(self.engine, df, x_col, y_col, src, tgt)

    def format_history_for_export(self, history_data: List[Dict]) -> str:
        """Delegate export formatting to the service layer."""
        return export_history_to_csv(history_data)

    def get_gps_location(
        self,
        require_existing_permission: bool = False,
        show_status: bool = True,
        widget_key: str = "get_device_location",
    ) -> Any:
        """Fetch device location via the infrastructure service."""
        return get_device_location(
            require_existing_permission=require_existing_permission,
            show_status=show_status,
            widget_key=widget_key,
        )

    def get_map_preview(
        self, x: float, y: float, src_sys: str
    ) -> Tuple[float, float, str]:
        """Convert coordinates to WGS84 for map preview rendering."""
        return self.engine.transform_point(x, y, src_sys, "EPSG:4326")

    def convert(self, raw_input: str, src_sys: str, tgt_sys: str) -> Dict[str, Any]:
        """Convert raw input and return conversion output with verification info."""
        trace_id = str(uuid.uuid4())[:8]
        logger.info(f"[{trace_id}] Request: {raw_input} | Path: {src_sys} -> {tgt_sys}")

        details = self.get_input_details(raw_input)
        ix, iy = details["x"], details["y"]

        if ix is None or iy is None:
            msg = f"[{ErrorCode.INVALID_FORMAT.value}] Geçersiz koordinat formatı."
            logger.error(f"[{trace_id}] {msg}")
            raise ValueError(msg)

        src_info = get_crs_unit_info(src_sys)
        t_info = get_crs_unit_info(tgt_sys)

        check = self.engine.sanity_check(ix, iy, src_sys)
        if not check["valid"]:
            logger.warning(
                f"[{trace_id}] Validation Failed: {check['error_code']} - {check['message']}"
            )
            error_code = check.get("error_code")
            if isinstance(error_code, ErrorCode) and error_code != ErrorCode.SUCCESS:
                raise ValueError(f"[{error_code.value}] {check['message']}")
            raise ValueError(check["message"])

        rx, ry, resolved_tgt = self.engine.transform_point(ix, iy, src_sys, tgt_sys)

        ok, diff, back = self.engine.verify_conversion(ix, iy, src_sys, tgt_sys)
        t_meta = self.engine.get_transformer_info(src_sys, tgt_sys, ix, iy)

        return {
            "input_x": ix,
            "input_y": iy,
            "src_sys": src_sys,
            "src_info": src_info,
            "output_x": rx,
            "output_y": ry,
            "resolved_tgt": resolved_tgt,
            "t_meta": t_meta,
            "t_info": t_info,
            "verification": {
                "ok": ok,
                "diff": diff,
                "back": back,
            },
            "unit_choice": "Derece" if t_info["is_geo"] else "Metre",
        }
