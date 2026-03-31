# ui/utils/df_i18n.py

from typing import Dict
import pandas as pd

from ui.i18n import translate_text


COLUMN_KEY_MAP: Dict[str, str] = {
    "Durum": "batch.column.status",
    "Hata_Kodu": "batch.column.error_code",
    "Hata_Mesaji": "batch.column.error_message",
    "Kaynak": "sidebar.history.df_source",
    "Hedef": "sidebar.history.df_target",
    "Girdi": "sidebar.history.df_input",
    "Sonuç": "sidebar.history.df_output",
    "Tutarlılık": "sidebar.history.df_consistency",
}

def translate_dataframe_columns(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        # Sütun ismindeki olası boşlukları temizleyerek sözlükte ara
        clean_col = str(col).strip() 
        key = COLUMN_KEY_MAP.get(clean_col)
        
        if key:
            translated = translate_text(key, lang)
            rename_map[col] = translated
        else:
            rename_map[col] = col
    return df.rename(columns=rename_map)