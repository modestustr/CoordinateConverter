import time

import pandas as pd
import streamlit as st

from config.settings import MAX_UPLOAD_SIZE_MB
from ui.feedback import build_error_feedback, summarize_batch_errors


def _format_seconds_compact(seconds: float) -> str:
    rounded = max(1, int(round(seconds)))
    minutes, secs = divmod(rounded, 60)
    if minutes:
        return f"{minutes} dk {secs} sn"
    return f"{secs} sn"


def _estimate_batch_duration_range(row_count: int, tgt_sys: str) -> tuple[float, float]:
    complexity_factor = 1.1 if "Dinamik" in tgt_sys else 1.0
    transform_seconds = 0.8 + (row_count / 100000) * 3.6 * complexity_factor
    render_seconds = 0.4 + min(row_count / 100000, 2.0) * 1.6
    lower = transform_seconds + (render_seconds * 0.6)
    upper = transform_seconds + (render_seconds * 1.5)
    return lower, max(lower + 1, upper)


def _render_batch_metrics(
    total_rows: int,
    success_count: int,
    error_count: int,
    elapsed_seconds: float,
) -> None:
    success_rate = 0.0 if total_rows == 0 else (success_count / total_rows) * 100
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Toplam Satır", total_rows)
    c2.metric("Başarılı", success_count)
    c3.metric("Hatalı", error_count)
    c4.metric("Başarı Oranı", f"%{success_rate:.1f}")
    c5.metric("İşlem Süresi", _format_seconds_compact(elapsed_seconds))


def render_batch_conversion(controller):
    st.subheader("📦 Toplu İşlem")
    up = st.file_uploader("CSV veya Excel dosyası seçin", type=["csv", "xlsx"])

    if not up:
        return

    max_size_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if getattr(up, "size", 0) > max_size_bytes:
        st.error(f"⚠️ Dosya boyutu {MAX_UPLOAD_SIZE_MB} MB sınırını aşıyor.")
        st.info("Daha küçük bir dosya yükleyin veya dosyayı parçalara bölün.")
        return

    try:
        df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
        if len(df.columns) < 2:
            st.error("⚠️ Dosyada en az iki kolon bulunmalı.")
            st.info("X ve Y için kullanılacak iki ayrı koordinat kolonu ekleyin.")
            return

        st.info(f"💾 Dosya yüklendi: {len(df)} satır işlenmeye hazır.")
        st.dataframe(df.head(5))

        c1, c2 = st.columns(2)
        xc = c1.selectbox("X (Boylam/Easting) Sütunu", df.columns)
        yc = c2.selectbox("Y (Enlem/Northing) Sütunu", df.columns)

        tgt_sys = st.session_state["tgt_sys"]
        estimate_low, estimate_high = _estimate_batch_duration_range(len(df), tgt_sys)
        st.caption(
            f"Tahmini işlem süresi: {_format_seconds_compact(estimate_low)} - "
            f"{_format_seconds_compact(estimate_high)}. "
            "Büyük sonuç tablolarında tarayıcı çizimi için birkaç saniye ek gecikme olabilir."
        )

        if st.button("🚀 Dönüştürmeyi Başlat", type="primary", width="stretch"):
            if xc == yc:
                st.error("⚠️ X ve Y için farklı kolonlar seçin.")
                st.info("Aynı kolonu iki eksen için kullanmak dönüşümü geçersiz kılar.")
                return

            src_sys = st.session_state["src_sys"]
            tgt_sys = st.session_state["tgt_sys"]
            started_at = time.perf_counter()

            progress = st.progress(5, text="İşlem hazırlanıyor...")
            status = st.status("Toplu işlem başlatıldı", expanded=True)
            status.write(
                f"{len(df)} satır işlenecek. Tahmini süre: "
                f"{_format_seconds_compact(estimate_low)} - {_format_seconds_compact(estimate_high)}."
            )

            try:
                progress.progress(15, text="Kolon seçimi ve dosya yapısı doğrulanıyor...")
                status.write(f"Kaynak: {src_sys}")
                status.write(f"Hedef: {tgt_sys}")

                progress.progress(35, text="Koordinatlar doğrulanıyor ve dönüştürülüyor...")
                res_df = controller.transform_batch(df, xc, yc, src_sys, tgt_sys)

                progress.progress(70, text="Sonuç özeti hazırlanıyor...")
                error_count = (
                    int((res_df["Durum"] == "ERROR").sum())
                    if "Durum" in res_df.columns
                    else 0
                )
                success_count = len(res_df) - error_count
                elapsed_seconds = time.perf_counter() - started_at

                progress.progress(85, text="Metrikler ve hata dağılımı hazırlanıyor...")
                _render_batch_metrics(
                    len(res_df), success_count, error_count, elapsed_seconds
                )

                if error_count:
                    st.warning(
                        f"⚠️ {error_count} satır dönüştürülemedi. "
                        f"{success_count} satır başarıyla işlendi."
                    )
                    st.caption(
                        "Hata dağılımı aşağıda özetlenmiştir. Tam ayrıntılar sonuç tablosundaki "
                        "`Hata_Kodu` ve `Hata_Mesaji` kolonlarında yer alır."
                    )
                    st.dataframe(
                        summarize_batch_errors(res_df),
                        hide_index=True,
                        width="stretch",
                    )
                    status.write(f"Hatalı satır sayısı: {error_count}")
                else:
                    st.success("✅ Tüm satırlar başarıyla dönüştürüldü!")
                    status.write("Tüm satırlar başarıyla işlendi.")

                if len(res_df) >= 50000:
                    st.info(
                        "Büyük sonuç tablosu tarayıcıda hazırlanıyor. İlk çizimde kısa bir ek gecikme görebilirsiniz."
                    )

                progress.progress(95, text="Sonuç tablosu ve indirme çıktısı hazırlanıyor...")
                st.dataframe(res_df)

                csv = res_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Sonuçları İndir (CSV)",
                    csv,
                    "donusturulmus_koordinatlar.csv",
                    "text/csv",
                )

                total_elapsed = time.perf_counter() - started_at
                progress.progress(
                    100,
                    text=f"Tamamlandı • {_format_seconds_compact(total_elapsed)}",
                )
                status.update(
                    label=f"Toplu işlem tamamlandı • {_format_seconds_compact(total_elapsed)}",
                    state="complete",
                    expanded=False,
                )
            except Exception as e:
                progress.progress(100, text="İşlem hata ile sonlandı")
                feedback = build_error_feedback(e)
                status.update(
                    label=f"Toplu işlem tamamlanamadı • {feedback['title']}",
                    state="error",
                    expanded=True,
                )
                st.error(f"⚠️ {feedback['title']}")
                st.caption(feedback["detail"])
                st.info(
                    feedback["hint"]
                    or "Dosya biçimini, ayraç yapısını ve seçilen kolonları kontrol ederek tekrar deneyin."
                )
    except Exception as e:
        feedback = build_error_feedback(e)
        st.error(f"⚠️ {feedback['title']}")
        st.caption(feedback["detail"])
        st.info(
            feedback["hint"]
            or "Dosya biçimini, ayraç yapısını ve seçilen kolonları kontrol ederek tekrar deneyin."
        )
