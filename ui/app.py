# ui/app.py
import streamlit as st

from config.logging import configure_logging
from config.settings import APP_TITLE
from ui.controller import AppController
from ui.i18n import t
from ui.sidebar import render_sidebar
from ui.state import init_session_state
from ui.views.batch import render_batch_conversion
from ui.views.single import render_single_conversion

APP_CONTEXT_VERSION = "controller-v3"


def main():
    configure_logging()
    st.set_page_config(page_title=APP_TITLE, layout="wide")

    @st.cache_resource
    def get_app_context(version: str):
        from core.coord import CoordConverter

        _ = version
        engine = CoordConverter()
        return AppController(engine)

    controller = get_app_context(APP_CONTEXT_VERSION)
    init_session_state()
    all_names = controller.get_system_list()

    render_sidebar(controller, all_names)
    st.title(t("app.main_title"))

    tab_single, tab_batch = st.tabs([t("app.tab.single"), t("app.tab.batch")])

    with tab_single:
        render_single_conversion(controller, all_names)
    with tab_batch:
        render_batch_conversion(controller)
