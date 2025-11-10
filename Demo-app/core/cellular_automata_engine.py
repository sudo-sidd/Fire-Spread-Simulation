"""
Enhanced Cellular Automaton Fire Simulation Engine
Works with OSM-based terrain classification and realistic fire spread properties
"""

import numpy as np
import random
import math
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class BurnState(Enum):
    """Fire burn states for cellular automaton"""
    UNBURNED = "unburned"
    BURNING = "burning" 
    BURNED = "burned"
    ASH = "ash"  # Completely burned out

class WindDirection(Enum):
    """Wind direction constants"""
    NORTH = 0
    NORTHEAST = 1
    EAST = 2
    SOUTHEAST = 3
    SOUTH = 4
    SOUTHWEST = 5
    WEST = 6
    NORTHWEST = 7

@dataclass
class EnvironmentalConditions:
    """Environmental conditions affecting fire spread"""
    temperature: float = 25.0  # Celsius
    humidity: float = 50.0     # Percentage
    wind_speed: float = 5.0    # km/h
    wind_direction: WindDirection = WindDirection.NORTH
    rain_probability: float = 0.0  # 0.0 - 1.0
    time_of_day: int = 12      # Hour (0-23)

@dataclass
class CellState:
    """State of a single cell in the automaton"""
    terrain_type: str
    burn_state: BurnState
    burn_intensity: float = 0.0  # 0.0 - 1.0
    burn_duration: int = 0       # Ticks spent burning
    moisture: float = 0.5        # 0.0 - 1.0
    fuel_load: float = 1.0       # Remaining combustible material
    temperature: float = 20.0    # Cell temperature
    
class CellularAutomatonEngine:
    """Enhanced cellular automaton engine for fire simulation"""
    
    def __init__(self, grid_size: int = 50):
        self.grid_size = grid_size
        self.grid: List[List[CellState]] = []
        self.tick_count = 0
        self.conditions = EnvironmentalConditions()
        
        # Neighborhood patterns
        self.moore_neighbors = [
            (-1, -1), (-1, 0), (-1, 1),
            ( 0, -1),          ( 0, 1),
            ( 1, -1), ( 1, 0), ( 1, 1)
        ]
        
        self.von_neumann_neighbors = [
            (-1, 0), (0, -1), (0, 1), (1, 0)
        ]
        
        # Use Moore neighborhood by default
        self.neighborhood = self.moore_neighbors
        
        # Fire spread parameters by terrain type
        self.terrain_fire_params = {
            'forest': {
                'max_burn_duration': 8,
                'spread_probability': 0.8,
                'fuel_consumption_rate': 0.12,
                'heat_generation': 0.9,
                'moisture_loss_rate': 0.15,
                'ignition_threshold': 0.3,  # Easy to ignite
                'is_flammable': True
            },
            'grass': {
                'max_burn_duration': 3,
                'spread_probability': 0.95,
                'fuel_consumption_rate': 0.25,
                'heat_generation': 0.7,
                'moisture_loss_rate': 0.3,
                'ignition_threshold': 0.2,  # Very easy to ignite
                'is_flammable': True
            },
            'shrub': {
                'max_burn_duration': 5,
                'spread_probability': 0.75,
                'fuel_consumption_rate': 0.18,
                'heat_generation': 0.8,
                'moisture_loss_rate': 0.2,
                'ignition_threshold': 0.35,  # Moderately easy to ignite
                'is_flammable': True
            },
            'agriculture': {
                'max_burn_duration': 4,
                'spread_probability': 0.6,
                'fuel_consumption_rate': 0.2,
                'heat_generation': 0.6,
                'moisture_loss_rate': 0.25,
                'ignition_threshold': 0.4,  # Moderate ignition threshold
                'is_flammable': True
            },
            'urban': {
                'max_burn_duration': 12,
                'spread_probability': 0.1,
                'fuel_consumption_rate': 0.05,
                'heat_generation': 0.3,
                'moisture_loss_rate': 0.1,
                'ignition_threshold': 0.9,  # Very hard to ignite
                'is_flammable': True  # Buildings can burn, but slowly
            },
            'water': {
                'max_burn_duration': 0,
                'spread_probability': 0.0,
                'fuel_consumption_rate': 0.0,
                'heat_generation': 0.0,
                'moisture_loss_rate': 0.0,
                'ignition_threshold': 999.0,  # Impossible to ignite
                'is_flammable': False  # Water cannot burn!
            },
            'bare_ground': {
                'max_burn_duration': 1,
                'spread_probability': 0.1,
                'fuel_consumption_rate': 0.8,
                'heat_generation': 0.2,
                'moisture_loss_rate': 0.4,
                'ignition_threshold': 0.85,  # Hard to ignite (minimal fuel)
                'is_flammable': True
            },
            'beach': {
                'max_burn_duration': 1,
                'spread_probability': 0.05,
                'fuel_consumption_rate': 0.9,
                'heat_generation': 0.1,
                'moisture_loss_rate': 0.5,
                'ignition_threshold': 0.95,  # Very hard to ignite
                'is_flammable': False  # Sand doesn't burn
            },
            'desert': {
                'max_burn_duration': 2,
                'spread_probability': 0.2,
                'fuel_consumption_rate': 0.6,
                'heat_generation': 0.3,
                'moisture_loss_rate': 0.6,
                'ignition_threshold': 0.8,  # Hard to ignite (low fuel)
                'is_flammable': True
            }
        }
    
    def initialize_from_terrain_grid(self, terrain_grid: List[List[Dict]]):
        """Initialize the cellular automaton from terrain classification data"""
        logger.info(f"Initializing {self.grid_size}x{self.grid_size} fire simulation grid")
        
        self.grid = []
        for row in range(self.grid_size):
            grid_row = []
            for col in range(self.grid_size):
                terrain_data = terrain_grid[row][col]
                terrain_type = terrain_data['terrain_type']
                properties = terrain_data.get('properties', {})
                
                # Get terrain-specific parameters
                terrain_params = self.terrain_fire_params.get(
                    terrain_type,
                    self.terrain_fire_params['grass']
                )
                
                # Set moisture based on terrain type
                if terrain_type == 'water':
                    base_moisture = 1.0  # Water is always wet
                elif terrain_type in ['urban', 'bare_ground', 'desert']:
                    base_moisture = 0.2  # Low moisture
                elif terrain_type in ['agriculture', 'grass']:
                    base_moisture = 0.5  # Medium moisture
                else:  # forest, shrub
                    base_moisture = 0.6  # Higher moisture
                
                # Override with property value if provided
                moisture = properties.get('moisture_retention', base_moisture)
                
                # Initialize cell state
                cell = CellState(
                    terrain_type=terrain_type,
                    burn_state=BurnState.UNBURNED,
                    burn_intensity=0.0,
                    burn_duration=0,
                    moisture=moisture,
                    fuel_load=1.0 if terrain_params.get('is_flammable', True) else 0.0,
                    temperature=self.conditions.temperature
                )
                
                grid_row.append(cell)
            self.grid.append(grid_row)
        
        logger.info("Fire simulation grid initialized")
    
    def ignite_cell(self, row: int, col: int, intensity: float = 1.0) -> bool:
        """Ignite a specific cell if possible"""
        if not self._is_valid_position(row, col):
            return False
        
        cell = self.grid[row][col]
        
        # Get terrain parameters
        terrain_params = self.terrain_fire_params.get(
            cell.terrain_type, 
            self.terrain_fire_params['grass']
        )
        
        # Check if terrain is flammable
        if not terrain_params.get('is_flammable', True):
            logger.warning(f"Cannot ignite non-flammable terrain '{cell.terrain_type}' at ({row}, {col})")
            return False
        
        # Can only ignite unburned cells with fuel
        if cell.burn_state == BurnState.UNBURNED and cell.fuel_load > 0:
            # Check if ignition is possible based on moisture and terrain
            ignition_threshold = terrain_params.get('ignition_threshold', 0.5)
            moisture_resistance = cell.moisture * ignition_threshold
            
            if intensity > moisture_resistance:
                cell.burn_state = BurnState.BURNING
                cell.burn_intensity = min(1.0, intensity)
                cell.burn_duration = 1
                logger.info(f"Ignited cell at ({row}, {col}) - {cell.terrain_type}")
                return True
            else:
                logger.info(f"Failed to ignite {cell.terrain_type} at ({row}, {col}): "
                          f"intensity {intensity:.2f} < moisture resistance {moisture_resistance:.2f}")
        
        return False
    
    def _is_valid_position(self, row: int, col: int) -> bool:
        """Check if position is within grid bounds"""
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size
    
    def _get_neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get valid neighbor positions"""
        neighbors = []
        for dr, dc in self.neighborhood:
            new_row, new_col = row + dr, col + dc
            if self._is_valid_position(new_row, new_col):
                neighbors.append((new_row, new_col))
        return neighbors
    
    def _calculate_wind_effect(self, from_row: int, from_col: int, 
                             to_row: int, to_col: int) -> float:
        """Calculate wind effect on fire spread between two cells"""
        # Calculate direction from source to target
        dr = to_row - from_row
        dc = to_col - from_col
        
        # Convert to wind direction factor
        wind_directions = {
            WindDirection.NORTH: (-1, 0),
            WindDirection.NORTHEAST: (-1, 1),
            WindDirection.EAST: (0, 1),
            WindDirection.SOUTHEAST: (1, 1),
            WindDirection.SOUTH: (1, 0),
            WindDirection.SOUTHWEST: (1, -1),
            WindDirection.WEST: (0, -1),
            WindDirection.NORTHWEST: (-1, -1)
        }
        
        wind_dr, wind_dc = wind_directions[self.conditions.wind_direction]
        
        # Calculate alignment with wind direction
        if wind_dr == 0 and wind_dc == 0:
            alignment = 0
        else:
            alignment = (dr * wind_dr + dc * wind_dc) / math.sqrt(dr*dr + dc*dc) / math.sqrt(wind_dr*wind_dr + wind_dc*wind_dc)
        
        # Wind speed effect (0-1 scale)
        wind_factor = min(1.0, self.conditions.wind_speed / 50.0)  # Normalize to 50 km/h max
        
        # Positive alignment increases spread, negative decreases
        wind_effect = 1.0 + (alignment * wind_factor * 0.5)
        return max(0.1, wind_effect)  # Minimum 10% chance even against wind
    
    def _calculate_spread_probability(self, source_cell: CellState, 
                                    target_cell: CellState,
                                    source_row: int, source_col: int,
                                    target_row: int, target_col: int) -> float:
        """Calculate probability of fire spreading from source to target cell"""
        
        # Target must be unburned and have fuel
        if target_cell.burn_state != BurnState.UNBURNED or target_cell.fuel_load <= 0:
            return 0.0
        
        # Get target terrain parameters
        target_params = self.terrain_fire_params.get(
            target_cell.terrain_type, 
            self.terrain_fire_params['grass']
        )
        
        # Check if target terrain is flammable
        if not target_params.get('is_flammable', True):
            return 0.0  # Non-flammable terrain cannot catch fire
        
        # Base spread probability from terrain
        base_prob = target_params['spread_probability']
        
        # If base probability is 0 (like water), immediately return 0
        if base_prob == 0.0:
            return 0.0
        
        # Modify by source intensity
        intensity_factor = source_cell.burn_intensity
        
        # Modify by target moisture (dry = easier to ignite)
        moisture_factor = 1.0 - target_cell.moisture
        
        # Modify by fuel load
        fuel_factor = target_cell.fuel_load
        
        # Environmental factors
        temp_factor = 1.0 + (self.conditions.temperature - 20) * 0.02  # 2% per degree above 20C
        humidity_factor = 1.0 - (self.conditions.humidity - 50) * 0.01  # 1% per % humidity above 50%
        rain_factor = 1.0 - self.conditions.rain_probability * 0.8  # Rain greatly reduces spread
        
        # Wind effect
        wind_effect = self._calculate_wind_effect(source_row, source_col, target_row, target_col)
        
        # Combine all factors
        total_probability = (base_prob * intensity_factor * moisture_factor * 
                           fuel_factor * temp_factor * humidity_factor * 
                           rain_factor * wind_effect)
        
        return min(1.0, max(0.0, total_probability))
    
    def _update_burning_cell(self, cell: CellState, row: int, col: int) -> List[Tuple[int, int]]:
        """Update a burning cell and return list of newly ignited neighbors"""
        terrain_params = self.terrain_fire_params.get(
            cell.terrain_type, 
            self.terrain_fire_params['grass']
        )
        
        newly_burning = []
        
        # Consume fuel
        fuel_consumption = terrain_params['fuel_consumption_rate'] * cell.burn_intensity
        cell.fuel_load = max(0.0, cell.fuel_load - fuel_consumption)
        
        # Increase temperature
        heat_gen = terrain_params['heat_generation'] * cell.burn_intensity
        cell.temperature = min(1000, cell.temperature + heat_gen * 50)
        
        # Reduce moisture from heat
        moisture_loss = terrain_params['moisture_loss_rate'] * cell.burn_intensity
        cell.moisture = max(0.0, cell.moisture - moisture_loss)
        
        # Increment burn duration
        cell.burn_duration += 1
        
        # Try to spread to neighbors
        neighbors = self._get_neighbors(row, col)
        for neighbor_row, neighbor_col in neighbors:
            neighbor_cell = self.grid[neighbor_row][neighbor_col]
            
            spread_prob = self._calculate_spread_probability(
                cell, neighbor_cell, row, col, neighbor_row, neighbor_col
            )
            
            if random.random() < spread_prob:
                neighbor_cell.burn_state = BurnState.BURNING
                neighbor_cell.burn_intensity = min(1.0, cell.burn_intensity * 0.8)
                neighbor_cell.burn_duration = 1
                newly_burning.append((neighbor_row, neighbor_col))
        
        # Check if cell should burn out
        max_duration = terrain_params['max_burn_duration']
        if cell.burn_duration >= max_duration or cell.fuel_load <= 0.1:
            cell.burn_state = BurnState.BURNED
            cell.burn_intensity = 0.0
            cell.temperature = self.conditions.temperature  # Cool down
        
        return newly_burning
    
    def step(self) -> Dict[str, Any]:
        """Execute one simulation step"""
        self.tick_count += 1
        
        # Find all currently burning cells
        burning_cells = []
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if self.grid[row][col].burn_state == BurnState.BURNING:
                    burning_cells.append((row, col))
        
        # Update all burning cells
        newly_ignited = []
        for row, col in burning_cells:
            cell = self.grid[row][col]
            new_fires = self._update_burning_cell(cell, row, col)
            newly_ignited.extend(new_fires)
        
        # Calculate statistics
        stats = self._calculate_statistics()
        
        logger.info(f"Simulation step {self.tick_count}: {len(burning_cells)} burning, "
                   f"{len(newly_ignited)} newly ignited, "
                   f"{stats['total_burned']} total burned")
        
        return {
            'tick': self.tick_count,
            'burning_cells': len(burning_cells),
            'newly_ignited': len(newly_ignited),
            'statistics': stats,
            'is_active': len(burning_cells) > 0
        }
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate simulation statistics"""
        stats = {
            'unburned': 0,
            'burning': 0,
            'burned': 0,
            'total_cells': self.grid_size * self.grid_size,
            'total_burned': 0,
            'avg_intensity': 0.0,
            'avg_temperature': 0.0,
            'fuel_remaining': 0.0
        }
        
        total_intensity = 0.0
        total_temperature = 0.0
        total_fuel = 0.0
        burning_count = 0
        
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                cell = self.grid[row][col]
                
                if cell.burn_state == BurnState.UNBURNED:
                    stats['unburned'] += 1
                elif cell.burn_state == BurnState.BURNING:
                    stats['burning'] += 1
                    burning_count += 1
                    total_intensity += cell.burn_intensity
                else:  # BURNED or ASH
                    stats['burned'] += 1
                
                total_temperature += cell.temperature
                total_fuel += cell.fuel_load
        
        stats['total_burned'] = stats['burned']
        
        if burning_count > 0:
            stats['avg_intensity'] = total_intensity / burning_count
        
        stats['avg_temperature'] = total_temperature / stats['total_cells']
        stats['fuel_remaining'] = total_fuel / stats['total_cells']
        
        return stats
    
    def get_grid_state(self) -> List[List[Dict]]:
        """Get current grid state for visualization"""
        grid_state = []
        
        for row in range(self.grid_size):
            row_state = []
            for col in range(self.grid_size):
                cell = self.grid[row][col]
                
                cell_state = {
                    'terrain_type': cell.terrain_type,
                    'burn_state': cell.burn_state.value,
                    'burn_intensity': cell.burn_intensity,
                    'burn_duration': cell.burn_duration,
                    'moisture': cell.moisture,
                    'fuel_load': cell.fuel_load,
                    'temperature': cell.temperature,
                    'row': row,
                    'col': col
                }
                
                row_state.append(cell_state)
            grid_state.append(row_state)
        
        return grid_state
    
    def set_environmental_conditions(self, conditions: Dict[str, Any]):
        """Update environmental conditions"""
        if 'temperature' in conditions:
            self.conditions.temperature = conditions['temperature']
        if 'humidity' in conditions:
            self.conditions.humidity = conditions['humidity']
        if 'wind_speed' in conditions:
            self.conditions.wind_speed = conditions['wind_speed']
        if 'wind_direction' in conditions:
            # Convert string to enum
            wind_dir_map = {
                'north': WindDirection.NORTH,
                'northeast': WindDirection.NORTHEAST,
                'east': WindDirection.EAST,
                'southeast': WindDirection.SOUTHEAST,
                'south': WindDirection.SOUTH,
                'southwest': WindDirection.SOUTHWEST,
                'west': WindDirection.WEST,
                'northwest': WindDirection.NORTHWEST
            }
            self.conditions.wind_direction = wind_dir_map.get(
                conditions['wind_direction'].lower(), 
                WindDirection.NORTH
            )
        if 'rain_probability' in conditions:
            self.conditions.rain_probability = conditions['rain_probability']
        if 'time_of_day' in conditions:
            self.conditions.time_of_day = conditions['time_of_day']
        
        logger.info(f"Updated environmental conditions: "
                   f"temp={self.conditions.temperature}°C, "
                   f"humidity={self.conditions.humidity}%, "
                   f"wind={self.conditions.wind_speed}km/h {self.conditions.wind_direction.name}")
    
    def reset(self):
        """Reset the simulation"""
        self.tick_count = 0
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                cell = self.grid[row][col]
                cell.burn_state = BurnState.UNBURNED
                cell.burn_intensity = 0.0
                cell.burn_duration = 0
                cell.fuel_load = 1.0
                cell.temperature = self.conditions.temperature
                # Reset moisture to terrain-based default
                terrain_params = self.terrain_fire_params.get(
                    cell.terrain_type,
                    self.terrain_fire_params['grass']
                )
                # Water has high moisture, others vary
                if cell.terrain_type == 'water':
                    cell.moisture = 1.0
                elif cell.terrain_type in ['urban', 'bare_ground']:
                    cell.moisture = 0.2
                else:
                    cell.moisture = 0.5
        
        logger.info("Simulation reset")
