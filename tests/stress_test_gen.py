import time

import numpy as np
import pandas as pd


def build_stress_test_dataframe(row_count=100000) -> pd.DataFrame:
    # Gecerli Turkiye koordinatlari (WGS84)
    # Enlem: 36-42, Boylam: 26-45
    lats = np.round(np.random.uniform(36.0, 42.0, size=row_count), 4)
    lons = np.round(np.random.uniform(26.0, 45.0, size=row_count), 4)
    point_names = [f"Nokta_{i:06d}" for i in range(row_count)]

    # Ornek dosya ile ayni sema: Nokta_Adi, Boylam, Enlem
    df = pd.DataFrame(
        {
            "Nokta_Adi": point_names,
            "Boylam": lons,
            "Enlem": lats,
        }
    )

    # Metin hata enjeksiyonu icin kolonlari object'e cevir.
    df["Boylam"] = df["Boylam"].astype(object)
    df["Enlem"] = df["Enlem"].astype(object)

    # Kasti hata enjeksiyonu (yaklasik %5 secili satir)
    error_count = int(row_count * 0.05)
    indices = np.random.choice(df.index, size=error_count, replace=False)

    for i, idx in enumerate(indices):
        if i % 4 == 0:
            df.at[idx, "Enlem"] = np.nan
        elif i % 4 == 1:
            df.at[idx, "Boylam"] = 190.0
        elif i % 4 == 2:
            df.at[idx, "Enlem"] = "HATALI_METIN"
        else:
            df.at[idx, "Nokta_Adi"] = "Sinir_Durum"

    return df


def generate_stress_test_data(row_count=100000, file_name="stress_test_100k.csv"):
    print(f"{row_count} satirlik test verisi uretiliyor...")
    start_time = time.time()

    df = build_stress_test_dataframe(row_count)
    df.to_csv(file_name, index=False)

    end_time = time.time()
    print(f"Dosya hazir: {file_name}")
    print(f"Uretim suresi: {end_time - start_time:.2f} saniye")
    print(f"Veri cercevesi bellek boyutu: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")


if __name__ == "__main__":
    generate_stress_test_data()
