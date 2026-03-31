import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import requests

import config.settings as app_settings
from core.coord import CoordConverter
from core.crs import CRSResolutionError, ErrorCode
import services.geocode as geocode_service
from ui.feedback import build_error_feedback, summarize_batch_errors
from ui.i18n import LANGUAGE_LABELS, normalize_language, translate_text
from ui.controller import AppController
from ui.sidebar import _build_system_status
from ui.views.batch import _estimate_batch_duration_range, _format_seconds_compact
from ui.views.single import _build_copy_payload


@pytest.fixture
def app():
    engine = CoordConverter()
    return AppController(engine)


@pytest.mark.parametrize(
    "input_text, expected_lon, expected_lat",
    [
        ("32.85, 39.93", 32.85, 39.93),
        ("39.93, 32.85", 32.85, 39.93),
        ("39° 56' 00\" N, 32° 51' 00\" E", 32.85, 39.933333),
        ("39 56 00 N 32 51 00 E", 32.85, 39.933333),
        ("37.77, -122.41", -122.41, 37.77),
        ("-122.41, 37.77", -122.41, 37.77),
        ("0, 0", 0.0, 0.0),
        ("41.008, 28.978", 28.978, 41.008),
        ("28.978, 41.008", 28.978, 41.008),
        ("39.9,32.8", 32.8, 39.9),
        ("500000 4400000", 500000.0, 4400000.0),
    ],
)
def test_coordinate_handling(app, input_text, expected_lon, expected_lat):
    ix, iy = app.parse_input_coords(input_text)

    assert ix == pytest.approx(expected_lon, abs=1e-5)
    assert iy == pytest.approx(expected_lat, abs=1e-5)


def test_resolver_confidence_scoring(app):
    res_tr = app.get_input_details("39.9, 32.8")
    assert res_tr["suggestion"]["confidence"] >= 0.8
    assert "Türkiye" in res_tr["suggestion"]["reason"]

    res_ocean = app.get_input_details("0.0, 0.0")
    assert res_ocean["suggestion"]["confidence"] <= 0.5


def test_dynamic_utm_ankara(app):
    res = app.convert("39.93, 32.85", "*GPS (WGS84) (deg)", "WGS84 / UTM (Dinamik)")
    assert "36N" in res["t_meta"]["description"]
    assert res["src_info"]["is_geo"] is True


@pytest.mark.parametrize(
    "lat, lon",
    [
        (41.0, 29.0),
        (48.8, 2.3),
        (40.7, -74.0),
    ],
)
def test_roundtrip_precision(app, lat, lon):
    res = app.convert(f"{lat}, {lon}", "*GPS (WGS84) (deg)", "WGS 84 / Pseudo-Mercator")
    assert res["verification"]["ok"] is True


def test_invalid_input_handling(app):
    with pytest.raises(ValueError, match=ErrorCode.INVALID_FORMAT.value):
        app.convert("merhaba dünya", "*GPS (WGS84) (deg)", "WGS84 / UTM (Dinamik)")


def test_out_of_bounds(app):
    with pytest.raises(ValueError, match=ErrorCode.OUT_OF_BOUNDS.value):
        app.convert("70.0, -40.0", "ITRF96 / TM30 (Türkiye)", "*GPS (WGS84) (deg)")


def test_nan_handling_point(app):
    with pytest.raises(ValueError, match=ErrorCode.NAN_COORDINATE.value):
        app.engine.transform_point(np.nan, 32.85, "EPSG:4326", "EPSG:3857")


def test_invalid_crs_resolution(app):
    with pytest.raises(CRSResolutionError):
        app.engine.transform_point(32.85, 39.93, "GEÇERSİZ_SİSTEM", "EPSG:4326")


def test_extreme_coordinates_sanity(app):
    check = app.engine.sanity_check(200.0, 95.0, "EPSG:4326")
    assert check["valid"] is False
    assert check["error_code"] == ErrorCode.INVALID_GEO_RANGE


def test_dataframe_with_nans(app):
    df = pd.DataFrame({"x": [32.85, np.nan, 32.86], "y": [39.93, 39.94, np.nan]})

    res_df = app.engine.transform_dataframe(df, "x", "y", "EPSG:4326", "EPSG:3857")

    assert not np.isnan(res_df.iloc[0]["Hedef_x"])
    assert np.isnan(res_df.iloc[1]["Hedef_x"])
    assert np.isnan(res_df.iloc[2]["Hedef_x"])


def test_dataframe_invalid_rows_are_flagged(app):
    df = pd.DataFrame({"x": [200.0, "bad"], "y": [95.0, 39.0]})

    res_df = app.engine.transform_dataframe(df, "x", "y", "EPSG:4326", "EPSG:3857")

    assert res_df.iloc[0]["Durum"] == "ERROR"
    assert res_df.iloc[0]["Hata_Kodu"] == ErrorCode.INVALID_GEO_RANGE.value
    assert np.isnan(res_df.iloc[0]["Hedef_x"])

    assert res_df.iloc[1]["Durum"] == "ERROR"
    assert res_df.iloc[1]["Hata_Kodu"] == ErrorCode.INVALID_FORMAT.value
    assert np.isnan(res_df.iloc[1]["Hedef_x"])


def test_dataframe_dynamic_utm_batch_works(app):
    df = pd.DataFrame(
        {
            "longitude": [32.85, 29.0, 41.0],
            "latitude": [39.93, 41.0, 37.0],
        }
    )

    res_df = app.engine.transform_dataframe(
        df,
        "longitude",
        "latitude",
        "EPSG:4326",
        "WGS84 / UTM (Dinamik)",
    )

    assert (res_df["Durum"] == "OK").all()
    assert res_df["Hedef_longitude"].notna().all()
    assert res_df["Hedef_latitude"].notna().all()


def test_build_error_feedback_maps_codes():
    feedback = build_error_feedback("[OUT_OF_BOUNDS] Kapsama alanı dışında")

    assert feedback["code"] == ErrorCode.OUT_OF_BOUNDS.value
    assert feedback["title"] == "Koordinat seçilen sistemin kapsama alanı dışında"
    assert "Kaynak koordinat sistemini" in feedback["hint"]


def test_summarize_batch_errors_groups_codes():
    df = pd.DataFrame(
        {
            "Durum": ["ERROR", "ERROR", "OK"],
            "Hata_Kodu": ["INVALID_FORMAT", "INVALID_FORMAT", ""],
            "Hata_Mesaji": ["Sayısal değil", "Sayısal değil", ""],
        }
    )

    summary = summarize_batch_errors(df)

    assert len(summary) == 1
    assert summary.iloc[0]["Hata Tipi"] == "Koordinat biçimi anlaşılamadı"
    assert summary.iloc[0]["Adet"] == 2


def test_batch_duration_estimate_increases_with_row_count():
    small_low, small_high = _estimate_batch_duration_range(1000, "EPSG:3857")
    big_low, big_high = _estimate_batch_duration_range(100000, "EPSG:3857")

    assert big_low > small_low
    assert big_high > small_high
    assert big_high > big_low


def test_format_seconds_compact_handles_minutes():
    assert _format_seconds_compact(8.4) == "8 sn"
    assert _format_seconds_compact(65) == "1 dk 5 sn"


def test_build_copy_payload_uses_lat_lon_for_geographic_results():
    payload = _build_copy_payload(
        {
            "output_x": 32.85,
            "output_y": 39.93,
            "t_info": {"is_geo": True},
        }
    )

    assert payload == "39.93000000, 32.85000000"


def test_build_copy_payload_uses_x_y_for_projected_results():
    payload = _build_copy_payload(
        {
            "output_x": 441234.56789,
            "output_y": 4478901.23456,
            "t_info": {"is_geo": False},
        }
    )

    assert payload == "441234.568, 4478901.235"


def test_language_labels_include_requested_languages():
    for code in ("tr", "en", "de", "fr", "ru", "el", "it", "es"):
        assert code in LANGUAGE_LABELS


def test_language_alias_and_locale_contract():
    assert normalize_language("gr") == "el"
    assert translate_text("single.copy.button", "de") == "Ergebnis kopieren"
    assert translate_text("single.copy.button", "fr") == "Copier le résultat"
    assert translate_text("single.copy.button", "ru") == "Скопировать результат"
    assert translate_text("single.copy.button", "el") == "Αντιγραφή αποτελέσματος"
    assert translate_text("single.copy.button", "it") == "Copia risultato"
    assert translate_text("single.copy.button", "es") == "Copiar resultado"


def test_stress_test_generator_matches_example_schema():
    module_path = Path(__file__).with_name("stress_test_gen.py")
    spec = importlib.util.spec_from_file_location("stress_test_gen", module_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    df = mod.build_stress_test_dataframe(25)

    assert list(df.columns) == ["Nokta_Adi", "Boylam", "Enlem"]
    assert len(df) == 25


def test_geocode_retries_after_timeout(monkeypatch):
    attempts = {"count": 0}

    class _Response:
        def raise_for_status(self):
            return None

        def json(self):
            return [{"lon": "32.8500", "lat": "39.9300"}]

    def fake_get(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise requests.Timeout("simulated timeout")
        return _Response()

    monkeypatch.setattr(geocode_service.requests, "get", fake_get)
    monkeypatch.setattr(geocode_service.time, "sleep", lambda *_args: None)

    lon, lat = geocode_service.geocode_address("Ankara")

    assert attempts["count"] == 2
    assert lon == pytest.approx(32.85)
    assert lat == pytest.approx(39.93)


def test_geocode_returns_none_after_retry_exhaustion(monkeypatch):
    attempts = {"count": 0}

    def fake_get(*args, **kwargs):
        attempts["count"] += 1
        raise requests.Timeout("always timeout")

    monkeypatch.setattr(geocode_service.requests, "get", fake_get)
    monkeypatch.setattr(geocode_service.time, "sleep", lambda *_args: None)

    lon, lat = geocode_service.geocode_address("Istanbul")

    assert attempts["count"] == geocode_service.GEOCODE_MAX_RETRIES
    assert lon is None
    assert lat is None


def test_geocode_skips_empty_address():
    lon, lat = geocode_service.geocode_address("   ")

    assert lon is None
    assert lat is None


def test_dataframe_output_contract_preserves_input_and_status_columns(app):
    df = pd.DataFrame(
        {
            "Nokta_Adi": ["Ankara", "Bos"],
            "Boylam": [32.85, None],
            "Enlem": [39.93, 39.92],
        }
    )

    res_df = app.transform_batch(df, "Boylam", "Enlem", "EPSG:4326", "EPSG:3857")

    assert list(res_df.columns) == [
        "Nokta_Adi",
        "Boylam",
        "Enlem",
        "Hedef_Boylam",
        "Hedef_Enlem",
        "Durum",
        "Hata_Kodu",
        "Hata_Mesaji",
    ]
    assert res_df.iloc[0]["Durum"] == "OK"
    assert res_df.iloc[0]["Hata_Kodu"] == ""
    assert res_df.iloc[1]["Durum"] == "ERROR"
    assert res_df.iloc[1]["Hata_Kodu"] == ErrorCode.NAN_COORDINATE.value


def test_build_error_feedback_for_unknown_error_uses_generic_contract():
    feedback = build_error_feedback(RuntimeError("beklenmeyen hata"))

    assert feedback["code"] is None
    assert feedback["title"] == "İşlem tamamlanamadı"
    assert feedback["detail"] == "beklenmeyen hata"
    assert feedback["hint"] is None


def test_summarize_batch_errors_empty_contract():
    summary = summarize_batch_errors(pd.DataFrame({"x": [1], "y": [2]}))

    assert list(summary.columns) == ["Hata Tipi", "Adet", "Örnek Mesaj"]
    assert summary.empty


def test_dynamic_utm_source_returns_machine_readable_error(app):
    with pytest.raises(ValueError, match=ErrorCode.DYNAMIC_SOURCE_FORBIDDEN.value):
        app.convert(
            "500000 4400000",
            "WGS84 / UTM (Dinamik)",
            "*GPS (WGS84) (deg)",
        )


def test_export_history_csv_contract(app):
    csv_text = app.format_history_for_export(
        [
            {
                "Kaynak": "EPSG:4326",
                "Hedef": "EPSG:3857",
                "Girdi": "39.93, 32.85",
                "Sonuc": "3650000, 4850000",
            }
        ]
    )

    lines = csv_text.strip().splitlines()
    assert lines[0] == "Kaynak,Hedef,Girdi,Sonuc"
    assert lines[1] == 'EPSG:4326,EPSG:3857,"39.93, 32.85","3650000, 4850000"'


def test_system_list_contract_is_sorted_and_unique(app):
    systems = app.get_system_list()

    assert systems == sorted(systems)
    assert len(systems) == len(set(systems))
    assert "*GPS (WGS84) (deg)" in systems


def test_sidebar_status_contract():
    healthy = _build_system_status(["EPSG:4326", "EPSG:3857"])
    unhealthy = _build_system_status([])

    assert healthy["healthy"] is True
    assert healthy["system_count"] == 2
    assert unhealthy["healthy"] is False
    assert unhealthy["system_count"] == 0


def test_settings_env_normalization():
    assert app_settings._normalize_env(" PROD ") == "prod"
    assert app_settings._normalize_env("invalid") == "dev"
