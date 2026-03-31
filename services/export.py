# services/export.py
import pandas as pd
from typing import List, Dict

def export_history_to_csv(history_data: List[Dict]) -> str:
    """Geçmiş verisini CSV formatına dönüştürür."""
    return pd.DataFrame(history_data).to_csv(index=False)