import pandas as pd
import streamlit as st

from core.crs import format_to_dms_string
from ui.components.map import render_result_map
from ui.feedback import build_error_feedback
from ui.i18n import get_language, t, translate_text
from ui.state import set_preset, swap_systems


def _set_coords_text(lat: float, lon: float) -> None:
    coord_text = f"{lat:.6f}, {lon:.6f}"
    st.session_state["coords"]["lat"] = lat
    st.session_state["coords"]["lon"] = lon
    st.session_state["coords"]["text"] = coord_text
    st.session_state["coords_text"] = coord_text


def _format_pair(x: float, y: float, is_geo: bool, lang: str) -> str:
    if is_geo:
        return translate_text("single.result.latlon", lang, lat=y, lon=x)
    return translate_text("single.result.xy", lang, x=x, y=y)


def _format_diff(value: float, src_info: dict) -> str:
    precision = 8 if src_info.get("is_geo") else 4
    unit = "°" if src_info.get("is_geo") else src_info.get("unit", "birim")
    return f"{value:.{precision}f} {unit}"


def _format_accuracy(value: float, lang: str) -> str:
    if value is None or value < 0:
        return translate_text("single.result.not_specified", lang)
    return f"{value:.3f} m"


def _build_roundtrip_table(res: dict, lang: str) -> pd.DataFrame:
    src_info = res["src_info"]
    x_label = src_info.get("x_label", "X")
    y_label = src_info.get("y_label", "Y")
    is_geo = src_info.get("is_geo", False)
    back_x, back_y = res["verification"]["back"]
    diff_x, diff_y = res["verification"]["diff"]
    precision = 8 if is_geo else 3

    return pd.DataFrame(
        [
            {
                translate_text("single.table.step", lang): translate_text("single.table.original", lang),
                x_label: f"{res['input_x']:.{precision}f}",
                y_label: f"{res['input_y']:.{precision}f}",
            },
            {
                translate_text("single.table.step", lang): translate_text("single.table.roundtrip", lang),
                x_label: f"{back_x:.{precision}f}",
                y_label: f"{back_y:.{precision}f}",
            },
            {
                translate_text("single.table.step", lang): translate_text("single.table.abs_diff", lang),
                x_label: _format_diff(diff_x, src_info),
                y_label: _format_diff(diff_y, src_info),
            },
        ]
    )


def _translate_location_error(loc: dict, lang: str) -> str:
    return translate_text(f"gps.error.{loc.get('error_code', 'location_unavailable')}", lang)


def _handle_initial_location(controller) -> None:
    if not st.session_state.get("gps_auto_attempted"):
        st.session_state["gps_auto_attempted"] = True
        st.session_state["gps_auto_pending"] = True

    if not st.session_state.get("gps_auto_pending"):
        return

    lang = get_language()
    loc = controller.get_gps_location(
        require_existing_permission=True,
        show_status=False,
        widget_key="auto_device_location",
    )
    if not loc:
        return

    st.session_state["gps_auto_pending"] = False
    if "lat" in loc and "lon" in loc:
        _set_coords_text(loc["lat"], loc["lon"])
        st.toast(translate_text("single.location.auto_loaded", lang), icon="📍")
        st.rerun()


def _handle_manual_location(controller) -> None:
    if not st.session_state.get("gps_active"):
        return

    lang = get_language()
    loc = controller.get_gps_location(
        require_existing_permission=False,
        show_status=True,
        widget_key="manual_device_location",
        status_message=translate_text("gps.waiting_permission", lang),
    )
    if not loc:
        return

    if "error_code" not in loc and "lat" in loc and "lon" in loc:
        _set_coords_text(loc["lat"], loc["lon"])
        st.toast(translate_text("single.location.manual_success", lang), icon="✅")
        st.session_state["gps_active"] = False
        st.rerun()

    if "error_code" in loc:
        st.error(f"⚠️ {_translate_location_error(loc, lang)}")
        st.session_state["gps_active"] = False


def _render_result_summary(res: dict, lang: str) -> None:
    with st.container(border=True):
        st.caption(f"{res['t_info']['name']} • {res['t_meta']['description']}")
        if res["t_info"]["is_geo"]:
            st.write(f"## {_format_pair(res['output_x'], res['output_y'], True, lang)}")
            st.write(
                translate_text(
                    "single.result.dms",
                    lang,
                    lat_dms=format_to_dms_string(res["output_y"], True),
                    lon_dms=format_to_dms_string(res["output_x"], False),
                )
            )
        else:
            st.write(f"## {_format_pair(res['output_x'], res['output_y'], False, lang)}")


def _render_scientific_proof(res: dict, lang: str) -> None:
    verification = res["verification"]
    src_info = res["src_info"]
    diff_x, diff_y = verification["diff"]
    max_diff = max(diff_x, diff_y)
    back_x, back_y = verification["back"]

    with st.expander(t("single.proof.title"), expanded=True):
        st.caption(t("single.proof.caption"))

        if verification["ok"]:
            st.success(
                t("single.proof.ok", value=_format_diff(max_diff, src_info))
            )
        else:
            st.warning(
                t("single.proof.warn", value=_format_diff(max_diff, src_info))
            )

        c1, c2, c3 = st.columns(3)
        c1.metric(t("single.proof.max_diff"), _format_diff(max_diff, src_info))
        c2.metric(f"Δ {src_info.get('x_label', 'X')}", _format_diff(diff_x, src_info))
        c3.metric(f"Δ {src_info.get('y_label', 'Y')}", _format_diff(diff_y, src_info))

        st.write(t("single.proof.method", method=res["t_meta"]["description"]))
        st.write(
            t(
                "single.proof.accuracy",
                accuracy=_format_accuracy(res["t_meta"].get("accuracy", -1), lang),
            )
        )
        st.write(t("single.proof.resolved_crs", crs=res["resolved_tgt"]))
        st.write(
            t(
                "single.proof.back_coords",
                coords=_format_pair(
                    back_x,
                    back_y,
                    src_info.get("is_geo", False),
                    lang,
                ),
            )
        )
        st.dataframe(_build_roundtrip_table(res, lang), hide_index=True, width="stretch")


def render_single_conversion(controller, all_names):
    _handle_initial_location(controller)
    _handle_manual_location(controller)
    lang = get_language()

    col_input, col_gps = st.columns([3, 1], vertical_alignment="bottom")
    with col_input:
        raw_input = st.text_input(
            t("single.input.label"),
            key="coords_text",
            placeholder="39.93, 32.85",
        )
        st.session_state["coords"]["text"] = raw_input
        st.caption(t("single.input.caption"))

    with col_gps:
        if st.button(
            t("single.button.location"),
            width="stretch",
            disabled=st.session_state.get("gps_active"),
        ):
            st.session_state["gps_active"] = True
            st.rerun()

    with st.expander(t("single.scenarios.title")):
        p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5)
        if p_col1.button(t("single.scenario.google_utm")):
            set_preset("*GPS (WGS84) (deg)", "WGS84 / UTM (Dinamik)")
        if p_col2.button(t("single.scenario.gps_web")):
            set_preset("*GPS (WGS84) (deg)", "WGS 84 / Pseudo-Mercator")
        if p_col3.button(t("single.scenario.wgs84_ed50")):
            set_preset("*GPS (WGS84) (deg)", "ED50 (GCS)")
        if p_col4.button(t("single.scenario.itrf96_gps")):
            set_preset("ITRF96 / TM30 (Türkiye)", "*GPS (WGS84) (deg)")
        if p_col5.button(t("single.scenario.ed50_utm")):
            set_preset("ED50 / UTM zone 35N (6 Derece)", "*GPS (WGS84) (deg)")

    main_c1, main_c2, main_c3 = st.columns([10, 2, 10], vertical_alignment="bottom")
    with main_c1:
        src_sys = st.selectbox(t("single.source"), all_names, key="src_sys")
        if raw_input and st.session_state["auto_detect"]:
            res = controller.get_input_details(raw_input)
            suggestion = res["suggestion"]
            if suggestion["system"] and suggestion["system"] != src_sys:
                st.info(
                    f"{t('single.suggestion', system=suggestion['system'], confidence=suggestion['confidence'] * 100)} "
                    f"- {translate_text(suggestion.get('reason_key') or '', lang) if suggestion.get('reason_key') else suggestion.get('reason', '')}"
                )
                if st.button(t("single.apply")):
                    st.session_state["src_sys"] = suggestion["system"]
                    st.rerun()
    with main_c2:
        st.button("🔄", on_click=swap_systems, width="stretch")
    with main_c3:
        tgt_sys = st.selectbox(t("single.target"), all_names, key="tgt_sys")

    if st.button(t("single.convert"), type="primary", width="stretch"):
        try:
            res = controller.convert(raw_input, src_sys, tgt_sys)
            st.session_state["last_result"] = res
            st.session_state["history"].append(
                {
                    "Kaynak": src_sys,
                    "Hedef": tgt_sys,
                    "Girdi": _format_pair(
                        res["input_x"], res["input_y"], res["src_info"]["is_geo"], lang
                    ),
                    "Sonuç": _format_pair(
                        res["output_x"], res["output_y"], res["t_info"]["is_geo"], lang
                    ),
                    "Tutarlılık": _format_diff(
                        max(res["verification"]["diff"]), res["src_info"]
                    ),
                }
            )
        except Exception as e:
            feedback = build_error_feedback(e, lang)
            st.error(f"⚠️ {feedback['title']}")
            st.caption(feedback["detail"])
            if feedback["hint"]:
                st.info(feedback["hint"])

    if st.session_state["last_result"]:
        res = st.session_state["last_result"]
        _render_result_summary(res, lang)
        _render_scientific_proof(res, lang)

        map_lon, map_lat, _ = controller.get_map_preview(
            res["output_x"], res["output_y"], res["resolved_tgt"]
        )
        render_result_map(map_lat, map_lon)
