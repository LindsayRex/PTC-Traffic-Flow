import pytest
import pandas as pd
import datetime
from contextlib import nullcontext

import app.features.feature_1_profile as f1

class DummySession:
    """A dummy DB session with no-op close()."""
    def close(self) -> None:
        pass

@pytest.fixture(autouse=True)
def stub_streamlit(monkeypatch):
    """
    Stub Streamlit UI calls so render_station_profile() runs headlessly
    and capture st.error/st.warning messages.
    """
    messages = {"error": [], "warning": []}

    # layout contexts
    monkeypatch.setattr(f1.st, "columns", lambda *a, **k: [nullcontext(), nullcontext()])
    monkeypatch.setattr(f1.st, "spinner", lambda *a, **k: nullcontext())

    # basic UI stubs
    for attr in ("title", "subheader", "selectbox", "table"):  
        monkeypatch.setattr(f1.st, attr, lambda *a, **k: None)

    # capture error/warning
    monkeypatch.setattr(f1.st, "error", lambda msg, *a, **k: messages["error"].append(msg))
    monkeypatch.setattr(f1.st, "warning", lambda msg, *a, **k: messages["warning"].append(msg))

    f1._test_messages = messages
    yield
    del f1._test_messages

@pytest.mark.parametrize(
    "session_ret, meta_ret, expected_error",
    [
        (None, None, "Could not get database session."),
        (DummySession(), None, "Error loading station data. Database connection might be unavailable."),
    ]
)
def test_metadata_fetch_errors(monkeypatch, session_ret, meta_ret, expected_error):
    """
    If get_db_session() is None or metadata fetch returns None,
    render_station_profile() should call st.error().
    """
    monkeypatch.setattr(f1, "get_db_session", lambda: session_ret)
    monkeypatch.setattr(f1, "get_all_station_metadata", lambda sess: meta_ret)

    f1.render_station_profile()
    errors = f1._test_messages["error"]
    assert errors, "Expected at least one error"
    assert any(expected_error in e for e in errors)


def test_metadata_empty_warns(monkeypatch):
    """
    If get_all_station_metadata() returns empty DataFrame,
    render_station_profile() should call st.warning().
    """
    monkeypatch.setattr(f1, "get_db_session", lambda: DummySession())
    monkeypatch.setattr(f1, "get_all_station_metadata", lambda sess: pd.DataFrame())

    f1.render_station_profile()
    warnings = f1._test_messages["warning"]
    assert warnings, "Expected warning"
    assert any("No station data found matching criteria." in w for w in warnings)


# Helper to create a minimal station metadata DataFrame

def _make_station_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"station_key": "K1", "station_id": "S1", "road_name": "R1"}
    ])


# --- New test: get_station_details raises exception ---

def test_station_details_exception(monkeypatch):
    """
    If get_station_details raises an exception, render_station_profile() should call st.error().
    """
    # Setup
    monkeypatch.setattr(f1, "get_db_session", lambda: DummySession())
    monkeypatch.setattr(f1, "get_all_station_metadata", lambda s: _make_station_df())
    def bad_details(s, key):
        raise RuntimeError("DB failure")
    monkeypatch.setattr(f1, "get_station_details", bad_details)
    # stub selectbox to return first option for both station and direction drops
    monkeypatch.setattr(f1.st, "selectbox", lambda label, options, *a, **k: options[0])

    f1.render_station_profile()
    errs = f1._test_messages["error"]
    assert any("Error loading station details" in e for e in errs)


# --- New test: get_latest_data_date raises exception ---

def test_latest_data_date_exception(monkeypatch):
    """
    If get_latest_data_date raises, render_station_profile should call st.error().
    """
    monkeypatch.setattr(f1, "get_db_session", lambda: DummySession())
    monkeypatch.setattr(f1, "get_all_station_metadata", lambda s: _make_station_df())
    monkeypatch.setattr(f1, "get_station_details", lambda s, key: {"dummy": 1})
    def bad_latest(s, key, date):
        raise ValueError("no date")
    monkeypatch.setattr(f1, "get_latest_data_date", bad_latest)
    # stub selectbox to return first element in options list
    monkeypatch.setattr(f1.st, "selectbox", lambda label, options, *a, **k: options[0])

    f1.render_station_profile()
    errs = f1._test_messages["error"]
    assert any("Error determining data date range." in e for e in errs)


# --- New test: full successful flow with no errors/warnings ---

def test_full_flow_success(monkeypatch):
    """
    When all DB calls succeed and data is present, there should be no st.error or st.warning.
    """
    # minimal station df
    df = _make_station_df()
    # one hourly record with required fields
    today = datetime.date(2024, 6, 30)
    hourly = pd.DataFrame({
        'count_date': [today],
        'is_public_holiday': [False],
        'day_of_week': [2],
        **{f'hour_{h:02d}': [h * 10] for h in range(24)},
        'daily_total': [sum(h * 10 for h in range(24))]
    })

    # Monkeypatch DB calls
    monkeypatch.setattr(f1, "get_db_session", lambda: DummySession())
    monkeypatch.setattr(f1, "get_all_station_metadata", lambda s: df)
    # return truthy latitude/longitude to render map and avoid location warning
    monkeypatch.setattr(f1, "get_station_details", lambda s, key: {'wgs84_latitude': 1.0, 'wgs84_longitude': 1.0})
    monkeypatch.setattr(f1, "get_latest_data_date", lambda s, key, direction: today)
    monkeypatch.setattr(f1, "get_hourly_data_for_stations", lambda s, keys, start, end, **kw: hourly)
    # stub selectbox to handle station and direction
    monkeypatch.setattr(f1.st, "selectbox", lambda label, options, *a, **k: options[0])
    # stub plot embed and components
    monkeypatch.setattr(f1, "embed_bokeh_plot", lambda fig, height=None: '<html/>' )
    monkeypatch.setattr(f1.components, "html", lambda html, height=None: None)

    f1.render_station_profile()
    assert not f1._test_messages['error']
    assert not f1._test_messages['warning']
