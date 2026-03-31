# ui/components/map.py
import folium
import streamlit as st
from streamlit_folium import st_folium

from ui.i18n import t

def render_result_map(lat: float, lon: float):
    """Sonuç noktasını harita üzerinde gösterir."""
    try:
        m = folium.Map(location=[lat, lon], zoom_start=13)
        folium.Marker([lat, lon], tooltip="Result").add_to(m)
        st_folium(m, width="100%", height=400, key="result_map")
    except Exception:
        st.warning(t("map.warning.load_failed"))
