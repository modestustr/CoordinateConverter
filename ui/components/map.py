# ui/components/map.py
import folium
from streamlit_folium import st_folium
import streamlit as st

def render_result_map(lat: float, lon: float):
    """Sonuç noktasını harita üzerinde gösterir."""
    try:
        m = folium.Map(location=[lat, lon], zoom_start=13)
        folium.Marker([lat, lon], tooltip="Sonuç").add_to(m)
        st_folium(m, width="100%", height=400, key="result_map")
    except Exception:
        st.warning("⚠️ Harita yüklenemedi.")