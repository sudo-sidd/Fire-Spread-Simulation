"""
Configuration settings for the Fire Spread Simulation Web Application
"""

import os
from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fire-simulation-secret-key-2024'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Map settings
    DEFAULT_ZOOM = 10
    DEFAULT_LAT = 39.8283  # Center of USA
    DEFAULT_LON = -98.5795
    MAP_TILE_SIZE = 512
    
    # Simulation grid settings
    GRID_SIZE = 200  # 200x200 grid for detailed simulation
    CELL_SIZE = 2    # Pixel size of each cell in visualization
    
    # Fire simulation parameters
    IGNITION_PROBABILITY = 0.001  # Spontaneous ignition chance
    SPREAD_PROBABILITY = 0.4      # Fire spread probability
    BURN_TIME = 5                 # Steps a cell burns before becoming ash
    WIND_FACTOR = 1.2            # Wind influence multiplier
    
    # Terrain types and their fire properties
    TERRAIN_TYPES = {
        'water': {'color': (0, 100, 200), 'fuel_load': 0, 'spread_rate': 0},
        'urban': {'color': (128, 128, 128), 'fuel_load': 0.1, 'spread_rate': 0.2},
        'bare_ground': {'color': (139, 69, 19), 'fuel_load': 0.05, 'spread_rate': 0.1},
        'grass': {'color': (124, 252, 0), 'fuel_load': 0.8, 'spread_rate': 0.9},
        'shrub': {'color': (34, 139, 34), 'fuel_load': 0.6, 'spread_rate': 0.7},
        'forest': {'color': (0, 100, 0), 'fuel_load': 1.0, 'spread_rate': 0.8},
        'agriculture': {'color': (255, 215, 0), 'fuel_load': 0.4, 'spread_rate': 0.5}
    }
    
    # Fire state colors (RGB)
    FIRE_COLORS = {
        'normal': (0, 0, 0, 0),        # Transparent for normal terrain
        'burning': (255, 0, 0, 255),    # Bright red for active fire
        'burned': (64, 64, 64, 255),    # Dark gray for burned areas
        'smoldering': (255, 140, 0, 255), # Orange for smoldering
        'extinguished': (100, 100, 100, 255)  # Gray for extinguished
    }
    
    # API settings
    SATELLITE_API_TIMEOUT = 30
    MAX_REQUEST_SIZE = 16 * 1024 * 1024  # 16MB
    
    # File paths
    TEMP_DIR = 'temp'
    IMAGES_DIR = 'static/images'
    DATA_DIR = 'data'
    
    # Weather data settings
    WEATHER_UPDATE_INTERVAL = 3600  # 1 hour in seconds
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        for dir_path in [cls.TEMP_DIR, cls.IMAGES_DIR, cls.DATA_DIR]:
            os.makedirs(dir_path, exist_ok=True)
