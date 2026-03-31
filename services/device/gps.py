import logging

import streamlit as st
from streamlit_js_eval import streamlit_js_eval

from config.settings import GPS_TIMEOUT_MS


logger = logging.getLogger(__name__)


def _manual_geolocation_script() -> str:
    return f"""
        new Promise((res) => {{
            if (!navigator.geolocation) {{
                res({{error: 'Tarayiciniz GPS destegi sunmuyor.'}});
                return;
            }}

            navigator.geolocation.getCurrentPosition(
                p => res({{lat: p.coords.latitude, lon: p.coords.longitude}}),
                e => {{
                    let msg = 'Konum alinamadi';
                    if (e.code === 1) msg = 'Konum izni reddedildi.';
                    else if (e.code === 2) msg = 'Konum bilgisi mevcut degil.';
                    else if (e.code === 3) msg = 'Zaman asimi olustu.';
                    res({{error: msg}});
                }},
                {{timeout: {GPS_TIMEOUT_MS}, enableHighAccuracy: true}}
            );
        }})
    """


def _granted_only_geolocation_script() -> str:
    return f"""
        new Promise(async (res) => {{
            if (!navigator.geolocation) {{
                res({{error: 'Tarayiciniz GPS destegi sunmuyor.'}});
                return;
            }}

            if (!navigator.permissions || !navigator.permissions.query) {{
                res({{status: 'unknown'}});
                return;
            }}

            try {{
                const permission = await navigator.permissions.query({{name: 'geolocation'}});
                if (permission.state !== 'granted') {{
                    res({{status: permission.state}});
                    return;
                }}
            }} catch (err) {{
                res({{status: 'unknown'}});
                return;
            }}

            navigator.geolocation.getCurrentPosition(
                p => res({{lat: p.coords.latitude, lon: p.coords.longitude}}),
                e => {{
                    let msg = 'Konum alinamadi';
                    if (e.code === 1) msg = 'Konum izni reddedildi.';
                    else if (e.code === 2) msg = 'Konum bilgisi mevcut degil.';
                    else if (e.code === 3) msg = 'Zaman asimi olustu.';
                    res({{error: msg}});
                }},
                {{timeout: {GPS_TIMEOUT_MS}, enableHighAccuracy: true}}
            );
        }})
    """


def get_device_location(
    require_existing_permission: bool = False,
    show_status: bool = True,
    widget_key: str = "get_device_location",
):
    """
    Read device location from the browser.

    When `require_existing_permission` is True, location is fetched only if the
    browser already granted geolocation access. This avoids prompting users on
    initial page load and lets us keep the Ankara fallback silently.
    """

    logger.info(
        "GPS location request started widget_key=%s require_existing_permission=%s",
        widget_key,
        require_existing_permission,
    )

    if show_status:
        st.toast("Konum erisim izni bekleniyor...", icon="📍")

    script = (
        _granted_only_geolocation_script()
        if require_existing_permission
        else _manual_geolocation_script()
    )
    result = streamlit_js_eval(
        js_expressions=script,
        want_output=True,
        key=widget_key,
    )

    if result is None:
        logger.info("GPS location request pending widget_key=%s", widget_key)
        return result

    if isinstance(result, dict):
        if "error" in result:
            logger.warning(
                "GPS location request failed widget_key=%s error=%s",
                widget_key,
                result["error"],
            )
        elif "lat" in result and "lon" in result:
            logger.info(
                "GPS location request succeeded widget_key=%s lat=%s lon=%s",
                widget_key,
                result["lat"],
                result["lon"],
            )
        elif "status" in result:
            logger.info(
                "GPS location permission status widget_key=%s status=%s",
                widget_key,
                result["status"],
            )
        else:
            logger.info(
                "GPS location request returned unexpected payload widget_key=%s payload=%s",
                widget_key,
                result,
            )
    else:
        logger.info(
            "GPS location request returned non-dict payload widget_key=%s payload=%s",
            widget_key,
            result,
        )

    return result
