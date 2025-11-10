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
        
        # ESA WorldCover 2021 class values and mapping
        # Reference: https://esa-worldcover.org/en
        self.esa_worldcover_classes = {
            10: 'forest',        # Tree cover
            20: 'shrub',         # Shrubland
            30: 'grass',         # Grassland
            40: 'agriculture',   # Cropland
            50: 'urban',         # Built-up
            60: 'bare_ground',   # Bare / sparse vegetation
            70: 'snow',          # Snow and ice
            80: 'water',         # Permanent water bodies
            90: 'wetland',       # Herbaceous wetland
            95: 'mangrove',      # Mangroves
            100: 'moss'          # Moss and lichen
        }
        
        # Simplified terrain mapping for fire simulation
        self.terrain_mapping = {
            10: 'forest',
            20: 'shrub',
            30: 'grass',
            40: 'agriculture',
            50: 'urban',
            60: 'bare_ground',
            70: 'snow',  # Will treat as bare ground
            80: 'water',
            90: 'wetland',  # Will treat as grass/water mix
            95: 'mangrove',  # Will treat as forest
            100: 'bare_ground'  # Moss as bare ground
        }
        
        # Map legend colors for visualization
        self.legend_colors = {
            'forest': '#228B22',      # Forest green
            'grass': '#90EE90',       # Light green
            'urban': '#808080',       # Gray
            'water': '#4682B4',       # Steel blue
            'agriculture': '#DAA520',  # Goldenrod
            'shrub': '#9ACD32',       # Yellow green
            'bare_ground': '#D2B48C',  # Tan
            'snow': '#FFFFFF',        # White
            'wetland': '#20B2AA',     # Light sea green
            'mangrove': '#006400'     # Dark green
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
        """Download a single ESA WorldCover tile"""
        try:
            # ESA WorldCover 2021 tiles via their WMS service
            # Using OpenLayers XYZ tile format
            # Note: ESA WorldCover is available at zoom levels up to 16
            
            # Primary: ESA WorldCover tiles (land cover classification)
            # Fallback: ESRI satellite imagery for visualization
            urls = [
                # ESA WorldCover Map - provides classified land cover data
                f"https://services.terrascope.be/wms/v2?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&BBOX=-180,-90,180,90&CRS=EPSG:4326&WIDTH=256&HEIGHT=256&LAYERS=WORLDCOVER_2021_MAP&STYLES=&FORMAT=image/png&DPI=96&MAP_RESOLUTION=96&FORMAT_OPTIONS=dpi:96&TRANSPARENT=TRUE",
                # Fallback to ESRI satellite
                f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}",
            ]
            
            # For ESA WorldCover, we need to use their tile service
            # Using the XYZ tile endpoint
            esa_url = f"https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2021_3857/default/g/{zoom}/{y}/{x}.jpg"
            
            # Try ESA WorldCover S2 Cloudless for base imagery combined with classification
            # Then we'll use their classification API
            worldcover_url = f"https://services.terrascope.be/wmts/v2?layer=WORLDCOVER_2021_MAP&style=default&tilematrixset=GoogleMapsCompatible&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image%2Fpng&TileMatrix={zoom}&TileCol={x}&TileRow={y}"
            
            urls = [worldcover_url, esa_url, urls[1]]  # Try WorldCover first, then S2 cloudless, then ESRI
            
            for url in urls:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            image = Image.open(io.BytesIO(image_data))
                            logger.debug(f"Downloaded tile from {url.split('/')[2]}")
                            return np.array(image.convert('RGB'))
                except Exception as e:
                    logger.debug(f"Failed to download from {url.split('/')[2]}: {e}")
                    continue
            
            logger.warning(f"Failed to download tile {x},{y},{zoom} from all sources")
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
        """Classify a single pixel's terrain type based on RGB values from ESA WorldCover or satellite imagery"""
        r, g, b = rgb
        
        # ESA WorldCover uses specific colors for each class
        # We'll detect these and also fall back to satellite imagery classification
        
        # ESA WorldCover color scheme detection
        # Tree cover (10): Dark green ~(0, 100, 0)
        if r < 50 and g > 80 and g < 130 and b < 50:
            return 'forest'
        
        # Shrubland (20): Orange-brown ~(255, 187, 34)
        if r > 200 and g > 150 and g < 200 and b < 100:
            return 'shrub'
        
        # Grassland (30): Yellow-green ~(255, 255, 76)
        if r > 200 and g > 200 and b > 50 and b < 150:
            return 'grass'
        
        # Cropland (40): Magenta-pink ~(240, 150, 255)
        if r > 200 and g > 100 and g < 180 and b > 200:
            return 'agriculture'
        
        # Built-up (50): Red ~(250, 0, 0)
        if r > 200 and g < 50 and b < 50:
            return 'urban'
        
        # Bare/sparse (60): Silver-gray ~(180, 180, 180)
        if abs(r - 180) < 40 and abs(g - 180) < 40 and abs(b - 180) < 40 and r > 140:
            return 'bare_ground'
        
        # Snow and ice (70): White ~(240, 240, 240)
        if r > 220 and g > 220 and b > 220:
            return 'snow'
        
        # Water (80): Blue ~(0, 100, 200)
        if b > 150 and b > r + 50 and b > g + 30:
            return 'water'
        
        # Wetland (90): Cyan ~(0, 150, 160)
        if b > 120 and g > 120 and r < 80:
            return 'wetland'
        
        # Mangroves (95): Dark cyan-green ~(0, 207, 117)
        if g > 150 and g > r + 100 and b > 80 and b < 150:
            return 'mangrove'
        
        # Fallback to satellite imagery-based classification
        # Water detection (blue dominant, low red)
        if b > 100 and b > r + 30 and b > g + 10:
            return 'water'
        
        # Urban/roads detection (gray - similar R, G, B values)
        if abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30:
            if r > 80:  # Light gray (roads, buildings)
                return 'urban'
            elif r < 80 and r > 40:  # Medium gray
                return 'urban'
        
        # Vegetation detection (green channel analysis)
        # Calculate NDVI-like metric: (G - R) / (G + R)
        if g + r > 0:
            green_ratio = (g - r) / (g + r)
            
            # Strong vegetation (forest)
            if green_ratio > 0.15 and g > 80 and r < 120:
                if g < 130:  # Dark green
                    return 'forest'
                else:  # Bright green
                    return 'grass'
            
            # Moderate vegetation (shrub)
            elif green_ratio > 0.05 and g > 60:
                return 'shrub'
        
        # Bare soil/sand detection (brownish - high red, moderate green, low blue)
        if r > g and r > b and r > 100 and b < 130:
            if g > 80:  # Yellowish (agriculture/dry grass)
                return 'agriculture'
            else:  # Brown (bare ground)
                return 'bare_ground'
        
        # Default fallback
        return 'grass'
    
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
        sample_count = 0
        
        for y in range(0, cell_pixels.shape[0], sample_step):
            for x in range(0, cell_pixels.shape[1], sample_step):
                pixel_rgb = tuple(cell_pixels[y, x])
                terrain = self.classify_pixel_terrain(pixel_rgb)
                terrain_votes[terrain] = terrain_votes.get(terrain, 0) + 1
                sample_count += 1
        
        # Return the most common terrain type
        if terrain_votes:
            dominant_terrain = max(terrain_votes.items(), key=lambda x: x[1])[0]
            logger.debug(f"Cell at ({cell_lat:.4f}, {cell_lon:.4f}): sampled {sample_count} pixels, votes: {terrain_votes}, result: {dominant_terrain}")
            return dominant_terrain
        else:
            logger.warning(f"No terrain votes for cell at ({cell_lat:.4f}, {cell_lon:.4f})")
            return 'grass'
    
    async def classify_grid_area(self, lat: float, lon: float, grid_size: int = 50,
                               cell_size_degrees: float = 0.001) -> List[List[Dict]]:
        """Classify terrain for an entire grid area"""
        
        logger.info(f"Starting grid classification for {grid_size}x{grid_size} grid at {lat}, {lon}")
        logger.info(f"Cell size: {cell_size_degrees} degrees (~{cell_size_degrees * 111000:.1f}m)")
        logger.info(f"Total area: {grid_size * cell_size_degrees:.4f} degrees (~{grid_size * cell_size_degrees * 111000:.1f}m)")
        
        # Download tiles for the area
        tiles, zoom, tile_bounds = await self.get_area_tiles(lat, lon, grid_size, cell_size_degrees)
        
        if not tiles:
            logger.warning("No tiles downloaded, using synthetic terrain")
            return self._generate_synthetic_grid(grid_size)
        
        logger.info(f"Downloaded {len(tiles)} tiles at zoom level {zoom}")
        logger.info(f"Tile bounds: {tile_bounds}")
        
        # Classify each grid cell
        grid_classification = []
        terrain_stats = {}
        
        for row in range(grid_size):
            grid_row = []
            for col in range(grid_size):
                # Calculate cell center coordinates
                # Grid starts at top-left (north-west) and goes south and east
                cell_lat = lat - (grid_size * cell_size_degrees / 2) + (row + 0.5) * cell_size_degrees
                cell_lon = lon - (grid_size * cell_size_degrees / 2) + (col + 0.5) * cell_size_degrees
                
                # Classify the cell
                terrain_type = self.classify_grid_cell(tiles, zoom, tile_bounds, 
                                                     cell_lat, cell_lon, cell_size_degrees)
                
                # Track statistics
                terrain_stats[terrain_type] = terrain_stats.get(terrain_type, 0) + 1
                
                # Set terrain-specific properties for fire simulation
                properties = self._get_terrain_properties(terrain_type)
                
                cell_data = {
                    'terrain_type': terrain_type,
                    'color': self.legend_colors[terrain_type],
                    'properties': properties,
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
        logger.info(f"Terrain distribution: {terrain_stats}")
        return grid_classification
    
    def _get_terrain_properties(self, terrain_type: str) -> Dict:
        """Get fire-related properties for a terrain type"""
        
        # Map terrain types to their fire properties
        terrain_properties = {
            'water': {
                'moisture_retention': 1.0,
                'flammability': 0.0,
                'fuel_density': 0.0,
                'is_flammable': False
            },
            'urban': {
                'moisture_retention': 0.2,
                'flammability': 0.1,
                'fuel_density': 0.3,
                'is_flammable': True
            },
            'bare_ground': {
                'moisture_retention': 0.2,
                'flammability': 0.1,
                'fuel_density': 0.05,
                'is_flammable': True
            },
            'grass': {
                'moisture_retention': 0.5,
                'flammability': 0.9,
                'fuel_density': 0.8,
                'is_flammable': True
            },
            'shrub': {
                'moisture_retention': 0.6,
                'flammability': 0.75,
                'fuel_density': 0.7,
                'is_flammable': True
            },
            'forest': {
                'moisture_retention': 0.6,
                'flammability': 0.8,
                'fuel_density': 1.0,
                'is_flammable': True
            },
            'agriculture': {
                'moisture_retention': 0.5,
                'flammability': 0.6,
                'fuel_density': 0.5,
                'is_flammable': True
            }
        }
        
        return terrain_properties.get(terrain_type, terrain_properties['grass'])
    
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
                
                # Set terrain-specific properties for fire simulation
                properties = self._get_terrain_properties(terrain_type)
                
                cell_data = {
                    'terrain_type': terrain_type,
                    'color': self.legend_colors[terrain_type],
                    'properties': properties,
                    'row': row,
                    'col': col,
                    'lat': 0,  # Placeholder
                    'lon': 0   # Placeholder
                }
                
                grid_row.append(cell_data)
            grid.append(grid_row)
        
        return grid
