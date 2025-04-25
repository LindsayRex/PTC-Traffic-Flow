# conftest.py - Configure pytest for the entire test suite
import os
import sys
import warnings
import pytest
from pathlib import Path
from unittest.mock import patch

# Import SAWarning early for the filter
try:
    from sqlalchemy.exc import SAWarning
except ImportError:
    print("Warning: Could not import SAWarning in conftest.py. Warning filtering might be less specific.")
    SAWarning = Warning  # Fallback

# --- WARNING FILTER (Applied VERY EARLY in conftest.py) ---
# This targets the specific geoalchemy2 warning by message, category, AND module
warnings.filterwarnings(
    "ignore",
    message=r"The GenericFunction '.+' is already registered and is going to be overridden\.",
    category=SAWarning,
    module=r"geoalchemy2\.functions"  # Add the module filter!
)

# Add the project root to the PYTHONPATH AFTER initial imports and filters
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Now it's safe to import other modules if needed


from collections.abc import Generator

@pytest.fixture(scope="session", autouse=True)
def suppress_geoalchemy2_warnings() -> Generator[None, None, None]:
    """
    Suppress GeoAlchemy2 function registration warnings.

    Note: This fixture is mainly kept for backward compatibility.
    Most warnings should already be filtered by the early warning filter.
    """
    # The early filter should handle most cases, but keep the patch as a fallback
    with patch("geoalchemy2.functions.GenericFunction.__init_subclass__",
               side_effect=lambda *args, **kwargs: None):
        yield


def pytest_configure(config):
    """Configure pytest with custom settings including warning filters."""
    # The filter is already applied at the top level, this is redundant but harmless
    warnings.filterwarnings(
        'ignore',
        message=r"The GenericFunction '.+' is already registered and is going to be overridden\.",
        category=SAWarning,
        module=r"geoalchemy2\.functions"  # Ensure module is here too
    )
    
    # Add any other global test configuration here