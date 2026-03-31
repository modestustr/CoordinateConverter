# services/batch.py
import pandas as pd

def process_batch_transform(engine, df: pd.DataFrame, x_col: str, y_col: str, src: str, tgt: str) -> pd.DataFrame:
    """Toplu veri dönüşüm iş mantığı."""
    return engine.transform_dataframe(df, x_col, y_col, src, tgt)