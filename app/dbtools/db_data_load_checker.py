import logging
import pandas as pd
import sys
from pathlib import Path
from sqlalchemy.orm import Session

# Ensure project root is in the Python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Now use absolute imports consistently
from app.models import Station, HourlyCount

logger = logging.getLogger(__name__)

def validate_station_data(df: pd.DataFrame) -> bool:
    """
    Validates station data in a Pandas DataFrame.

    Args:
        df: The Pandas DataFrame containing station data.

    Returns:
        True if the data is valid, False otherwise.
    """
    # Check for required columns
    required_columns = [
        'station_key', 'station_id', 'name', 'road_name', 'full_name',
        'common_road_name', 'lga', 'suburb', 'post_code',
        'road_functional_hierarchy', 'lane_count', 'road_classification_type',
        'device_type', 'permanent_station', 'vehicle_classifier',
        'heavy_vehicle_checking_station', 'quality_rating', 'wgs84_latitude',
        'wgs84_longitude'
    ]
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False

    # Check data types (example)
    if not pd.api.types.is_numeric_dtype(df['station_key']):
        logger.error("station_key must be numeric")
        return False
    if not pd.api.types.is_numeric_dtype(df['wgs84_latitude']):
        logger.error("wgs84_latitude must be numeric")
        return False
    if not pd.api.types.is_numeric_dtype(df['wgs84_longitude']):
        logger.error("wgs84_longitude must be numeric")
        return False

    # Check for missing values (example)
    if df[['station_key', 'wgs84_latitude', 'wgs84_longitude']].isnull().values.any():
        logger.error("Missing values found in station_key, wgs84_latitude, or wgs84_longitude")
        return False

    # Add more validation checks as needed (e.g., range checks, value constraints)

    logger.info("Station data validation passed")
    return True

def validate_hourly_count_data(df: pd.DataFrame) -> bool:
    """
    Validates hourly count data in a Pandas DataFrame.

    Args:
        df: The Pandas DataFrame containing hourly count data.

    Returns:
        True if the data is valid, False otherwise.
    """
    # Check for required columns (excluding hourly columns)
    required_columns = [
        'station_key', 'traffic_direction_seq', 'cardinal_direction_seq',
        'classification_seq', 'date', 'year', 'month', 'day_of_week',
        'is_public_holiday', 'is_school_holiday', 'daily_total'
    ]
    for col in required_columns:
        if col not in df.columns:
            logger.error(f"Missing required column: {col}")
            return False

     # Check data types (example)
    if not pd.api.types.is_numeric_dtype(df['station_key']):
        logger.error("station_key must be numeric")
        return False
    if not pd.api.types.is_numeric_dtype(df['traffic_direction_seq']):
        logger.error("traffic_direction_seq must be numeric")
        return False
    if not pd.api.types.is_numeric_dtype(df['cardinal_direction_seq']):
        logger.error("cardinal_direction_seq must be numeric")
        return False
    if not pd.api.types.is_numeric_dtype(df['classification_seq']):
        logger.error("classification_seq must be numeric")
        return False
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        logger.error("date must be a datetime")
        return False
    if not pd.api.types.is_numeric_dtype(df['daily_total']):
        logger.error("daily_total must be numeric")
        return False

    # Check for missing values (example)
    if df[['station_key', 'traffic_direction_seq', 'cardinal_direction_seq', 'classification_seq', 'date', 'daily_total']].isnull().values.any():
        logger.error("Missing values found in station_key, traffic_direction_seq, cardinal_direction_seq, classification_seq, or date")
        return False

    # Check for valid ranges (example)
    if (df['traffic_direction_seq'] < 1).any() or (df['traffic_direction_seq'] > 2).any():
        logger.error("traffic_direction_seq must be 1 or 2")
        return False
    if (df['cardinal_direction_seq'] < 1).any() or (df['cardinal_direction_seq'] > 4).any():
        logger.error("cardinal_direction_seq must be between 1 and 4")
        return False
    if (df['classification_seq'] < 0).any() or (df['classification_seq'] > 3).any():
        logger.error("classification_seq must be between 0 and 3")
        return False

    # Add more validation checks as needed

    logger.info("Hourly count data validation passed")
    return True