import time

import pandas as pd
import streamlit as st

from config.settings import MAX_UPLOAD_SIZE_MB
from ui.feedback import build_error_feedback, summarize_batch_errors
from ui.i18n import get_language, t, translate_text
from ui.utils.df_i18n import translate_dataframe_columns


def _format_seconds_compact(seconds: float, lang: str = "tr") -> str:
    rounded = max(1, int(round(seconds)))
    minutes, secs = divmod(rounded, 60)
    if minutes:
        return f"{minutes} {translate_text('time.minute', lang)} {secs} {translate_text('time.second', lang)}"
    return f"{secs} {translate_text('time.second', lang)}"


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
    lang: str,
) -> None:
    success_rate = 0.0 if total_rows == 0 else (success_count / total_rows) * 100
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("batch.metrics.total"), total_rows)
    c2.metric(t("batch.metrics.success"), success_count)
    c3.metric(t("batch.metrics.error"), error_count)
    c4.metric(t("batch.metrics.success_rate"), f"%{success_rate:.1f}")
    c5.metric(t("batch.metrics.elapsed"), _format_seconds_compact(elapsed_seconds, lang))


def render_batch_conversion(controller):
    lang = get_language()
    st.subheader(t("batch.title"))
    up = st.file_uploader(t("batch.upload"), type=["csv", "xlsx"])

    if not up:
        return

    max_size_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if getattr(up, "size", 0) > max_size_bytes:
        st.error(t("batch.file_too_large", limit=MAX_UPLOAD_SIZE_MB))
        st.info(t("batch.file_too_large_hint"))
        return

    try:
        df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up)
        if len(df.columns) < 2:
            st.error(t("batch.need_two_columns"))
            st.info(t("batch.need_two_columns_hint"))
            return

        st.info(t("batch.file_loaded", rows=len(df)))
        st.dataframe(translate_dataframe_columns(df.head(5), lang))
        c1, c2 = st.columns(2)
        xc = c1.selectbox(t("batch.x_column"), df.columns)
        yc = c2.selectbox(t("batch.y_column"), df.columns)

        tgt_sys = st.session_state["tgt_sys"]
        estimate_low, estimate_high = _estimate_batch_duration_range(len(df), tgt_sys)
        st.caption(
            t(
                "batch.estimate",
                low=_format_seconds_compact(estimate_low, lang),
                high=_format_seconds_compact(estimate_high, lang),
            )
        )

        if st.button(t("batch.start"), type="primary", width="stretch"):
            if xc == yc:
                st.error(t("batch.same_columns"))
                st.info(t("batch.same_columns_hint"))
                return

            src_sys = st.session_state["src_sys"]
            tgt_sys = st.session_state["tgt_sys"]
            started_at = time.perf_counter()

            progress = st.progress(5, text=t("batch.progress.preparing"))
            status = st.status(t("batch.status.started"), expanded=True)
            status.write(
                t(
                    "batch.status.rows_estimate",
                    rows=len(df),
                    low=_format_seconds_compact(estimate_low, lang),
                    high=_format_seconds_compact(estimate_high, lang),
                )
            )

            try:
                progress.progress(15, text=t("batch.progress.validate"))
                status.write(t("batch.status.source", source=src_sys))
                status.write(t("batch.status.target", target=tgt_sys))

                progress.progress(35, text=t("batch.progress.transform"))
                res_df = controller.transform_batch(df, xc, yc, src_sys, tgt_sys)

                progress.progress(70, text=t("batch.progress.summary"))
                error_count = (
                    int((res_df["Durum"] == "ERROR").sum())
                    if "Durum" in res_df.columns
                    else 0
                )
                success_count = len(res_df) - error_count
                elapsed_seconds = time.perf_counter() - started_at

                progress.progress(85, text=t("batch.progress.metrics"))
                _render_batch_metrics(
                    len(res_df), success_count, error_count, elapsed_seconds, lang
                )

                if error_count:
                    st.warning(
                        t(
                            "batch.warning.rows_failed",
                            error_count=error_count,
                            success_count=success_count,
                        )
                    )
                    st.caption(t("batch.warning.caption"))
                    err_df = summarize_batch_errors(res_df, lang)
                    st.dataframe(
                        translate_dataframe_columns(err_df, lang),
                        hide_index=True,
                        width="stretch",
                    )
                    status.write(t("batch.status.error_rows", count=error_count))
                else:
                    st.success(t("batch.success.all_rows"))
                    status.write(t("batch.status.all_ok"))

                if len(res_df) >= 50000:
                    st.info(t("batch.info.browser_render"))

                progress.progress(95, text=t("batch.progress.render"))
                st.dataframe(translate_dataframe_columns(res_df, lang))
                csv = res_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    t("batch.download"),
                    csv,
                    "donusturulmus_koordinatlar.csv",
                    "text/csv",
                )

                total_elapsed = time.perf_counter() - started_at
                progress.progress(
                    100,
                    text=t(
                        "batch.progress.completed",
                        elapsed=_format_seconds_compact(total_elapsed, lang),
                    ),
                )
                status.update(
                    label=t(
                        "batch.status.completed",
                        elapsed=_format_seconds_compact(total_elapsed, lang),
                    ),
                    state="complete",
                    expanded=False,
                )
            except Exception as e:
                progress.progress(100, text=t("batch.progress.failed"))
                feedback = build_error_feedback(e, lang)
                status.update(
                    label=t("batch.status.failed", title=feedback["title"]),
                    state="error",
                    expanded=True,
                )
                st.error(f"⚠️ {feedback['title']}")
                st.caption(feedback["detail"])
                st.info(feedback["hint"] or t("batch.error.retry_hint"))
    except Exception as e:
        feedback = build_error_feedback(e, lang)
        st.error(f"⚠️ {feedback['title']}")
        st.caption(feedback["detail"])
        st.info(feedback["hint"] or t("batch.error.retry_hint"))
