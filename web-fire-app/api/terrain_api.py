"""
Terrain API endpoints
Handles terrain extraction and processing
"""

from flask import Blueprint, request, jsonify, send_file
from services.terrain_service import TerrainExtractor
from services.map_tile_service import MapTileClassifier
from services.visualization_service import VisualizationService
from core.config import Config
import os
import tempfile
import uuid
import asyncio
import logging

logger = logging.getLogger(__name__)

terrain_bp = Blueprint('terrain', __name__)

@terrain_bp.route('/extract', methods=['POST'])
def extract_terrain():
    """Extract terrain data from coordinates"""
    try:
        data = request.get_json()
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        zoom = int(data.get('zoom', 15))
        size = data.get('size', [Config.GRID_SIZE, Config.GRID_SIZE])
        
        extractor = TerrainExtractor()
        terrain_bitmap, color_map, metadata = extractor.create_terrain_bitmap(
            lat, lon, tuple(size)
        )
        
        # Convert to base64 for response
        viz_service = VisualizationService()
        terrain_b64 = viz_service.image_to_base64(terrain_bitmap)
        
        return jsonify({
            'success': True,
            'terrain_bitmap': terrain_b64,
            'color_map': {str(k): v for k, v in color_map.items()},
            'metadata': metadata,
            'statistics': {
                'total_pixels': terrain_bitmap.shape[0] * terrain_bitmap.shape[1],
                'terrain_types': list(Config.TERRAIN_TYPES.keys())
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to extract terrain'
        }), 500

@terrain_bp.route('/analyze', methods=['POST'])
def analyze_terrain():
    """Analyze terrain composition and fire risk"""
    try:
        data = request.get_json()
        terrain_data = data.get('terrain_bitmap')
        
        if not terrain_data:
            return jsonify({'error': 'Terrain data required'}), 400
        
        # Convert base64 back to array for analysis
        import base64
        import numpy as np
        from PIL import Image
        import io
        
        # Decode base64 image
        img_data = base64.b64decode(terrain_data.split(',')[1])
        img = Image.open(io.BytesIO(img_data))
        terrain_array = np.array(img)
        
        # Analyze terrain composition
        analysis = _analyze_terrain_composition(terrain_array)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terrain_bp.route('/download/<terrain_id>', methods=['GET'])
def download_terrain(terrain_id):
    """Download terrain bitmap as image file"""
    try:
        # In production, retrieve terrain data from database
        # For demo, return error
        return jsonify({
            'error': 'Terrain download not implemented in demo'
        }), 501
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terrain_bp.route('/presets', methods=['GET'])
def get_terrain_presets():
    """Get predefined terrain configurations"""
    try:
        presets = {
            'forest_dense': {
                'name': 'Dense Forest',
                'description': 'High fire risk forested area',
                'terrain_distribution': {
                    'forest': 0.7,
                    'grass': 0.2,
                    'water': 0.05,
                    'bare_ground': 0.05
                },
                'fire_risk': 'high'
            },
            'grassland': {
                'name': 'Open Grassland',
                'description': 'Grassland with scattered trees',
                'terrain_distribution': {
                    'grass': 0.8,
                    'shrub': 0.15,
                    'water': 0.03,
                    'bare_ground': 0.02
                },
                'fire_risk': 'medium'
            },
            'mixed_rural': {
                'name': 'Rural Mixed',
                'description': 'Mixed rural landscape',
                'terrain_distribution': {
                    'agriculture': 0.4,
                    'grass': 0.3,
                    'forest': 0.2,
                    'urban': 0.05,
                    'water': 0.05
                },
                'fire_risk': 'medium'
            },
            'urban_interface': {
                'name': 'Urban-Wildland Interface',
                'description': 'Urban area adjacent to wildland',
                'terrain_distribution': {
                    'urban': 0.4,
                    'grass': 0.3,
                    'forest': 0.2,
                    'bare_ground': 0.1
                },
                'fire_risk': 'high'
            }
        }
        
        return jsonify({
            'success': True,
            'presets': presets
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terrain_bp.route('/classify-grid', methods=['POST'])
def classify_grid():
    """Classify terrain for a grid using real map tile imagery"""
    try:
        data = request.get_json()
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        grid_size = int(data.get('grid_size', Config.GRID_SIZE))
        cell_size = float(data.get('cell_size_degrees', 0.001))
        
        logger.info(f"Classifying grid at {lat}, {lon} with size {grid_size}")
        
        # Create classifier and run async classification
        classifier = MapTileClassifier()
        
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            grid_classification = loop.run_until_complete(
                classifier.classify_grid_area(lat, lon, grid_size, cell_size)
            )
        finally:
            loop.close()
        
        # Calculate statistics
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
        
        return jsonify({
            'success': True,
            'grid_classification': grid_classification,
            'legend_colors': classifier.legend_colors,
            'statistics': {
                'total_cells': total_cells,
                'terrain_counts': terrain_counts,
                'terrain_percentages': terrain_percentages,
                'grid_size': grid_size
            },
            'metadata': {
                'center_lat': lat,
                'center_lon': lon,
                'cell_size_degrees': cell_size,
                'classification_method': 'map_tiles'
            }
        })
        
    except Exception as e:
        logger.error(f"Error in grid classification: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to classify grid terrain'
        }), 500

def _analyze_terrain_composition(terrain_array):
    """Analyze terrain composition and calculate fire risk metrics"""
    
    import numpy as np
    from core.config import Config
    
    height, width = terrain_array.shape[:2]
    total_pixels = height * width
    
    # Count terrain types by color
    terrain_counts = {}
    fire_risk_score = 0.0
    
    for terrain_type, props in Config.TERRAIN_TYPES.items():
        color = props['color']
        # Find pixels matching this terrain type (with some tolerance)
        mask = np.all(np.abs(terrain_array[:, :, :3] - color) < 30, axis=2)
        count = np.sum(mask)
        percentage = (count / total_pixels) * 100
        
        terrain_counts[terrain_type] = {
            'pixel_count': int(count),
            'percentage': round(percentage, 2)
        }
        
        # Calculate fire risk contribution
        fuel_load = props['fuel_load']
        spread_rate = props['spread_rate']
        fire_risk_score += (percentage / 100) * fuel_load * spread_rate
    
    # Overall fire risk assessment
    if fire_risk_score > 0.6:
        risk_level = 'high'
    elif fire_risk_score > 0.3:
        risk_level = 'medium'
    else:
        risk_level = 'low'
    
    # Calculate connectivity metrics
    flammable_types = ['forest', 'grass', 'shrub', 'agriculture']
    flammable_pixels = 0
    for terrain_type in flammable_types:
        if terrain_type in terrain_counts:
            flammable_pixels += terrain_counts[terrain_type]['pixel_count']
    
    flammable_percentage = (flammable_pixels / total_pixels) * 100
    
    return {
        'terrain_composition': terrain_counts,
        'fire_risk': {
            'score': round(fire_risk_score, 3),
            'level': risk_level,
            'flammable_percentage': round(flammable_percentage, 2)
        },
        'recommendations': _generate_fire_risk_recommendations(terrain_counts, fire_risk_score),
        'total_area_km2': total_pixels * 0.000025  # Assuming 25m² per pixel
    }

def _generate_fire_risk_recommendations(terrain_counts, fire_risk_score):
    """Generate fire risk management recommendations"""
    
    recommendations = []
    
    # High vegetation areas
    forest_pct = terrain_counts.get('forest', {}).get('percentage', 0)
    grass_pct = terrain_counts.get('grass', {}).get('percentage', 0)
    
    if forest_pct > 50:
        recommendations.append("Consider fuel reduction treatments in dense forest areas")
    
    if grass_pct > 40:
        recommendations.append("Maintain firebreaks in grassland areas during dry seasons")
    
    # Water availability
    water_pct = terrain_counts.get('water', {}).get('percentage', 0)
    if water_pct < 5:
        recommendations.append("Limited water sources - enhance water access for firefighting")
    
    # Urban interface
    urban_pct = terrain_counts.get('urban', {}).get('percentage', 0)
    if urban_pct > 20 and fire_risk_score > 0.4:
        recommendations.append("High wildland-urban interface risk - create defensible space")
    
    if fire_risk_score > 0.6:
        recommendations.append("High overall fire risk - implement comprehensive fire management plan")
    
    return recommendations
