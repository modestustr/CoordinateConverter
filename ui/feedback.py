import re
from typing import Any, Dict, Optional

import pandas as pd

from ui.i18n import translate_text


ERROR_CODES = {
    "INVALID_FORMAT",
    "OUT_OF_BOUNDS",
    "INVALID_GEO_RANGE",
    "RESOLUTION_ERROR",
    "NAN_COORDINATE",
    "DYNAMIC_SOURCE_FORBIDDEN",
}


def parse_error_message(raw_error: Any) -> tuple[Optional[str], str]:
    text = str(raw_error).strip()
    match = re.match(r"^\[(?P<code>[A-Z_]+)\]\s*(?P<detail>.*)$", text)
    if match:
        return match.group("code"), match.group("detail").strip()
    return None, text


def build_error_feedback(raw_error: Any, lang: str = "tr") -> Dict[str, Optional[str]]:
    code, detail = parse_error_message(raw_error)
    return {
        "code": code,
        "title": (
            translate_text(f"error.title.{code}", lang)
            if code in ERROR_CODES
            else translate_text("feedback.generic_title", lang)
        ),
        "detail": (
            translate_text(f"error.detail.{code}", lang)
            if code in ERROR_CODES
            else detail or translate_text("feedback.generic_detail", lang)
        ),
        "hint": (
            translate_text(f"error.hint.{code}", lang)
            if code in ERROR_CODES
            else None
        ),
    }


def summarize_batch_errors(df: pd.DataFrame, lang: str = "tr") -> pd.DataFrame:
    columns = [
        translate_text("feedback.summary.type", lang),
        translate_text("feedback.summary.count", lang),
        translate_text("feedback.summary.sample", lang),
    ]
    if "Durum" not in df.columns or "Hata_Kodu" not in df.columns:
        return pd.DataFrame(columns=columns)

    error_df = df[df["Durum"] == "ERROR"].copy()
    if error_df.empty:
        return pd.DataFrame(columns=columns)

    error_df["Hata Tipi"] = error_df["Hata_Kodu"].map(
        lambda code: (
            translate_text(f"error.title.{code}", lang)
            if code in ERROR_CODES
            else code or translate_text("feedback.summary.unknown", lang)
        )
    )
    error_df["Ornek_Mesaj"] = error_df["Hata_Kodu"].map(
        lambda code: (
            translate_text(f"error.detail.{code}", lang)
            if code in ERROR_CODES
            else translate_text("feedback.generic_detail", lang)
        )
    )
    summary = (
        error_df.groupby(["Hata_Kodu", "Hata Tipi"], dropna=False)
        .agg(
            Adet=("Hata_Kodu", "size"),
            Ornek_Mesaj=("Ornek_Mesaj", "first"),
        )
        .reset_index()
        .rename(
            columns={
                "Hata Tipi": translate_text("feedback.summary.type", lang),
                "Adet": translate_text("feedback.summary.count", lang),
                "Ornek_Mesaj": translate_text("feedback.summary.sample", lang),
            }
        )
        .sort_values(translate_text("feedback.summary.count", lang), ascending=False)
    )
    return summary[columns]
