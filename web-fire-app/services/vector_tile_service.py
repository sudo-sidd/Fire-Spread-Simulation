"""
Vector Tile Classification Service
Downloads and analyzes OSM vector tiles to classify terrain types for grid cells
Supports proper landuse/landcover classification from OpenStreetMap data
"""

import numpy as np
import requests
import json
import math
import sqlite3
import geopandas as gpd
from shapely.geometry import Point, Polygon, box
from typing import Tuple, Dict, List, Optional, Any
import asyncio
import aiohttp
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class VectorTileClassifier:
    """Classifies terrain types from OSM vector tile data"""
    
    def __init__(self):
        # OSM landuse/landcover to our terrain type mapping
        self.osm_terrain_mapping = {
            # Forest and natural areas
            'forest': 'forest',
            'wood': 'forest',
            'woodland': 'forest',
            'natural_wood': 'forest',
            
            # Grass and meadows
            'grass': 'grass',
            'meadow': 'grass',
            'grassland': 'grass',
            'recreation_ground': 'grass',
            'village_green': 'grass',
            'park': 'grass',
            
            # Urban areas
            'residential': 'urban',
            'commercial': 'urban',
            'industrial': 'urban',
            'retail': 'urban',
            'construction': 'urban',
            'built_up_area': 'urban',
            'building': 'urban',
            
            # Water bodies
            'water': 'water',
            'wetland': 'water',
            'reservoir': 'water',
            'river': 'water',
            'stream': 'water',
            'lake': 'water',
            'pond': 'water',
            
            # Agriculture
            'farmland': 'agriculture',
            'allotments': 'agriculture',
            'orchard': 'agriculture',
            'vineyard': 'agriculture',
            'plant_nursery': 'agriculture',
            'greenhouse_horticulture': 'agriculture',
            
            # Shrubland and scrub
            'scrub': 'shrub',
            'heath': 'shrub',
            'scrubland': 'shrub',
            
            # Bare ground and desert
            'bare_rock': 'bare_ground',
            'sand': 'bare_ground',
            'scree': 'bare_ground',
            'quarry': 'bare_ground',
            'landfill': 'bare_ground',
            
            # Beach and coastal
            'beach': 'beach',
            'dune': 'beach',
            'coastline': 'beach',
            
            # Desert
            'desert': 'desert',
        }
        
        # Priority for overlapping features (higher priority wins)
        self.terrain_priority = {
            'water': 10,
            'urban': 9,
            'beach': 8,
            'desert': 7,
            'forest': 6,
            'agriculture': 5,
            'shrub': 4,
            'grass': 3,
            'bare_ground': 2,
            'unknown': 1
        }
        
        # Color scheme for visualization
        self.terrain_colors = {
            'forest': '#228B22',      # Forest green
            'grass': '#90EE90',       # Light green
            'urban': '#808080',       # Gray
            'water': '#4682B4',       # Steel blue
            'agriculture': '#DAA520',  # Goldenrod
            'shrub': '#9ACD32',       # Yellow green
            'bare_ground': '#D2B48C', # Tan
            'beach': '#F4A460',       # Sandy brown
            'desert': '#EDC9AF',      # Desert sand
            'unknown': '#DDD'         # Light gray
        }
        
        # Cell properties for fire simulation
        self.terrain_properties = {
            'forest': {
                'flammability': 0.8,
                'burn_rate': 0.7,
                'moisture_retention': 0.3,
                'wind_resistance': 0.2
            },
            'grass': {
                'flammability': 0.9,
                'burn_rate': 0.9,
                'moisture_retention': 0.1,
                'wind_resistance': 0.8
            },
            'shrub': {
                'flammability': 0.7,
                'burn_rate': 0.6,
                'moisture_retention': 0.2,
                'wind_resistance': 0.4
            },
            'agriculture': {
                'flammability': 0.6,
                'burn_rate': 0.5,
                'moisture_retention': 0.4,
                'wind_resistance': 0.6
            },
            'urban': {
                'flammability': 0.1,
                'burn_rate': 0.1,
                'moisture_retention': 0.9,
                'wind_resistance': 0.9
            },
            'water': {
                'flammability': 0.0,
                'burn_rate': 0.0,
                'moisture_retention': 1.0,
                'wind_resistance': 1.0
            },
            'bare_ground': {
                'flammability': 0.1,
                'burn_rate': 0.1,
                'moisture_retention': 0.1,
                'wind_resistance': 0.9
            },
            'beach': {
                'flammability': 0.1,
                'burn_rate': 0.1,
                'moisture_retention': 0.1,
                'wind_resistance': 0.9
            },
            'desert': {
                'flammability': 0.2,
                'burn_rate': 0.2,
                'moisture_retention': 0.0,
                'wind_resistance': 0.9
            },
            'unknown': {
                'flammability': 0.5,
                'burn_rate': 0.5,
                'moisture_retention': 0.5,
                'wind_resistance': 0.5
            }
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
    
    def tile_to_bbox(self, x: int, y: int, zoom: int) -> Tuple[float, float, float, float]:
        """Convert tile coordinates to bounding box (north, south, east, west)"""
        north, west = self.num2deg(x, y, zoom)
        south, east = self.num2deg(x + 1, y + 1, zoom)
        return (north, south, east, west)
    
    async def download_overpass_data(self, session: aiohttp.ClientSession, 
                                   bbox: Tuple[float, float, float, float]) -> Optional[Dict]:
        """Download OSM data using Overpass API for a bounding box"""
        north, south, east, west = bbox
        
        # Overpass query for landuse, natural, water, and building data
        overpass_query = f"""
        [out:json][timeout:25];
        (
          way["landuse"]({south},{west},{north},{east});
          way["natural"]({south},{west},{north},{east});
          way["water"]({south},{west},{north},{east});
          way["waterway"]({south},{west},{north},{east});
          way["building"]({south},{west},{north},{east});
          relation["landuse"]({south},{west},{north},{east});
          relation["natural"]({south},{west},{north},{east});
          relation["water"]({south},{west},{north},{east});
        );
        out geom;
        """
        
        try:
            url = "https://overpass-api.de/api/interpreter"
            async with session.post(url, data=overpass_query) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.warning(f"Overpass API request failed: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching Overpass data: {e}")
            return None
    
    def classify_osm_feature(self, feature: Dict) -> str:
        """Classify an OSM feature into our terrain types"""
        tags = feature.get('tags', {})
        
        # Check landuse first
        if 'landuse' in tags:
            landuse = tags['landuse']
            if landuse in self.osm_terrain_mapping:
                return self.osm_terrain_mapping[landuse]
        
        # Check natural features
        if 'natural' in tags:
            natural = tags['natural']
            if natural in self.osm_terrain_mapping:
                return self.osm_terrain_mapping[natural]
        
        # Check water features
        if 'water' in tags or 'waterway' in tags:
            return 'water'
        
        # Check buildings
        if 'building' in tags:
            return 'urban'
        
        return 'unknown'
    
    def point_in_polygon(self, point: Tuple[float, float], 
                        polygon_coords: List[List[float]]) -> bool:
        """Check if a point is inside a polygon using ray casting"""
        x, y = point
        n = len(polygon_coords)
        inside = False
        
        p1x, p1y = polygon_coords[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon_coords[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def classify_grid_cell_from_osm(self, osm_data: Dict, 
                                  cell_lat: float, cell_lon: float) -> str:
        """Classify a grid cell based on OSM data"""
        if not osm_data or 'elements' not in osm_data:
            return 'unknown'
        
        cell_point = (cell_lon, cell_lat)  # Note: lon, lat order for Point
        matching_features = []
        
        for element in osm_data['elements']:
            if element['type'] not in ['way', 'relation']:
                continue
            
            # Get geometry coordinates
            if 'geometry' in element:
                coords = []
                for node in element['geometry']:
                    coords.append([node['lon'], node['lat']])
                
                # Check if point is inside this polygon
                if len(coords) >= 3 and self.point_in_polygon(cell_point, coords):
                    terrain_type = self.classify_osm_feature(element)
                    priority = self.terrain_priority.get(terrain_type, 0)
                    matching_features.append((terrain_type, priority))
        
        # Return the highest priority terrain type
        if matching_features:
            matching_features.sort(key=lambda x: x[1], reverse=True)
            return matching_features[0][0]
        
        return 'unknown'
    
    async def classify_grid_area(self, lat: float, lon: float, 
                               grid_size: int = 50,
                               cell_size_degrees: float = 0.001) -> List[List[Dict]]:
        """Classify terrain for an entire grid area using OSM vector data"""
        
        logger.info(f"Starting OSM vector tile classification for {grid_size}x{grid_size} grid at {lat}, {lon}")
        
        # Calculate the area bounds
        half_size = grid_size * cell_size_degrees / 2
        north = lat + half_size
        south = lat - half_size
        east = lon + half_size
        west = lon - half_size
        
        bbox = (north, south, east, west)
        
        # Download OSM data for the area
        async with aiohttp.ClientSession() as session:
            osm_data = await self.download_overpass_data(session, bbox)
        
        if not osm_data:
            logger.warning("No OSM data downloaded, using fallback classification")
            return self._generate_fallback_grid(lat, lon, grid_size, cell_size_degrees)
        
        logger.info(f"Downloaded {len(osm_data.get('elements', []))} OSM features")
        
        # Classify each grid cell
        grid_classification = []
        
        for row in range(grid_size):
            grid_row = []
            for col in range(grid_size):
                # Calculate cell center coordinates
                cell_lat = lat - (grid_size * cell_size_degrees / 2) + (row + 0.5) * cell_size_degrees
                cell_lon = lon - (grid_size * cell_size_degrees / 2) + (col + 0.5) * cell_size_degrees
                
                # Classify the cell using OSM data
                terrain_type = self.classify_grid_cell_from_osm(osm_data, cell_lat, cell_lon)
                
                # Get terrain properties
                properties = self.terrain_properties.get(terrain_type, self.terrain_properties['unknown'])
                
                cell_data = {
                    'terrain_type': terrain_type,
                    'color': self.terrain_colors[terrain_type],
                    'row': row,
                    'col': col,
                    'lat': cell_lat,
                    'lon': cell_lon,
                    'properties': properties,
                    'burn_state': 'unburned',  # Initial state
                    'burn_intensity': 0.0,
                    'moisture': properties['moisture_retention']
                }
                
                grid_row.append(cell_data)
            
            grid_classification.append(grid_row)
            
            # Log progress
            if (row + 1) % 10 == 0:
                logger.info(f"Classified {row + 1}/{grid_size} rows")
        
        logger.info(f"OSM grid classification completed")
        return grid_classification
    
    def _generate_fallback_grid(self, lat: float, lon: float, 
                              grid_size: int, cell_size_degrees: float) -> List[List[Dict]]:
        """Generate a fallback grid with basic terrain distribution"""
        
        logger.info("Generating fallback terrain grid with geographic patterns")
        
        grid = []
        center_row = grid_size // 2
        center_col = grid_size // 2
        
        for row in range(grid_size):
            grid_row = []
            for col in range(grid_size):
                # Calculate cell coordinates
                cell_lat = lat - (grid_size * cell_size_degrees / 2) + (row + 0.5) * cell_size_degrees
                cell_lon = lon - (grid_size * cell_size_degrees / 2) + (col + 0.5) * cell_size_degrees
                
                # Distance from center
                dist_from_center = math.sqrt((row - center_row)**2 + (col - center_col)**2)
                normalized_dist = dist_from_center / (grid_size / 2)
                
                # Use some geographic patterns and randomness
                rand = np.random.random()
                edge_factor = min(1.0, normalized_dist)
                
                # Determine terrain type with geographic logic
                if rand < 0.08:  # Water features (rivers, lakes)
                    terrain_type = 'water'
                elif edge_factor < 0.3 and rand < 0.2:  # Urban areas near center
                    terrain_type = 'urban'
                elif rand < 0.35:  # Forest areas
                    terrain_type = 'forest'
                elif rand < 0.55:  # Agricultural areas
                    terrain_type = 'agriculture'
                elif rand < 0.75:  # Grassland
                    terrain_type = 'grass'
                elif rand < 0.85:  # Shrubland
                    terrain_type = 'shrub'
                else:  # Bare ground
                    terrain_type = 'bare_ground'
                
                # Get terrain properties
                properties = self.terrain_properties.get(terrain_type, self.terrain_properties['unknown'])
                
                cell_data = {
                    'terrain_type': terrain_type,
                    'color': self.terrain_colors[terrain_type],
                    'row': row,
                    'col': col,
                    'lat': cell_lat,
                    'lon': cell_lon,
                    'properties': properties,
                    'burn_state': 'unburned',
                    'burn_intensity': 0.0,
                    'moisture': properties['moisture_retention']
                }
                
                grid_row.append(cell_data)
            grid.append(grid_row)
        
        return grid
    
    def get_terrain_statistics(self, grid: List[List[Dict]]) -> Dict[str, int]:
        """Calculate terrain type statistics for the grid"""
        stats = {}
        for row in grid:
            for cell in row:
                terrain = cell['terrain_type']
                stats[terrain] = stats.get(terrain, 0) + 1
        return stats
