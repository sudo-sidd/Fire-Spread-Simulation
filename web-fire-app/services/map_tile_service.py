"""
Map Tile Classification Service
Downloads and analyzes map tiles to classify terrain types for grid cells
"""

import numpy as np
import requests
from PIL import Image
import io
import math
from typing import Tuple, Dict, List, Optional
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class MapTileClassifier:
    """Classifies terrain types from map tile imagery"""
    
    def __init__(self):
        self.tile_size = 256  # Standard map tile size
        
        # Color ranges for terrain classification from satellite imagery
        self.terrain_classifiers = {
            'forest': {
                'rgb_ranges': [(20, 80, 20), (80, 160, 80)],  # Dark to medium green
                'priority': 3
            },
            'grass': {
                'rgb_ranges': [(80, 150, 40), (180, 255, 120)],  # Light green
                'priority': 2
            },
            'urban': {
                'rgb_ranges': [(100, 100, 100), (200, 200, 200)],  # Gray tones
                'priority': 4
            },
            'water': {
                'rgb_ranges': [(0, 50, 100), (100, 150, 255)],  # Blue tones
                'priority': 5
            },
            'agriculture': {
                'rgb_ranges': [(150, 120, 60), (255, 200, 120)],  # Brown/tan
                'priority': 2
            },
            'bare_ground': {
                'rgb_ranges': [(120, 100, 80), (200, 180, 160)],  # Sandy/desert
                'priority': 1
            },
            'shrub': {
                'rgb_ranges': [(60, 100, 40), (120, 160, 80)],  # Medium green-brown
                'priority': 2
            }
        }
        
        # Map legend colors for visualization
        self.legend_colors = {
            'forest': '#228B22',      # Forest green
            'grass': '#90EE90',       # Light green
            'urban': '#808080',       # Gray
            'water': '#4682B4',       # Steel blue
            'agriculture': '#DAA520',  # Goldenrod
            'shrub': '#9ACD32',       # Yellow green
            'bare_ground': '#D2B48C'   # Tan
        }
    
    def deg2num(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile coordinates"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (x, y)
    
    def num2deg(self, x: int, y: int, zoom: int) -> Tuple[float, float]:
        """Convert tile coordinates to lat/lon"""
        n = 2.0 ** zoom
        lon_deg = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)
    
    async def download_tile(self, session: aiohttp.ClientSession, x: int, y: int, zoom: int) -> Optional[np.ndarray]:
        """Download a single map tile"""
        try:
            # Using OpenStreetMap tiles - in production consider using satellite imagery
            url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
            
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    image = Image.open(io.BytesIO(image_data))
                    return np.array(image.convert('RGB'))
                else:
                    logger.warning(f"Failed to download tile {x},{y},{zoom}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading tile {x},{y},{zoom}: {e}")
            return None
    
    async def get_area_tiles(self, lat: float, lon: float, grid_size: int, 
                           cell_size_degrees: float = 0.001) -> List[List[np.ndarray]]:
        """Download tiles for the entire grid area"""
        
        # Calculate the area bounds
        half_size = grid_size * cell_size_degrees / 2
        north = lat + half_size
        south = lat - half_size
        east = lon + half_size
        west = lon - half_size
        
        # Determine zoom level for good resolution
        zoom = 16  # Good balance between detail and download time
        
        # Get tile coordinates for corners
        min_x, max_y = self.deg2num(north, west, zoom)
        max_x, min_y = self.deg2num(south, east, zoom)
        
        # Download all tiles in the area
        tiles = {}
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    task = self.download_tile(session, x, y, zoom)
                    tasks.append((x, y, task))
            
            # Wait for all downloads
            results = await asyncio.gather(*[task for _, _, task in tasks])
            
            # Organize tiles by coordinates
            for i, (x, y, _) in enumerate(tasks):
                if results[i] is not None:
                    tiles[(x, y)] = results[i]
        
        return tiles, zoom, (min_x, min_y, max_x, max_y)
    
    def classify_pixel_terrain(self, rgb: Tuple[int, int, int]) -> str:
        """Classify a single pixel's terrain type based on RGB values"""
        r, g, b = rgb
        
        best_match = 'grass'  # Default
        best_score = 0
        
        for terrain_type, classifier in self.terrain_classifiers.items():
            for rgb_min, rgb_max in classifier['rgb_ranges']:
                r_min, g_min, b_min = rgb_min
                r_max, g_max, b_max = rgb_max
                
                # Check if pixel falls within this range
                if (r_min <= r <= r_max and 
                    g_min <= g <= g_max and 
                    b_min <= b <= b_max):
                    
                    # Calculate confidence score based on how centered the color is
                    r_center = (r_min + r_max) / 2
                    g_center = (g_min + g_max) / 2
                    b_center = (b_min + b_max) / 2
                    
                    distance = math.sqrt((r - r_center)**2 + (g - g_center)**2 + (b - b_center)**2)
                    max_distance = math.sqrt((r_max - r_min)**2 + (g_max - g_min)**2 + (b_max - b_min)**2)
                    
                    score = (1 - distance / max_distance) * classifier['priority']
                    
                    if score > best_score:
                        best_score = score
                        best_match = terrain_type
        
        return best_match
    
    def classify_grid_cell(self, tiles: Dict, zoom: int, tile_bounds: Tuple,
                          cell_lat: float, cell_lon: float, 
                          cell_size_degrees: float) -> str:
        """Classify terrain type for a single grid cell"""
        
        # Get tile coordinate for this cell
        tile_x, tile_y = self.deg2num(cell_lat, cell_lon, zoom)
        
        if (tile_x, tile_y) not in tiles:
            return 'grass'  # Default if no tile available
        
        tile_image = tiles[(tile_x, tile_y)]
        
        # Calculate pixel coordinates within the tile
        # Convert cell bounds to tile pixel coordinates
        north_lat = cell_lat + cell_size_degrees / 2
        south_lat = cell_lat - cell_size_degrees / 2
        east_lon = cell_lon + cell_size_degrees / 2
        west_lon = cell_lon - cell_size_degrees / 2
        
        # Get tile boundaries in lat/lon
        tile_north, tile_west = self.num2deg(tile_x, tile_y, zoom)
        tile_south, tile_east = self.num2deg(tile_x + 1, tile_y + 1, zoom)
        
        # Calculate pixel boundaries within the tile
        x_min = max(0, int((west_lon - tile_west) / (tile_east - tile_west) * self.tile_size))
        x_max = min(self.tile_size, int((east_lon - tile_west) / (tile_east - tile_west) * self.tile_size))
        y_min = max(0, int((tile_north - north_lat) / (tile_north - tile_south) * self.tile_size))
        y_max = min(self.tile_size, int((tile_north - south_lat) / (tile_north - tile_south) * self.tile_size))
        
        if x_max <= x_min or y_max <= y_min:
            return 'grass'  # Default if invalid bounds
        
        # Sample pixels from the cell area
        cell_pixels = tile_image[y_min:y_max, x_min:x_max]
        
        if cell_pixels.size == 0:
            return 'grass'
        
        # Classify based on dominant terrain type in the cell
        terrain_votes = {}
        
        # Sample pixels (downsample if too many)
        sample_step = max(1, cell_pixels.shape[0] // 10)  # Sample up to 100 pixels
        
        for y in range(0, cell_pixels.shape[0], sample_step):
            for x in range(0, cell_pixels.shape[1], sample_step):
                pixel_rgb = tuple(cell_pixels[y, x])
                terrain = self.classify_pixel_terrain(pixel_rgb)
                terrain_votes[terrain] = terrain_votes.get(terrain, 0) + 1
        
        # Return the most common terrain type
        if terrain_votes:
            return max(terrain_votes, key=terrain_votes.get)
        else:
            return 'grass'
    
    async def classify_grid_area(self, lat: float, lon: float, grid_size: int = 50,
                               cell_size_degrees: float = 0.001) -> List[List[Dict]]:
        """Classify terrain for an entire grid area"""
        
        logger.info(f"Starting grid classification for {grid_size}x{grid_size} grid at {lat}, {lon}")
        
        # Download tiles for the area
        tiles, zoom, tile_bounds = await self.get_area_tiles(lat, lon, grid_size, cell_size_degrees)
        
        if not tiles:
            logger.warning("No tiles downloaded, using synthetic terrain")
            return self._generate_synthetic_grid(grid_size)
        
        # Classify each grid cell
        grid_classification = []
        
        for row in range(grid_size):
            grid_row = []
            for col in range(grid_size):
                # Calculate cell center coordinates
                cell_lat = lat - (grid_size * cell_size_degrees / 2) + (row + 0.5) * cell_size_degrees
                cell_lon = lon - (grid_size * cell_size_degrees / 2) + (col + 0.5) * cell_size_degrees
                
                # Classify the cell
                terrain_type = self.classify_grid_cell(tiles, zoom, tile_bounds, 
                                                     cell_lat, cell_lon, cell_size_degrees)
                
                cell_data = {
                    'terrain_type': terrain_type,
                    'color': self.legend_colors[terrain_type],
                    'row': row,
                    'col': col,
                    'lat': cell_lat,
                    'lon': cell_lon
                }
                
                grid_row.append(cell_data)
            
            grid_classification.append(grid_row)
            
            # Log progress
            if (row + 1) % 10 == 0:
                logger.info(f"Classified {row + 1}/{grid_size} rows")
        
        logger.info(f"Grid classification completed")
        return grid_classification
    
    def _generate_synthetic_grid(self, grid_size: int) -> List[List[Dict]]:
        """Generate synthetic terrain grid as fallback"""
        
        logger.info("Generating synthetic terrain grid")
        
        grid = []
        center = grid_size // 2
        
        for row in range(grid_size):
            grid_row = []
            for col in range(grid_size):
                # Distance from center
                dist = math.sqrt((row - center)**2 + (col - center)**2)
                
                # Generate terrain based on patterns
                rand = np.random.random()
                
                if rand < 0.1:
                    terrain_type = 'water'
                elif dist < grid_size * 0.15 and rand < 0.3:
                    terrain_type = 'urban'
                elif rand < 0.4:
                    terrain_type = 'forest'
                elif rand < 0.6:
                    terrain_type = 'agriculture'
                elif rand < 0.8:
                    terrain_type = 'grass'
                else:
                    terrain_type = 'shrub'
                
                cell_data = {
                    'terrain_type': terrain_type,
                    'color': self.legend_colors[terrain_type],
                    'row': row,
                    'col': col,
                    'lat': 0,  # Placeholder
                    'lon': 0   # Placeholder
                }
                
                grid_row.append(cell_data)
            grid.append(grid_row)
        
        return grid
