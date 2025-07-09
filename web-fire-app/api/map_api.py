"""
Map API endpoints
Handles map selection and location services
"""

from flask import Blueprint, request, jsonify
from services.terrain_service import TerrainExtractor
from services.visualization_service import VisualizationService
import numpy as np
import logging

logger = logging.getLogger(__name__)

map_bp = Blueprint('map', __name__)

@map_bp.route('/select-area', methods=['POST'])
def select_area():
    """Handle map area selection from coordinates"""
    try:
        logger.info("=== MAP SELECT AREA ENDPOINT CALLED ===")
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        zoom = int(data.get('zoom', 15))
        grid_size = data.get('grid_size', [50, 50])  # Default to 50x50 grid
        
        # Convert grid_size to single integer if it's a list
        if isinstance(grid_size, list):
            grid_size = grid_size[0]  # Assume square grid
        
        cell_size_degrees = 0.001  # Approximately 100m at equator
        
        logger.info(f"Creating 2D grid for lat={lat}, lon={lon}, grid_size={grid_size}")
        
        # Import here to avoid circular imports
        from services.map_tile_service import MapTileClassifier
        import asyncio
        
        # Create classifier and run async classification to get 2D cell grid
        logger.info("Creating MapTileClassifier...")
        classifier = MapTileClassifier()
        
        # Run the async function in a new event loop
        logger.info("Starting async grid classification...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            logger.info("Running classify_grid_area...")
            grid_classification = loop.run_until_complete(
                classifier.classify_grid_area(lat, lon, grid_size, cell_size_degrees)
            )
            logger.info(f"Grid classification completed. Grid size: {len(grid_classification)}x{len(grid_classification[0])}")
        finally:
            loop.close()
            logger.info("Event loop closed")
        
        # Calculate grid bounds
        half_lat = (cell_size_degrees * grid_size) / 2
        half_lon = (cell_size_degrees * grid_size) / 2
        
        grid_bounds = {
            'north': lat + half_lat,
            'south': lat - half_lat,
            'east': lon + half_lon,
            'west': lon - half_lon
        }
        
        # Calculate statistics
        logger.info("Calculating statistics...")
        terrain_counts = {}
        total_cells = grid_size * grid_size
        
        for row in grid_classification:
            for cell in row:
                terrain_type = cell['terrain_type']
                terrain_counts[terrain_type] = terrain_counts.get(terrain_type, 0) + 1
        
        # Convert to percentages
        terrain_percentages = {
            terrain: (count / total_cells) * 100 
            for terrain, count in terrain_counts.items()
        }
        
        logger.info(f"Statistics calculated. Terrain counts: {terrain_counts}")
        
        response_data = {
            'success': True,
            'grid_classification': grid_classification,
            'legend_colors': classifier.legend_colors,
            'grid_bounds': grid_bounds,
            'statistics': {
                'total_cells': total_cells,
                'terrain_counts': terrain_counts,
                'terrain_percentages': terrain_percentages,
                'grid_size': grid_size
            },
            'metadata': {
                'center_lat': lat,
                'center_lon': lon,
                'cell_size_degrees': cell_size_degrees,
                'classification_method': 'map_tiles_grid',
                'grid_type': '2d_cell_sheet'
            },
            'message': f'2D Grid created for coordinates ({lat:.4f}, {lon:.4f})'
        }
        
        logger.info("=== MAP SELECT AREA ENDPOINT RETURNING SUCCESS ===")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in map select area: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to extract terrain data'
        }), 500

@map_bp.route('/geocode', methods=['GET'])
def geocode():
    """Convert address to coordinates"""
    try:
        address = request.args.get('address')
        if not address:
            return jsonify({'error': 'Address parameter required'}), 400
        
        # Simple geocoding (in production, use proper geocoding service)
        # For demo, return some sample coordinates
        sample_locations = {
            'california': {'lat': 36.7783, 'lon': -119.4179},
            'australia': {'lat': -25.2744, 'lon': 133.7751},
            'portugal': {'lat': 39.3999, 'lon': -8.2245},
            'greece': {'lat': 39.0742, 'lon': 21.8243},
            'canada': {'lat': 56.1304, 'lon': -106.3468}
        }
        
        # Simple matching
        address_lower = address.lower()
        for key, coords in sample_locations.items():
            if key in address_lower:
                return jsonify({
                    'success': True,
                    'coordinates': coords,
                    'address': address
                })
        
        # Default location if no match
        return jsonify({
            'success': True,
            'coordinates': {'lat': 39.8283, 'lon': -98.5795},
            'address': address,
            'message': 'Using default location'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@map_bp.route('/nearby-features', methods=['GET'])
def nearby_features():
    """Get nearby geographic features for a location"""
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        
        # Simulate nearby features (in production, use real geographic database)
        features = {
            'water_bodies': [
                {'name': 'Lake Example', 'distance_km': 2.5, 'type': 'lake'},
                {'name': 'River Valley', 'distance_km': 1.2, 'type': 'river'}
            ],
            'urban_areas': [
                {'name': 'Sample City', 'distance_km': 5.8, 'population': 25000}
            ],
            'protected_areas': [
                {'name': 'Nature Reserve', 'distance_km': 8.3, 'type': 'forest'}
            ],
            'elevation': 245,  # meters
            'climate_zone': 'temperate'
        }
        
        return jsonify({
            'success': True,
            'location': {'lat': lat, 'lon': lon},
            'features': features
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
