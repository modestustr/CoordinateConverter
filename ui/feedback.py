import re
from typing import Any, Dict, Optional

import pandas as pd


ERROR_TITLES = {
    "INVALID_FORMAT": "Koordinat biçimi anlaşılamadı",
    "OUT_OF_BOUNDS": "Koordinat seçilen sistemin kapsama alanı dışında",
    "INVALID_GEO_RANGE": "Enlem veya boylam aralığı geçersiz",
    "RESOLUTION_ERROR": "Koordinat sistemi çözümlenemedi",
    "NAN_COORDINATE": "Eksik koordinat değeri bulundu",
    "DYNAMIC_SOURCE_FORBIDDEN": "Dinamik UTM kaynak olarak kullanılamaz",
}

ERROR_HINTS = {
    "INVALID_FORMAT": "Girdiyi `enlem, boylam` veya `X, Y` biçiminde tekrar deneyin.",
    "OUT_OF_BOUNDS": "Kaynak koordinat sistemini ve girdi değerlerini yeniden kontrol edin.",
    "INVALID_GEO_RANGE": "Boylam `-180..180`, enlem `-90..90` aralığında olmalıdır.",
    "RESOLUTION_ERROR": "Seçilen CRS adını ve sistem eşleşmesini doğrulayın.",
    "NAN_COORDINATE": "Boş, eksik veya sayısal olmayan değerleri temizleyin.",
    "DYNAMIC_SOURCE_FORBIDDEN": "Dinamik UTM yalnızca hedef sistem olarak kullanılmalıdır.",
}


def parse_error_message(raw_error: Any) -> tuple[Optional[str], str]:
    text = str(raw_error).strip()
    match = re.match(r"^\[(?P<code>[A-Z_]+)\]\s*(?P<detail>.*)$", text)
    if match:
        return match.group("code"), match.group("detail").strip()
    return None, text


def build_error_feedback(raw_error: Any) -> Dict[str, Optional[str]]:
    code, detail = parse_error_message(raw_error)
    return {
        "code": code,
        "title": ERROR_TITLES.get(code, "İşlem tamamlanamadı"),
        "detail": detail or "Beklenmeyen bir hata oluştu.",
        "hint": ERROR_HINTS.get(code),
    }


def summarize_batch_errors(df: pd.DataFrame) -> pd.DataFrame:
    if "Durum" not in df.columns or "Hata_Kodu" not in df.columns:
        return pd.DataFrame(columns=["Hata Tipi", "Adet", "Örnek Mesaj"])

    error_df = df[df["Durum"] == "ERROR"].copy()
    if error_df.empty:
        return pd.DataFrame(columns=["Hata Tipi", "Adet", "Örnek Mesaj"])

    error_df["Hata Tipi"] = error_df["Hata_Kodu"].map(
        lambda code: ERROR_TITLES.get(code, code or "Bilinmeyen hata")
    )
    summary = (
        error_df.groupby(["Hata_Kodu", "Hata Tipi"], dropna=False)
        .agg(
            Adet=("Hata_Kodu", "size"),
            Ornek_Mesaj=("Hata_Mesaji", "first"),
        )
        .reset_index()
        .rename(columns={"Ornek_Mesaj": "Örnek Mesaj"})
        .sort_values("Adet", ascending=False)
    )
    return summary[["Hata Tipi", "Adet", "Örnek Mesaj"]]
