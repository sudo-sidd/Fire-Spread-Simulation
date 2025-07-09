"""
Simulation API endpoints
Handles fire simulation operations
"""

from flask import Blueprint, request, jsonify, session
from core.fire_engine import FireSimulation, WeatherConditions
from services.visualization_service import VisualizationService
from services.terrain_service import TerrainExtractor
from core.config import Config
import numpy as np
import uuid
import json
import time
from flask import current_app

simulation_bp = Blueprint('simulation', __name__)

# In-memory storage for active simulations (in production, use Redis or database)
active_simulations = {}

@simulation_bp.route('/create', methods=['POST'])
def create_simulation():
    """Create a new fire simulation"""
    try:
        data = request.get_json()
        
        # Simulation parameters
        width = data.get('width', Config.GRID_SIZE)
        height = data.get('height', Config.GRID_SIZE)
        terrain_data = data.get('terrain_data')
        
        # Create simulation
        simulation = FireSimulation(width, height)
        
        # Set terrain if provided
        if terrain_data:
            # Handle terrain bitmap - it might be base64 string or array
            terrain_bitmap_data = terrain_data['bitmap']
            
            if isinstance(terrain_bitmap_data, str):
                # Convert from base64 to numpy array
                import base64
                import io
                from PIL import Image
                
                # Remove data URL prefix if present
                if ',' in terrain_bitmap_data:
                    terrain_bitmap_data = terrain_bitmap_data.split(',')[1]
                
                # Decode base64 to image
                img_data = base64.b64decode(terrain_bitmap_data)
                img = Image.open(io.BytesIO(img_data))
                terrain_bitmap = np.array(img)
            else:
                # Already an array
                terrain_bitmap = np.array(terrain_bitmap_data)
            
            # Process color map
            color_map = {}
            for k, v in terrain_data['color_map'].items():
                if isinstance(k, str) and k.startswith('(') and k.endswith(')'):
                    # Parse string representation of tuple: "(255, 0, 0)"
                    color_values = k.strip('()').split(', ')
                    color_tuple = tuple(int(val) for val in color_values)
                    color_map[color_tuple] = v
                else:
                    # Already a proper key
                    color_map[k] = v
            
            simulation.set_terrain_from_bitmap(terrain_bitmap, color_map)
        
        # Generate unique simulation ID
        sim_id = str(uuid.uuid4())
        active_simulations[sim_id] = {
            'simulation': simulation,
            'visualization': VisualizationService(),
            'created_at': np.datetime64('now'),
            'step_history': []
        }
        
        return jsonify({
            'success': True,
            'simulation_id': sim_id,
            'grid_size': {'width': width, 'height': height},
            'message': 'Simulation created successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to create simulation'
        }), 500

@simulation_bp.route('/ignite', methods=['POST'])
def ignite_fire():
    """Start a fire at specified coordinates"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        x = int(data.get('x'))
        y = int(data.get('y'))
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        simulation = active_simulations[sim_id]['simulation']
        success = simulation.ignite_at(x, y)
        
        if success:
            # Get current visualization
            viz_service = active_simulations[sim_id]['visualization']
            fire_overlay = viz_service.create_fire_overlay(simulation)
            terrain_image = simulation.get_terrain_state_array()
            composite = viz_service.create_composite_image(terrain_image, fire_overlay)
            
            # Convert to base64
            composite_b64 = viz_service.image_to_base64(composite)
            
            return jsonify({
                'success': True,
                'message': f'Fire ignited at ({x}, {y})',
                'visualization': composite_b64,
                'statistics': {
                    'burning_cells': simulation.burning_cells,
                    'burned_cells': simulation.burned_cells,
                    'step': simulation.step_count
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Could not ignite fire at specified location'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@simulation_bp.route('/random-ignite', methods=['POST'])
def random_ignite():
    """Start fires randomly across flammable areas"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        num_ignitions = data.get('num_ignitions')  # Optional: specific number of fires
        ignition_probability = data.get('ignition_probability', 0.05)  # Default 5% chance per cell
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        simulation = active_simulations[sim_id]['simulation']
        
        # Get count of flammable cells before ignition
        flammable_count = simulation.get_flammable_cell_count()
        
        if flammable_count == 0:
            return jsonify({
                'success': False,
                'message': 'No flammable areas available for ignition'
            }), 400
        
        # Perform random ignition
        ignited_count = simulation.random_ignite(num_ignitions, ignition_probability)
        
        if ignited_count > 0:
            # Get current visualization
            viz_service = active_simulations[sim_id]['visualization']
            fire_overlay = viz_service.create_fire_overlay(simulation)
            terrain_image = simulation.get_terrain_state_array()
            composite = viz_service.create_composite_image(terrain_image, fire_overlay)
            
            # Convert to base64
            composite_b64 = viz_service.image_to_base64(composite)
            
            return jsonify({
                'success': True,
                'message': f'Successfully ignited {ignited_count} fires randomly',
                'ignited_count': ignited_count,
                'flammable_cells': flammable_count,
                'visualization': composite_b64,
                'statistics': {
                    'burning_cells': simulation.burning_cells,
                    'burned_cells': simulation.burned_cells,
                    'step': simulation.step_count
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to ignite any fires'
            }), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@simulation_bp.route('/step', methods=['POST'])
def step_simulation():
    """Advance simulation by one or more steps"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        steps = data.get('steps', 1)
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim_data = active_simulations[sim_id]
        simulation = sim_data['simulation']
        viz_service = sim_data['visualization']
        
        # Run simulation steps
        step_results = []
        for _ in range(steps):
            if simulation.is_active():
                result = simulation.step()
                step_results.append(result)
                sim_data['step_history'].append(result)
            else:
                break
        
        # Generate visualization
        fire_overlay = viz_service.create_fire_overlay(simulation)
        terrain_image = simulation.get_terrain_state_array()
        composite = viz_service.create_composite_image(terrain_image, fire_overlay)
        
        # Add effects if there are active fires
        if simulation.burning_cells > 0:
            composite = viz_service.add_fire_effects(composite, simulation)
        
        composite_b64 = viz_service.image_to_base64(composite)
        
        return jsonify({
            'success': True,
            'steps_executed': len(step_results),
            'visualization': composite_b64,
            'statistics': {
                'burning_cells': simulation.burning_cells,
                'burned_cells': simulation.burned_cells,
                'total_burned_area_km2': simulation.total_burned_area,
                'step': simulation.step_count,
                'is_active': simulation.is_active()
            },
            'step_results': step_results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@simulation_bp.route('/weather', methods=['POST'])
def set_weather():
    """Update weather conditions for simulation"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        simulation = active_simulations[sim_id]['simulation']
        
        # Update weather
        weather = WeatherConditions(
            wind_speed=data.get('wind_speed', 5.0),
            wind_direction=data.get('wind_direction', 0.0),
            humidity=data.get('humidity', 50.0),
            temperature=data.get('temperature', 25.0),
            precipitation=data.get('precipitation', 0.0)
        )
        
        simulation.set_weather(weather)
        
        return jsonify({
            'success': True,
            'message': 'Weather conditions updated',
            'weather': {
                'wind_speed': weather.wind_speed,
                'wind_direction': weather.wind_direction,
                'humidity': weather.humidity,
                'temperature': weather.temperature,
                'precipitation': weather.precipitation
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@simulation_bp.route('/reset', methods=['POST'])
def reset_simulation():
    """Reset simulation to initial state"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        simulation = active_simulations[sim_id]['simulation']
        simulation.reset()
        
        # Clear history
        active_simulations[sim_id]['step_history'] = []
        
        # Generate fresh visualization
        viz_service = active_simulations[sim_id]['visualization']
        terrain_image = simulation.get_terrain_state_array()
        terrain_b64 = viz_service.image_to_base64(terrain_image)
        
        return jsonify({
            'success': True,
            'message': 'Simulation reset successfully',
            'visualization': terrain_b64,
            'statistics': {
                'burning_cells': 0,
                'burned_cells': 0,
                'total_burned_area_km2': 0,
                'step': 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@simulation_bp.route('/status/<sim_id>', methods=['GET'])
def get_simulation_status(sim_id):
    """Get current status of a simulation"""
    try:
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim_data = active_simulations[sim_id]
        simulation = sim_data['simulation']
        
        return jsonify({
            'success': True,
            'simulation_id': sim_id,
            'statistics': {
                'burning_cells': simulation.burning_cells,
                'burned_cells': simulation.burned_cells,
                'total_burned_area_km2': simulation.total_burned_area,
                'step': simulation.step_count,
                'is_active': simulation.is_active(),
                'grid_size': {'width': simulation.width, 'height': simulation.height}
            },
            'history_length': len(sim_data['step_history'])
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@simulation_bp.route('/export/<sim_id>', methods=['GET'])
def export_simulation_data(sim_id):
    """Export simulation data and history"""
    try:
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim_data = active_simulations[sim_id]
        simulation = sim_data['simulation']
        
        export_data = {
            'simulation_id': sim_id,
            'grid_size': {'width': simulation.width, 'height': simulation.height},
            'current_step': simulation.step_count,
            'statistics': {
                'burning_cells': simulation.burning_cells,
                'burned_cells': simulation.burned_cells,
                'total_burned_area_km2': simulation.total_burned_area
            },
            'step_history': sim_data['step_history'],
            'terrain_data': simulation.get_terrain_state_array().tolist(),
            'fire_state': simulation.get_fire_state_array().tolist()
        }
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@simulation_bp.route('/<simulation_id>/state', methods=['GET'])
def get_simulation_state(simulation_id):
    """Get current state of the simulation including fire states"""
    try:
        if simulation_id not in active_simulations:
            return jsonify({
                'success': False,
                'error': 'Simulation not found'
            }), 404
        
        simulation = active_simulations[simulation_id]
        fire_engine = simulation['fire_engine']
        
        # Get current fire states from the fire engine
        fire_states = fire_engine.get_all_fire_states()
        
        return jsonify({
            'success': True,
            'fire_states': fire_states,
            'metadata': {
                'simulation_id': simulation_id,
                'timestamp': time.time(),
                'step': simulation.get('step', 0)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting simulation state: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
