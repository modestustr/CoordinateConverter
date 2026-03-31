import json
import logging
from typing import Any

from streamlit_js_eval import streamlit_js_eval


logger = logging.getLogger(__name__)


def _clipboard_write_script(text: str) -> str:
    return f"""
        new Promise(async (res) => {{
            if (!navigator.clipboard || !navigator.clipboard.writeText) {{
                res({{status: "not_supported"}});
                return;
            }}

            try {{
                await navigator.clipboard.writeText({json.dumps(text)});
                res({{status: "success"}});
            }} catch (err) {{
                res({{status: "error", message: String(err)}});
            }}
        }})
    """


def copy_text_to_clipboard(
    text: str,
    widget_key: str = "copy_to_clipboard",
) -> Any:
    logger.info("Clipboard copy request started widget_key=%s", widget_key)
    result = streamlit_js_eval(
        js_expressions=_clipboard_write_script(text),
        want_output=True,
        key=widget_key,
    )

    if result is None:
        logger.info("Clipboard copy request pending widget_key=%s", widget_key)
        return result

    if isinstance(result, dict):
        logger.info(
            "Clipboard copy request finished widget_key=%s status=%s",
            widget_key,
            result.get("status"),
        )
    else:
        logger.info(
            "Clipboard copy request returned non-dict payload widget_key=%s payload=%s",
            widget_key,
            result,
        )

    return result
