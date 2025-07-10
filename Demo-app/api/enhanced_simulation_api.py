"""
Enhanced Simulation API endpoints
Handles fire simulation operations using the new cellular automaton engine
"""

from flask import Blueprint, request, jsonify
from core.cellular_automata_engine import CellularAutomatonEngine, EnvironmentalConditions, WindDirection
from services.visualization_service import VisualizationService
import numpy as np
import uuid
import json
import time
import logging

logger = logging.getLogger(__name__)

enhanced_simulation_bp = Blueprint('enhanced_simulation', __name__)

# In-memory storage for active simulations (in production, use Redis or database)
active_simulations = {}

@enhanced_simulation_bp.route('/create', methods=['POST'])
def create_simulation():
    """Create a new enhanced fire simulation from terrain grid"""
    try:
        data = request.get_json()
        logger.info(f"Creating simulation with data keys: {list(data.keys())}")
        
        # Extract terrain grid data
        grid_classification = data.get('grid_classification')
        grid_size = data.get('grid_size', 50)
        
        if not grid_classification:
            return jsonify({
                'success': False,
                'error': 'grid_classification required',
                'message': 'Terrain grid data is required to create simulation'
            }), 400
        
        # Create cellular automaton engine
        engine = CellularAutomatonEngine(grid_size=grid_size)
        engine.initialize_from_terrain_grid(grid_classification)
        
        # Set initial environmental conditions
        env_conditions = data.get('environmental_conditions', {})
        if env_conditions:
            engine.set_environmental_conditions(env_conditions)
        
        # Generate unique simulation ID
        sim_id = str(uuid.uuid4())
        
        # Store simulation
        active_simulations[sim_id] = {
            'engine': engine,
            'visualization': VisualizationService(),
            'created_at': time.time(),
            'step_history': [],
            'grid_classification': grid_classification,
            'metadata': {
                'grid_size': grid_size,
                'center_lat': data.get('center_lat', 0),
                'center_lon': data.get('center_lon', 0),
                'cell_size_degrees': data.get('cell_size_degrees', 0.001)
            }
        }
        
        # Get initial statistics
        initial_stats = engine._calculate_statistics()
        
        logger.info(f"Created simulation {sim_id} with {grid_size}x{grid_size} grid")
        
        return jsonify({
            'success': True,
            'simulation_id': sim_id,
            'grid_size': grid_size,
            'initial_statistics': initial_stats,
            'environmental_conditions': {
                'temperature': engine.conditions.temperature,
                'humidity': engine.conditions.humidity,
                'wind_speed': engine.conditions.wind_speed,
                'wind_direction': engine.conditions.wind_direction.name.lower()
            },
            'message': 'Enhanced fire simulation created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating simulation: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to create simulation'
        }), 500

@enhanced_simulation_bp.route('/ignite', methods=['POST'])
def ignite_fire():
    """Start a fire at specified grid coordinates"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        row = int(data.get('row'))
        col = int(data.get('col'))
        intensity = float(data.get('intensity', 1.0))
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        engine = active_simulations[sim_id]['engine']
        success = engine.ignite_cell(row, col, intensity)
        
        if success:
            # Get current grid state
            grid_state = engine.get_grid_state()
            statistics = engine._calculate_statistics()
            
            logger.info(f"Fire ignited at ({row}, {col}) in simulation {sim_id}")
            
            return jsonify({
                'success': True,
                'message': f'Fire ignited at grid cell ({row}, {col})',
                'grid_state': grid_state,
                'statistics': statistics,
                'ignition_point': {'row': row, 'col': col, 'intensity': intensity}
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Could not ignite fire at grid cell ({row}, {col}). Cell may already be burned or unsuitable for ignition.'
            }), 400
            
    except Exception as e:
        logger.error(f"Error igniting fire: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_simulation_bp.route('/step', methods=['POST'])
def step_simulation():
    """Advance simulation by one or more steps"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        steps = int(data.get('steps', 1))
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        engine = active_simulations[sim_id]['engine']
        step_results = []
        
        # Execute simulation steps
        for i in range(steps):
            step_result = engine.step()
            step_results.append(step_result)
            
            # Stop if no more active fires
            if not step_result['is_active']:
                logger.info(f"Simulation {sim_id} completed at step {step_result['tick']}")
                break
        
        # Store step history
        active_simulations[sim_id]['step_history'].extend(step_results)
        
        # Get current grid state
        grid_state = engine.get_grid_state()
        current_stats = step_results[-1]['statistics'] if step_results else engine._calculate_statistics()
        
        return jsonify({
            'success': True,
            'steps_executed': len(step_results),
            'current_tick': engine.tick_count,
            'grid_state': grid_state,
            'statistics': current_stats,
            'step_results': step_results,
            'is_active': step_results[-1]['is_active'] if step_results else False,
            'message': f'Simulation advanced by {len(step_results)} steps'
        })
        
    except Exception as e:
        logger.error(f"Error stepping simulation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_simulation_bp.route('/update-conditions', methods=['POST'])
def update_environmental_conditions():
    """Update environmental conditions for the simulation"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        conditions = data.get('conditions', {})
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        engine = active_simulations[sim_id]['engine']
        engine.set_environmental_conditions(conditions)
        
        return jsonify({
            'success': True,
            'updated_conditions': {
                'temperature': engine.conditions.temperature,
                'humidity': engine.conditions.humidity,
                'wind_speed': engine.conditions.wind_speed,
                'wind_direction': engine.conditions.wind_direction.name.lower(),
                'rain_probability': engine.conditions.rain_probability
            },
            'message': 'Environmental conditions updated'
        })
        
    except Exception as e:
        logger.error(f"Error updating conditions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_simulation_bp.route('/reset', methods=['POST'])
def reset_simulation():
    """Reset the simulation to initial state"""
    try:
        data = request.get_json()
        sim_id = data.get('simulation_id')
        
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        engine = active_simulations[sim_id]['engine']
        engine.reset()
        
        # Clear step history
        active_simulations[sim_id]['step_history'] = []
        
        # Get reset grid state
        grid_state = engine.get_grid_state()
        statistics = engine._calculate_statistics()
        
        logger.info(f"Reset simulation {sim_id}")
        
        return jsonify({
            'success': True,
            'grid_state': grid_state,
            'statistics': statistics,
            'message': 'Simulation reset to initial state'
        })
        
    except Exception as e:
        logger.error(f"Error resetting simulation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_simulation_bp.route('/status/<sim_id>', methods=['GET'])
def get_simulation_status(sim_id):
    """Get current simulation status"""
    try:
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim_data = active_simulations[sim_id]
        engine = sim_data['engine']
        
        # Get current state
        grid_state = engine.get_grid_state()
        statistics = engine._calculate_statistics()
        
        # Calculate runtime
        runtime = time.time() - sim_data['created_at']
        
        return jsonify({
            'success': True,
            'simulation_id': sim_id,
            'current_tick': engine.tick_count,
            'grid_state': grid_state,
            'statistics': statistics,
            'environmental_conditions': {
                'temperature': engine.conditions.temperature,
                'humidity': engine.conditions.humidity,
                'wind_speed': engine.conditions.wind_speed,
                'wind_direction': engine.conditions.wind_direction.name.lower(),
                'rain_probability': engine.conditions.rain_probability
            },
            'metadata': sim_data['metadata'],
            'runtime_seconds': runtime,
            'step_count': len(sim_data['step_history']),
            'is_active': statistics['burning'] > 0
        })
        
    except Exception as e:
        logger.error(f"Error getting simulation status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_simulation_bp.route('/list', methods=['GET'])
def list_simulations():
    """List all active simulations"""
    try:
        simulations = []
        for sim_id, sim_data in active_simulations.items():
            engine = sim_data['engine']
            stats = engine._calculate_statistics()
            
            simulations.append({
                'simulation_id': sim_id,
                'created_at': sim_data['created_at'],
                'current_tick': engine.tick_count,
                'grid_size': sim_data['metadata']['grid_size'],
                'is_active': stats['burning'] > 0,
                'total_burned': stats['burned'],
                'total_burning': stats['burning']
            })
        
        return jsonify({
            'success': True,
            'simulations': simulations,
            'total_count': len(simulations)
        })
        
    except Exception as e:
        logger.error(f"Error listing simulations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_simulation_bp.route('/delete/<sim_id>', methods=['DELETE'])
def delete_simulation(sim_id):
    """Delete a simulation"""
    try:
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        del active_simulations[sim_id]
        
        logger.info(f"Deleted simulation {sim_id}")
        
        return jsonify({
            'success': True,
            'message': f'Simulation {sim_id} deleted'
        })
        
    except Exception as e:
        logger.error(f"Error deleting simulation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_simulation_bp.route('/export/<sim_id>', methods=['GET'])
def export_simulation_data(sim_id):
    """Export simulation data and history"""
    try:
        if sim_id not in active_simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim_data = active_simulations[sim_id]
        engine = sim_data['engine']
        
        export_data = {
            'simulation_id': sim_id,
            'metadata': sim_data['metadata'],
            'initial_grid_classification': sim_data['grid_classification'],
            'final_grid_state': engine.get_grid_state(),
            'step_history': sim_data['step_history'],
            'environmental_conditions': {
                'temperature': engine.conditions.temperature,
                'humidity': engine.conditions.humidity,
                'wind_speed': engine.conditions.wind_speed,
                'wind_direction': engine.conditions.wind_direction.name.lower(),
                'rain_probability': engine.conditions.rain_probability
            },
            'final_statistics': engine._calculate_statistics(),
            'export_timestamp': time.time()
        }
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting simulation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
