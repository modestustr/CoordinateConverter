from typing import Sequence
from ui.utils.df_i18n import translate_dataframe_columns

import pandas as pd
import streamlit as st

from config.settings import (
    APP_VERSION,
    ENV,
    GEOCODE_TIMEOUT_SECONDS,
    MAX_UPLOAD_SIZE_MB,
    SHOW_DEBUG_INFO,
)
from ui.i18n import LANGUAGE_LABELS, get_language, t


def _build_system_status(system_names: Sequence[str]) -> dict[str, object]:
    system_count = len(system_names)
    return {"healthy": system_count > 0, "system_count": system_count}


def render_sidebar(controller, system_names):
    """Render the application sidebar."""
    status = _build_system_status(system_names)
    lang = get_language()

    st.sidebar.title(t("sidebar.title"))
    st.sidebar.selectbox(
        t("sidebar.language"),
        options=list(LANGUAGE_LABELS.keys()),
        format_func=lambda code: LANGUAGE_LABELS[code],
        key="lang",
    )
    lang = get_language()
    st.sidebar.caption(t("sidebar.version_env", version=APP_VERSION, env=ENV.upper()))

    if status["healthy"]:
        st.sidebar.success(t("sidebar.status.ready"))
        st.sidebar.caption(
            t("sidebar.status.ready_detail", count=status["system_count"])
        )
    else:
        st.sidebar.error(t("sidebar.status.not_ready"))
        st.sidebar.caption(t("sidebar.status.not_ready_detail"))

    if SHOW_DEBUG_INFO:
        st.sidebar.caption(
            t(
                "sidebar.debug",
                upload_mb=MAX_UPLOAD_SIZE_MB,
                timeout_s=GEOCODE_TIMEOUT_SECONDS,
            )
        )

    st.sidebar.divider()
    st.sidebar.info(t("sidebar.info"))
    st.sidebar.markdown(t("sidebar.about"))

    st.sidebar.subheader(t("sidebar.technologies"))
    st.sidebar.caption(t("sidebar.tech.engine"))
    st.sidebar.caption(t("sidebar.tech.ui"))
    st.sidebar.caption(t("sidebar.tech.map"))
    st.sidebar.caption(t("sidebar.tech.geocoding"))
    st.sidebar.caption(t("sidebar.tech.gps"))

    st.sidebar.subheader(t("sidebar.sources"))
    st.sidebar.caption(t("sidebar.source.epsg"))
    st.sidebar.caption(t("sidebar.source.spatial"))

    if st.session_state.get("history"):
        st.sidebar.divider()
        st.sidebar.subheader(t("sidebar.history"))
        history_df = pd.DataFrame(st.session_state["history"]).tail(5)
        display_df = translate_dataframe_columns(history_df, lang)
        st.sidebar.dataframe(
            display_df,
            hide_index=True,
            width="stretch",
        )

        csv_content = controller.format_history_for_export(st.session_state["history"])
        st.sidebar.download_button(
            t("sidebar.download_history"),
            data=csv_content.encode("utf-8"),
            file_name="koordinat_gecmisi.csv",
            mime="text/csv",
        )

        if st.sidebar.button(t("sidebar.clear_history")):
            st.session_state["history"] = []
            st.rerun()
