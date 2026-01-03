# # src/utils/__init__.py

import os
from typing import Optional

# def validate_env_variables() -> bool:
#     """Validate that required environment variables are set."""
#     required_vars = ['MAPBOX_ACCESS_TOKEN']

#     missing = []
#     for var in required_vars:
#         if not os.getenv(var):
#             missing.append(var)

#     if missing:
#         print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
#         return False

#     return True


def get_mapbox_token() -> Optional[str]:
    """Safely retrieve Mapbox token."""
    return os.getenv('MAPBOX_ACCESS_TOKEN')


def format_coordinates(lat: float, lon: float) -> str:
    """Format coordinates for display."""
    lat_dir = 'N' if lat >= 0 else 'S'
    lon_dir = 'E' if lon >= 0 else 'W'
    return f"{abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}"


# # Export submodules
# from .stderr_filter import apply_stderr_filter, StderrFilter

# __all__ = [
#     'validate_env_variables',
#     'get_mapbox_token',
#     'format_coordinates',
#     'EventProcessor',
#     'process_runner_events',
#     'apply_stderr_filter',
#     'StderrFilter'
# ]
