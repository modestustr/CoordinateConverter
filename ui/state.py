import streamlit as st


def init_session_state():
    """Session state başlatma mantığını merkezileştirir."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = "tr"
    if "src_sys" not in st.session_state:
        st.session_state["src_sys"] = "*GPS (WGS84) (deg)"
    if "tgt_sys" not in st.session_state:
        st.session_state["tgt_sys"] = "WGS84 / UTM (Dinamik)"
    if "coords" not in st.session_state:
        st.session_state["coords"] = {
            "lon": 32.8597,
            "lat": 39.9334,
            "text": "39.933333, 32.859722",
        }
    if "coords_text" not in st.session_state:
        st.session_state["coords_text"] = st.session_state["coords"]["text"]
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None
    if "auto_detect" not in st.session_state:
        st.session_state["auto_detect"] = True
    if "gps_active" not in st.session_state:
        st.session_state["gps_active"] = False
    if "gps_auto_attempted" not in st.session_state:
        st.session_state["gps_auto_attempted"] = False
    if "gps_auto_pending" not in st.session_state:
        st.session_state["gps_auto_pending"] = False


def set_preset(src: str, tgt: str):
    """Sistem seçimlerini günceller."""
    st.session_state["src_sys"] = src
    st.session_state["tgt_sys"] = tgt


def swap_systems():
    """Kaynak ve hedef sistemleri takas eder."""
    st.session_state["src_sys"], st.session_state["tgt_sys"] = (
        st.session_state["tgt_sys"], st.session_state["src_sys"]
    )
