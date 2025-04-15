import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Station, HourlyCount
import datetime

from app.db_utils import (
    get_engine,
    get_session_factory,
    get_db_session,
    get_all_station_metadata,
    get_station_details,
    get_distinct_values,
    get_suburbs_for_lgas,
    get_filtered_station_keys,
    get_hourly_data_for_stations
)

class TestDbUtils(unittest.TestCase):

    @patch("app.db_utils.get_engine")
    def test_get_engine(self, mock_get_engine):
        mock_engine = MagicMock()
        mock_get_engine.return_value = mock_engine
        engine = get_engine()
        self.assertIsNotNone(engine)
        mock_get_engine.assert_called_once()

    @patch("app.db_utils.get_session_factory")
    def test_get_session_factory(self, mock_get_session_factory):
        mock_session_factory = MagicMock()
        mock_get_session_factory.return_value = mock_session_factory
        session_factory = get_session_factory()
        self.assertIsNotNone(session_factory)
        mock_get_session_factory.assert_called_once()

    @patch("app.db_utils.get_db_session")
    def test_get_all_station_metadata(self, mock_get_db_session):
        mock_session = MagicMock(spec=Session)
        mock_get_db_session.return_value.__enter__.return_value = mock_session
        mock_df = pd.DataFrame({"station_key": [1], "station_id": [101]})
        with patch("pandas.read_sql", return_value=mock_df):
            result = get_all_station_metadata(None)
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 1)

    @patch("app.db_utils.get_db_session")
    def test_get_station_details(self, mock_get_db_session):
        mock_session = MagicMock(spec=Session)
        mock_station = MagicMock(spec=Station)
        mock_get_db_session.return_value.__enter__.return_value = mock_session
        mock_session.get.return_value = mock_station
        result = get_station_details(None, 1)
        self.assertIsNotNone(result)
        mock_session.get.assert_called_once_with(Station, 1)

    @patch("app.db_utils.get_db_session")
    def test_get_distinct_values(self, mock_get_db_session):
        mock_session = MagicMock(spec=Session)
        mock_get_db_session.return_value.__enter__.return_value = mock_session
        mock_session.scalars.return_value.all.return_value = ["value1", "value2"]
        result = get_distinct_values(None, "column_name")
        self.assertEqual(result, ["value1", "value2"])

    @patch("app.db_utils.get_db_session")
    def test_get_suburbs_for_lgas(self, mock_get_db_session):
        mock_session = MagicMock(spec=Session)
        mock_get_db_session.return_value.__enter__.return_value = mock_session
        mock_session.scalars.return_value.all.return_value = ["Suburb1", "Suburb2"]
        result = get_suburbs_for_lgas(None, ["LGA1", "LGA2"])
        self.assertEqual(result, ["Suburb1", "Suburb2"])

    @patch("app.db_utils.get_db_session")
    def test_get_filtered_station_keys(self, mock_get_db_session):
        mock_session = MagicMock(spec=Session)
        mock_get_db_session.return_value.__enter__.return_value = mock_session
        mock_session.scalars.return_value.all.return_value = [1, 2, 3]
        result = get_filtered_station_keys(None, lgas=["LGA1"], min_quality=3)
        self.assertEqual(result, [1, 2, 3])

    @patch("app.db_utils.get_db_session")
    def test_get_hourly_data_for_stations(self, mock_get_db_session):
        mock_session = MagicMock(spec=Session)
        mock_get_db_session.return_value.__enter__.return_value = mock_session
        mock_df = pd.DataFrame({"station_key": [1], "hour_00": [100]})
        with patch("pandas.read_sql", return_value=mock_df):
            result = get_hourly_data_for_stations(
                None,
                station_keys=[1],
                start_date=datetime.date(2023, 1, 1),
                end_date=datetime.date(2023, 1, 2)
            )
            self.assertIsInstance(result, pd.DataFrame)
            self.assertEqual(len(result), 1)

if __name__ == "__main__":
    unittest.main()