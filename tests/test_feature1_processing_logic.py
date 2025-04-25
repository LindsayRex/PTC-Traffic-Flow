import pytest
import pandas as pd
import numpy as np

from app.features.feature_1_profile import process_hourly_profile

# Fixtures for test data
def make_hourly_df(columns):
    """
    Create a DataFrame with specified hour_NN columns and random values.
    """
    data = {col: np.arange(len(columns)) for col in columns}
    return pd.DataFrame(data)

@pytest.mark.parametrize(
    "period_name, df_cols, expected_hours",
    [
        ("AllHours", [f"hour_{i:02d}" for i in range(24)], list(range(24))),
        ("Partial", ["hour_00", "hour_05", "hour_23"], [0, 5, 23]),
    ]
)
def test_process_hourly_profile_various(period_name, df_cols, expected_hours):
    """
    process_hourly_profile should calculate average for each present hour_NN column and include only those.
    """
    # Create DataFrame with values equal to the hour index
    df = make_hourly_df(df_cols)

    result = process_hourly_profile(df, period_name)
    # Check periods column
    assert set(result['Period']) == {period_name}
    # Check hours and values
    got_hours = list(result['Hour'])
    assert got_hours == expected_hours
    # Each Average Volume should equal the hour index (since single row)
    assert list(result['Average Volume']) == expected_hours


def test_process_hourly_profile_empty():
    """
    If input DataFrame is empty or has no hour_NN columns, result should be empty DataFrame.
    """
    empty_df = pd.DataFrame()
    result = process_hourly_profile(empty_df, "EmptyPeriod")
    pd.testing.assert_frame_equal(result, pd.DataFrame(columns=["Hour", "Average Volume", "Period"]))
