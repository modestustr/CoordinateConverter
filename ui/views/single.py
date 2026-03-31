import pandas as pd
import streamlit as st

from core.crs import format_to_dms_string
from ui.feedback import build_error_feedback
from ui.components.map import render_result_map
from ui.state import set_preset, swap_systems


def _set_coords_text(lat: float, lon: float) -> None:
    coord_text = f"{lat:.6f}, {lon:.6f}"
    st.session_state["coords"]["lat"] = lat
    st.session_state["coords"]["lon"] = lon
    st.session_state["coords"]["text"] = coord_text
    st.session_state["coords_text"] = coord_text


def _format_pair(x: float, y: float, is_geo: bool) -> str:
    if is_geo:
        return f"Lat: {y:.8f}°, Lon: {x:.8f}°"
    return f"X: {x:.3f}, Y: {y:.3f}"


def _format_diff(value: float, src_info: dict) -> str:
    precision = 8 if src_info.get("is_geo") else 4
    unit = "°" if src_info.get("is_geo") else src_info.get("unit", "birim")
    return f"{value:.{precision}f} {unit}"


def _format_accuracy(value: float) -> str:
    if value is None or value < 0:
        return "Belirtilmedi"
    return f"{value:.3f} m"


def _build_roundtrip_table(res: dict) -> pd.DataFrame:
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
                "Adım": "Orijinal giriş",
                x_label: f"{res['input_x']:.{precision}f}",
                y_label: f"{res['input_y']:.{precision}f}",
            },
            {
                "Adım": "Geri dönüş sonrası",
                x_label: f"{back_x:.{precision}f}",
                y_label: f"{back_y:.{precision}f}",
            },
            {
                "Adım": "Mutlak fark",
                x_label: _format_diff(diff_x, src_info),
                y_label: _format_diff(diff_y, src_info),
            },
        ]
    )


def _handle_initial_location(controller) -> None:
    if not st.session_state.get("gps_auto_attempted"):
        st.session_state["gps_auto_attempted"] = True
        st.session_state["gps_auto_pending"] = True

    if not st.session_state.get("gps_auto_pending"):
        return

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
        st.toast("Tarayıcı izni bulundu, mevcut konum yüklendi.", icon="📍")
        st.rerun()


def _handle_manual_location(controller) -> None:
    if not st.session_state.get("gps_active"):
        return

    loc = controller.get_gps_location(
        require_existing_permission=False,
        show_status=True,
        widget_key="manual_device_location",
    )
    if not loc:
        return

    if "error" not in loc and "lat" in loc and "lon" in loc:
        _set_coords_text(loc["lat"], loc["lon"])
        st.toast("Konum başarıyla alındı!", icon="✅")
        st.session_state["gps_active"] = False
        st.rerun()

    if "error" in loc:
        st.error(f"⚠️ {loc['error']}")
        st.session_state["gps_active"] = False


def _render_result_summary(res: dict) -> None:
    with st.container(border=True):
        st.caption(f"{res['t_info']['name']} • {res['t_meta']['description']}")
        if res["t_info"]["is_geo"]:
            st.write(f"## { _format_pair(res['output_x'], res['output_y'], True) }")
            st.write(
                f"**DMS:** `{format_to_dms_string(res['output_y'], True)}` , "
                f"`{format_to_dms_string(res['output_x'], False)}`"
            )
        else:
            st.write(
                f"## {res['t_info']['x_label']}: {res['output_x']:.3f} | "
                f"{res['t_info']['y_label']}: {res['output_y']:.3f}"
            )


def _render_scientific_proof(res: dict) -> None:
    verification = res["verification"]
    src_info = res["src_info"]
    diff_x, diff_y = verification["diff"]
    max_diff = max(diff_x, diff_y)
    back_x, back_y = verification["back"]

    with st.expander("🔬 Bilimsel İspat ve Geri Dönüş Kontrolü", expanded=True):
        st.caption(
            "Bu kontrol, noktayı önce hedef sisteme dönüştürür; ardından aynı sonucu "
            "yeniden kaynak sisteme geri çevirir. Geri dönen koordinat ile ilk giriş "
            "arasındaki fark ne kadar küçükse dönüşüm sayısal olarak o kadar tutarlıdır."
        )

        if verification["ok"]:
            st.success(
                f"Dönüşüm tutarlı görünüyor. Maksimum geri dönüş farkı "
                f"{_format_diff(max_diff, src_info)}."
            )
        else:
            st.warning(
                f"Geri dönüş kontrolünde beklenenden yüksek sapma görüldü. "
                f"Maksimum fark {_format_diff(max_diff, src_info)}."
            )

        c1, c2, c3 = st.columns(3)
        c1.metric("Maks. fark", _format_diff(max_diff, src_info))
        c2.metric(f"Δ {src_info.get('x_label', 'X')}", _format_diff(diff_x, src_info))
        c3.metric(f"Δ {src_info.get('y_label', 'Y')}", _format_diff(diff_y, src_info))

        st.write(f"**Dönüşüm yöntemi:** {res['t_meta']['description']}")
        st.write(f"**PROJ accuracy:** {_format_accuracy(res['t_meta'].get('accuracy', -1))}")
        st.write(f"**Çözülmüş hedef CRS:** `{res['resolved_tgt']}`")
        st.write(
            f"**Geri dönüş koordinatı:** `{_format_pair(back_x, back_y, src_info.get('is_geo', False))}`"
        )
        st.dataframe(_build_roundtrip_table(res), hide_index=True, width="stretch")


def render_single_conversion(controller, all_names):
    _handle_initial_location(controller)
    _handle_manual_location(controller)

    col_input, col_gps = st.columns([3, 1], vertical_alignment="bottom")
    with col_input:
        raw_input = st.text_input(
            "📍 Koordinatları Yapıştırın",
            key="coords_text",
            placeholder="39.93, 32.85",
        )
        st.session_state["coords"]["text"] = raw_input
        st.caption(
            "Tarayıcıda konum izni zaten varsa bulunduğunuz konum otomatik yüklenir; "
            "aksi durumda varsayılan Ankara koordinatları kullanılır."
        )

    with col_gps:
        if st.button(
            "🛰️ Konumumu Al",
            width="stretch",
            disabled=st.session_state.get("gps_active"),
        ):
            st.session_state["gps_active"] = True
            st.rerun()

    with st.expander("🚀 Hızlı Senaryolar"):
        p_col1, p_col2, p_col3, p_col4, p_col5 = st.columns(5)
        if p_col1.button("🌍 Google → UTM"):
            set_preset("*GPS (WGS84) (deg)", "WGS84 / UTM (Dinamik)")
        if p_col2.button("🛰️ GPS → Web"):
            set_preset("*GPS (WGS84) (deg)", "WGS 84 / Pseudo-Mercator")
        if p_col3.button("🏗️ WGS84 → ED50"):
            set_preset("*GPS (WGS84) (deg)", "ED50 (GCS)")
        if p_col4.button("🇹🇷 ITRF96 → GPS"):
            set_preset("ITRF96 / TM30 (Türkiye)", "*GPS (WGS84) (deg)")
        if p_col5.button("📐 ED50 → UTM 6°"):
            set_preset("ED50 / UTM zone 35N (6 Derece)", "*GPS (WGS84) (deg)")

    main_c1, main_c2, main_c3 = st.columns([10, 2, 10], vertical_alignment="bottom")
    with main_c1:
        src_sys = st.selectbox("📥 Kaynak", all_names, key="src_sys")
        if raw_input and st.session_state["auto_detect"]:
            res = controller.get_input_details(raw_input)
            suggestion = res["suggestion"]
            if suggestion["system"] and suggestion["system"] != src_sys:
                st.info(
                    f"🧠 Öneri: {suggestion['system']} "
                    f"(%{suggestion['confidence'] * 100:.0f})"
                )
                if st.button("Uygula"):
                    st.session_state["src_sys"] = suggestion["system"]
                    st.rerun()
    with main_c2:
        st.button("🔄", on_click=swap_systems, width="stretch")
    with main_c3:
        tgt_sys = st.selectbox("📤 Hedef", all_names, key="tgt_sys")

    if st.button("🚀 DÖNÜŞTÜR", type="primary", width="stretch"):
        try:
            res = controller.convert(raw_input, src_sys, tgt_sys)
            st.session_state["last_result"] = res
            st.session_state["history"].append(
                {
                    "Kaynak": src_sys,
                    "Hedef": tgt_sys,
                    "Girdi": _format_pair(res["input_x"], res["input_y"], res["src_info"]["is_geo"]),
                    "Sonuç": _format_pair(res["output_x"], res["output_y"], res["t_info"]["is_geo"]),
                    "Tutarlılık": _format_diff(max(res["verification"]["diff"]), res["src_info"]),
                }
            )
        except Exception as e:
            feedback = build_error_feedback(e)
            st.error(f"⚠️ {feedback['title']}")
            st.caption(feedback["detail"])
            if feedback["hint"]:
                st.info(feedback["hint"])

    if st.session_state["last_result"]:
        res = st.session_state["last_result"]
        _render_result_summary(res)
        _render_scientific_proof(res)

        map_lon, map_lat, _ = controller.get_map_preview(
            res["output_x"], res["output_y"], res["resolved_tgt"]
        )
        render_result_map(map_lat, map_lon)
