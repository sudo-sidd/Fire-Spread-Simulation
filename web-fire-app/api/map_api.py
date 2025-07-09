"""
Map API endpoints
Handles map selection and location services
"""

from flask import Blueprint, request, jsonify
from services.terrain_service import TerrainExtractor
from services.visualization_service import VisualizationService
import numpy as np

map_bp = Blueprint('map', __name__)

@map_bp.route('/select-area', methods=['POST'])
def select_area():
    """Handle map area selection from coordinates"""
    try:
        data = request.get_json()
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        zoom = int(data.get('zoom', 15))
        grid_size = data.get('grid_size', [200, 200])
        
        print(f"Extracting terrain for lat={lat}, lon={lon}, grid_size={grid_size}")
        
        # Extract terrain data
        terrain_extractor = TerrainExtractor()
        terrain_bitmap, color_map, metadata = terrain_extractor.create_terrain_bitmap(
            lat, lon, tuple(grid_size)
        )
        
        print(f"Terrain bitmap shape: {terrain_bitmap.shape}")
        print(f"Terrain bitmap dtype: {terrain_bitmap.dtype}")
        print(f"Color map keys: {list(color_map.keys())}")
        
        # Convert to base64 for client
        viz_service = VisualizationService()
        terrain_b64 = viz_service.image_to_base64(terrain_bitmap)
        
        print(f"Base64 string length: {len(terrain_b64)}")
        print(f"Base64 prefix: {terrain_b64[:50]}...")
        
        return jsonify({
            'success': True,
            'terrain_image': terrain_b64,
            'color_map': {str(k): v for k, v in color_map.items()},
            'metadata': metadata,
            'message': f'Terrain extracted for coordinates ({lat:.4f}, {lon:.4f})'
        })
        
    except Exception as e:
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
