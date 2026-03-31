from typing import Sequence

import pandas as pd
import streamlit as st

from config.settings import (
    APP_VERSION,
    ENV,
    GEOCODE_TIMEOUT_SECONDS,
    MAX_UPLOAD_SIZE_MB,
    SHOW_DEBUG_INFO,
)


ABOUT_TEXT = """
Bu arac, karmasik cografi donusum sureclerini daha erisilebilir hale getirmek
icin tasarlandi. Jeodezik motor olarak `pyproj`, arayuz tarafinda `Streamlit`
kullanilir.
"""


def _build_system_status(system_names: Sequence[str]) -> dict[str, object]:
    system_count = len(system_names)
    healthy = system_count > 0
    return {
        "healthy": healthy,
        "label": "Donusum sistemi hazir" if healthy else "Donusum sistemi hazir degil",
        "detail": (
            f"Secilebilir {system_count} koordinat sistemi hazir."
            if healthy
            else "Kaynak ve hedef sistem listesi yuklenemedi."
        ),
        "system_count": system_count,
    }


def render_sidebar(controller, system_names):
    """Render the application sidebar."""
    status = _build_system_status(system_names)

    st.sidebar.title("Bilgi Paneli")
    st.sidebar.caption(f"Surum: `{APP_VERSION}` | Ortam: `{ENV.upper()}`")

    if status["healthy"]:
        st.sidebar.success(status["label"])
    else:
        st.sidebar.error(status["label"])
    st.sidebar.caption(status["detail"])

    if SHOW_DEBUG_INFO:
        st.sidebar.caption(
            f"Debug: upload={MAX_UPLOAD_SIZE_MB} MB, "
            f"geocode timeout={GEOCODE_TIMEOUT_SECONDS} sn"
        )

    st.sidebar.divider()
    st.sidebar.info("Global EPSG veri tabanini kullanarak hassas donusum yapar.")
    st.sidebar.markdown(ABOUT_TEXT)

    st.sidebar.subheader("Teknolojiler")
    st.sidebar.caption("Engine: PROJ / PyProj")
    st.sidebar.caption("Arayuz: Streamlit")
    st.sidebar.caption("Harita: OpenStreetMap / Esri")
    st.sidebar.caption("Geocoding: Nominatim API")
    st.sidebar.caption("GPS: JS-Eval")

    st.sidebar.subheader("Veri Kaynaklari")
    st.sidebar.caption("EPSG Registry")
    st.sidebar.caption("SpatialReference.org")

    if st.session_state.get("history"):
        st.sidebar.divider()
        st.sidebar.subheader("Islem Gecmisi")
        history_df = pd.DataFrame(st.session_state["history"]).tail(5)
        st.sidebar.dataframe(history_df, hide_index=True)

        csv_content = controller.format_history_for_export(st.session_state["history"])
        st.sidebar.download_button(
            "Gecmisi CSV Olarak Indir",
            data=csv_content.encode("utf-8"),
            file_name="koordinat_gecmisi.csv",
            mime="text/csv",
        )

        if st.sidebar.button("Gecmisi Temizle"):
            st.session_state["history"] = []
            st.rerun()
