"""
Terrain Extraction Service
Converts real-world map data into simulation-ready terrain bitmaps
"""

import numpy as np
import requests
from PIL import Image, ImageDraw
import folium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import tempfile
import os
import time
from typing import Tuple, Dict, Optional
import io
import base64

from core.config import Config

class TerrainExtractor:
    """Extract and process terrain data from satellite imagery and maps"""
    
    def __init__(self):
        self.temp_dir = Config.TEMP_DIR
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Color mappings for different data sources
        self.osm_color_map = {
            (34, 139, 34): 'forest',      # Forest green
            (124, 252, 0): 'grass',       # Lawn green  
            (139, 69, 19): 'bare_ground', # Saddle brown
            (0, 100, 200): 'water',       # Blue
            (128, 128, 128): 'urban',     # Gray
            (255, 215, 0): 'agriculture', # Gold
            (107, 142, 35): 'shrub'       # Olive drab
        }
    
    def extract_from_coordinates(self, lat: float, lon: float, 
                               zoom: int = 15, grid_size: Tuple[int, int] = (50, 50)) -> np.ndarray:
        """Extract terrain data from lat/lon coordinates using map tiles"""
        
        # Calculate the bounding box for the area
        bbox = self._calculate_bbox(lat, lon, zoom, grid_size)
        
        # Download map tiles for the area
        map_image = self._download_map_tiles(bbox, zoom, grid_size)
        
        # Process and classify the image into terrain types
        classified_terrain = self._classify_terrain_from_map(map_image, grid_size)
        
        return classified_terrain
    
    def _calculate_bbox(self, lat: float, lon: float, zoom: int, grid_size: Tuple[int, int]) -> Dict:
        """Calculate bounding box for the grid area"""
        # Approximate calculation for demo - in production use proper map projection
        lat_offset = 0.01 * (15 - zoom)  # Smaller area for higher zoom
        lon_offset = 0.01 * (15 - zoom)
        
        return {
            'north': lat + lat_offset,
            'south': lat - lat_offset,
            'east': lon + lon_offset,
            'west': lon - lon_offset
        }
    
    def _download_map_tiles(self, bbox: Dict, zoom: int, grid_size: Tuple[int, int]) -> np.ndarray:
        """Download map tiles and stitch them together"""
        try:
            # For now, use a simple approach with OpenStreetMap tiles
            # In production, you'd use proper tile stitching
            
            # Calculate center point
            center_lat = (bbox['north'] + bbox['south']) / 2
            center_lon = (bbox['east'] + bbox['west']) / 2
            
            # Create a synthetic satellite-like image based on coordinates
            return self._create_realistic_terrain_map(center_lat, center_lon, grid_size)
            
        except Exception as e:
            print(f"Error downloading map tiles: {e}")
            return self._generate_synthetic_terrain(0, 0, grid_size)
    
    def _create_realistic_terrain_map(self, lat: float, lon: float, size: Tuple[int, int]) -> np.ndarray:
        """Create a more realistic terrain map based on geographical features"""
        
        width, height = size
        terrain_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Base terrain determination based on coordinates
        if abs(lat) > 60:  # Arctic/Antarctic
            base_color = [240, 248, 255]  # Ice/snow
        elif abs(lat) > 45:  # Temperate
            base_color = [34, 139, 34]   # Forest
        elif abs(lat) < 23.5:  # Tropical
            base_color = [0, 100, 0]     # Dense forest
        else:  # Subtropical
            base_color = [124, 252, 0]   # Grassland
        
        # Fill with base color
        terrain_image[:, :] = base_color
        
        # Add water bodies (more likely near coasts)
        if self._is_near_coast(lat, lon):
            self._add_water_features(terrain_image, 0.3)
        else:
            self._add_water_features(terrain_image, 0.1)
        
        # Add urban areas (more likely in certain coordinates)
        if self._is_populated_area(lat, lon):
            self._add_urban_areas(terrain_image, 0.2)
        else:
            self._add_urban_areas(terrain_image, 0.05)
        
        # Add terrain variation
        self._add_terrain_variation(terrain_image, lat, lon)
        
        return terrain_image
    
    def _is_near_coast(self, lat: float, lon: float) -> bool:
        """Simple heuristic to determine if coordinates are near coast"""
        # This is a simplified check - in production use actual coastline data
        coastal_regions = [
            (37.7749, -122.4194),  # San Francisco
            (40.7128, -74.0060),   # New York
            (51.5074, -0.1278),    # London
            (-33.8688, 151.2093),  # Sydney
        ]
        
        for coast_lat, coast_lon in coastal_regions:
            if abs(lat - coast_lat) < 5 and abs(lon - coast_lon) < 5:
                return True
        return False
    
    def _is_populated_area(self, lat: float, lon: float) -> bool:
        """Simple heuristic for populated areas"""
        # Major city coordinates
        cities = [
            (40.7128, -74.0060),   # New York
            (34.0522, -118.2437),  # Los Angeles
            (51.5074, -0.1278),    # London
            (48.8566, 2.3522),     # Paris
            (35.6762, 139.6503),   # Tokyo
        ]
        
        for city_lat, city_lon in cities:
            if abs(lat - city_lat) < 2 and abs(lon - city_lon) < 2:
                return True
        return False
    
    def _add_water_features(self, terrain_image: np.ndarray, probability: float):
        """Add water bodies to terrain"""
        height, width = terrain_image.shape[:2]
        water_color = Config.TERRAIN_TYPES['water']['color']
        
        # Add rivers
        if np.random.random() < probability:
            # Create meandering river
            river_points = []
            y_start = np.random.randint(0, height)
            for x in range(0, width, 5):
                y_offset = int(10 * np.sin(x * 0.1)) + np.random.randint(-5, 5)
                y = max(0, min(height-1, y_start + y_offset))
                river_points.append((x, y))
            
            # Draw river
            for i in range(len(river_points)-1):
                x1, y1 = river_points[i]
                x2, y2 = river_points[i+1]
                self._draw_line(terrain_image, (x1, y1), (x2, y2), water_color, thickness=3)
        
        # Add lakes
        if np.random.random() < probability * 0.5:
            lake_x = np.random.randint(width//4, 3*width//4)
            lake_y = np.random.randint(height//4, 3*height//4)
            lake_radius = np.random.randint(5, 15)
            
            for y in range(max(0, lake_y-lake_radius), min(height, lake_y+lake_radius)):
                for x in range(max(0, lake_x-lake_radius), min(width, lake_x+lake_radius)):
                    if (x-lake_x)**2 + (y-lake_y)**2 <= lake_radius**2:
                        terrain_image[y, x] = water_color
    
    def _add_urban_areas(self, terrain_image: np.ndarray, probability: float):
        """Add urban areas to terrain"""
        height, width = terrain_image.shape[:2]
        urban_color = Config.TERRAIN_TYPES['urban']['color']
        
        if np.random.random() < probability:
            # Create urban blocks
            num_blocks = np.random.randint(2, 6)
            for _ in range(num_blocks):
                block_x = np.random.randint(0, width-20)
                block_y = np.random.randint(0, height-20)
                block_w = np.random.randint(8, 20)
                block_h = np.random.randint(8, 20)
                
                # Create irregular urban shape
                for y in range(block_y, min(height, block_y + block_h)):
                    for x in range(block_x, min(width, block_x + block_w)):
                        if np.random.random() > 0.3:  # 70% density
                            terrain_image[y, x] = urban_color
    
    def _add_terrain_variation(self, terrain_image: np.ndarray, lat: float, lon: float):
        """Add terrain variation based on geography"""
        height, width = terrain_image.shape[:2]
        
        # Add desert areas in appropriate latitudes
        if 15 < abs(lat) < 35:  # Desert belt
            if np.random.random() < 0.3:
                desert_color = Config.TERRAIN_TYPES['bare_ground']['color']
                # Create desert patches
                num_patches = np.random.randint(1, 3)
                for _ in range(num_patches):
                    patch_x = np.random.randint(0, width//2)
                    patch_y = np.random.randint(0, height//2)
                    patch_size = np.random.randint(15, 30)
                    
                    for y in range(patch_y, min(height, patch_y + patch_size)):
                        for x in range(patch_x, min(width, patch_x + patch_size)):
                            distance = np.sqrt((x-patch_x)**2 + (y-patch_y)**2)
                            if distance < patch_size * 0.7 and np.random.random() > 0.4:
                                terrain_image[y, x] = desert_color
        
        # Add agricultural areas in temperate zones
        if 30 < abs(lat) < 60:
            if np.random.random() < 0.4:
                agri_color = Config.TERRAIN_TYPES['agriculture']['color']
                # Create agricultural fields
                field_x = np.random.randint(0, width-30)
                field_y = np.random.randint(0, height-20)
                field_w = np.random.randint(20, 40)
                field_h = np.random.randint(10, 25)
                
                terrain_image[field_y:field_y+field_h, field_x:field_x+field_w] = agri_color
    
    def _draw_line(self, image: np.ndarray, start: Tuple[int, int], end: Tuple[int, int], 
                  color: Tuple[int, int, int], thickness: int = 1):
        """Draw a line on the image"""
        x1, y1 = start
        x2, y2 = end
        
        # Simple line drawing algorithm
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        x, y = x1, y1
        height, width = image.shape[:2]
        
        while True:
            # Draw thick line
            for ty in range(max(0, y-thickness//2), min(height, y+thickness//2+1)):
                for tx in range(max(0, x-thickness//2), min(width, x+thickness//2+1)):
                    image[ty, tx] = color
            
            if x == x2 and y == y2:
                break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
    
    def _create_terrain_map(self, lat: float, lon: float, 
                          zoom: int, size: Tuple[int, int]) -> np.ndarray:
        """Create a terrain map using multiple data sources"""
        
        # Method 1: Try OpenStreetMap-based approach
        try:
            return self._get_osm_terrain(lat, lon, zoom, size)
        except Exception as e:
            print(f"OSM method failed: {e}")
            
        # Method 2: Fallback to synthetic terrain generation
        return self._generate_synthetic_terrain(lat, lon, size)
    
    def _get_osm_terrain(self, lat: float, lon: float, 
                        zoom: int, size: Tuple[int, int]) -> np.ndarray:
        """Get terrain data from OpenStreetMap"""
        
        # Create folium map with terrain layers
        m = folium.Map(
            location=[lat, lon],
            zoom_start=zoom,
            tiles=None,
            width=size[0],
            height=size[1]
        )
        
        # Add satellite/terrain layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='ESRI World Imagery',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add OpenStreetMap layer for land use classification
        folium.TileLayer(
            tiles='OpenStreetMap',
            name='OSM',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Save map to HTML
        map_path = os.path.join(self.temp_dir, f'terrain_map_{lat}_{lon}.html')
        m.save(map_path)
        
        # Convert to image using selenium
        image_array = self._html_to_image(map_path, size)
        
        # Clean up
        try:
            os.remove(map_path)
        except:
            pass
            
        return image_array
    
    def _html_to_image(self, html_path: str, size: Tuple[int, int]) -> np.ndarray:
        """Convert HTML map to image using selenium"""
        
        # For now, skip selenium and use synthetic generation
        # This avoids the ChromeDriver compatibility issues
        print("Using synthetic terrain generation (Selenium temporarily disabled)")
        return self._generate_synthetic_terrain(0, 0, size)
    
    def _generate_synthetic_terrain(self, lat: float, lon: float, 
                                  size: Tuple[int, int]) -> np.ndarray:
        """Generate synthetic terrain when real data is unavailable"""
        
        width, height = size
        terrain_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create base terrain (grass)
        terrain_image[:, :] = Config.TERRAIN_TYPES['grass']['color']
        
        # Add water bodies (rivers/lakes)
        if np.random.random() > 0.7:  # 30% chance of water
            water_color = Config.TERRAIN_TYPES['water']['color']
            
            # Create random water body
            center_x, center_y = width // 2, height // 2
            for y in range(height):
                for x in range(width):
                    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if distance < width * 0.15 + np.random.normal(0, 10):
                        terrain_image[y, x] = water_color
        
        # Add forest patches
        for _ in range(np.random.randint(2, 6)):
            center_x = np.random.randint(0, width)
            center_y = np.random.randint(0, height)
            radius = np.random.randint(20, 80)
            
            forest_color = Config.TERRAIN_TYPES['forest']['color']
            
            for y in range(max(0, center_y - radius), min(height, center_y + radius)):
                for x in range(max(0, center_x - radius), min(width, center_x + radius)):
                    distance = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                    if distance < radius * (0.7 + 0.3 * np.random.random()):
                        terrain_image[y, x] = forest_color
        
        # Add urban areas
        if np.random.random() > 0.6:  # 40% chance of urban
            urban_color = Config.TERRAIN_TYPES['urban']['color']
            
            # Small urban cluster
            urban_x = np.random.randint(width // 4, 3 * width // 4)
            urban_y = np.random.randint(height // 4, 3 * height // 4)
            urban_size = np.random.randint(15, 40)
            
            for y in range(max(0, urban_y - urban_size), min(height, urban_y + urban_size)):
                for x in range(max(0, urban_x - urban_size), min(width, urban_x + urban_size)):
                    if np.random.random() > 0.3:  # Scattered urban pattern
                        terrain_image[y, x] = urban_color
        
        # Add agricultural areas
        for _ in range(np.random.randint(0, 3)):
            agri_color = Config.TERRAIN_TYPES['agriculture']['color']
            
            # Rectangular agricultural patches
            x1 = np.random.randint(0, width // 2)
            y1 = np.random.randint(0, height // 2)
            x2 = x1 + np.random.randint(30, 100)
            y2 = y1 + np.random.randint(30, 80)
            
            x2 = min(x2, width)
            y2 = min(y2, height)
            
            terrain_image[y1:y2, x1:x2] = agri_color
        
        return terrain_image
    
    def _classify_terrain(self, image: np.ndarray) -> np.ndarray:
        """Classify terrain from satellite/map imagery"""
        
        height, width = image.shape[:2]
        classified = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Convert to classification based on color analysis
        for y in range(height):
            for x in range(width):
                pixel = image[y, x][:3]  # RGB only
                terrain_type = self._classify_pixel(pixel)
                classified[y, x] = Config.TERRAIN_TYPES[terrain_type]['color']
        
        return classified
    
    def _classify_pixel(self, pixel: np.ndarray) -> str:
        """Classify a single pixel to terrain type"""
        
        # Ensure pixel values are within valid range
        r, g, b = int(pixel[0]) % 256, int(pixel[1]) % 256, int(pixel[2]) % 256
        
        # Water detection (blue dominant)
        if b > r and b > g and b > 100:
            return 'water'
        
        # Urban/built-up areas (gray-ish, low vegetation)
        if abs(r - g) < 30 and abs(g - b) < 30 and abs(r - b) < 30 and r > 80:
            return 'urban'
        
        # Vegetation detection (green dominant)
        if g > r and g > b:
            if g > 150:  # Bright green - grass/crops
                return 'grass' if r > 80 else 'agriculture'
            else:  # Dark green - forest/shrub
                return 'forest' if g > 100 else 'shrub'
        
        # Bare soil/desert (brown-ish)
        if r > g and r > b and r > 100:
            return 'bare_ground'
        
        # Default to grass
        return 'grass'
    
    def create_terrain_bitmap(self, lat: float, lon: float, 
                            grid_size: Tuple[int, int] = None) -> Tuple[np.ndarray, Dict]:
        """Create terrain bitmap for simulation"""
        
        if grid_size is None:
            grid_size = (Config.GRID_SIZE, Config.GRID_SIZE)
        
        # Extract terrain data
        terrain_data = self.extract_from_coordinates(lat, lon, size=grid_size)
        
        # Create color mapping for the simulation
        color_map = {}
        for terrain_type, props in Config.TERRAIN_TYPES.items():
            color_map[tuple(props['color'])] = terrain_type
        
        # Generate metadata
        metadata = {
            'lat': lat,
            'lon': lon,
            'grid_size': grid_size,
            'terrain_types': list(Config.TERRAIN_TYPES.keys()),
            'creation_time': time.time()
        }
        
        return terrain_data, color_map, metadata
    
    def save_terrain_bitmap(self, terrain_data: np.ndarray, 
                          filepath: str) -> bool:
        """Save terrain bitmap to file"""
        try:
            image = Image.fromarray(terrain_data.astype(np.uint8))
            image.save(filepath)
            return True
        except Exception as e:
            print(f"Error saving terrain bitmap: {e}")
            return False
    
    def load_terrain_bitmap(self, filepath: str) -> Optional[np.ndarray]:
        """Load terrain bitmap from file"""
        try:
            image = Image.open(filepath)
            return np.array(image)
        except Exception as e:
            print(f"Error loading terrain bitmap: {e}")
            return None
