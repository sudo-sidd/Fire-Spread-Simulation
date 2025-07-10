"""
Enhanced Fire Simulation Engine
Combines cellular automata with real terrain data and weather conditions
"""

import numpy as np
import random
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from core.config import Config

@dataclass
class WeatherConditions:
    """Weather parameters affecting fire spread"""
    wind_speed: float = 5.0      # km/h
    wind_direction: float = 0.0   # degrees (0-360, 0 = North)
    humidity: float = 50.0        # percentage
    temperature: float = 25.0     # celsius
    precipitation: float = 0.0    # mm/hour

class FireCell:
    """Individual cell in the fire simulation grid"""
    
    def __init__(self, terrain_type: str = 'grass'):
        self.terrain_type = terrain_type
        self.terrain_props = Config.TERRAIN_TYPES.get(terrain_type, Config.TERRAIN_TYPES['grass'])
        
        # Fire state: 0=normal, 1=burning, 2=burned, 3=smoldering
        self.fire_state = 0
        self.fuel_load = self.terrain_props['fuel_load']
        self.burn_time = 0
        self.max_burn_time = Config.BURN_TIME
        
        # Environmental factors
        self.moisture_content = 0.3  # 0-1, affects ignition probability
        self.elevation = 0.0         # meters above sea level
        
    def can_ignite(self) -> bool:
        """Check if cell can catch fire"""
        return (self.fire_state == 0 and 
                self.fuel_load > 0 and 
                self.terrain_type not in ['water', 'urban'])
    
    def ignite(self):
        """Set cell on fire"""
        if self.can_ignite():
            self.fire_state = 1
            self.burn_time = 0
    
    def update(self, weather: WeatherConditions) -> bool:
        """Update cell state, returns True if state changed"""
        old_state = self.fire_state
        
        if self.fire_state == 1:  # Currently burning
            self.burn_time += 1
            
            # Extinguish due to rain
            if weather.precipitation > 5.0:  # Heavy rain
                self.fire_state = 0  # Extinguished
                return old_state != self.fire_state
            
            # Transition to burned state
            if self.burn_time >= self.max_burn_time:
                self.fire_state = 2  # Burned
                self.fuel_load = 0  # No fuel left
        
        return old_state != self.fire_state

class FireSimulation:
    """Main fire simulation engine"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[FireCell() for _ in range(width)] for _ in range(height)]
        self.weather = WeatherConditions()
        self.step_count = 0
        
        # Statistics tracking
        self.burning_cells = 0
        self.burned_cells = 0
        self.total_burned_area = 0.0  # km²
        
    def set_terrain_from_bitmap(self, terrain_bitmap: np.ndarray, terrain_map: Dict[Tuple[int, int, int], str]):
        """Set terrain types from a bitmap image"""
        if terrain_bitmap.shape[:2] != (self.height, self.width):
            # Resize bitmap to match grid
            from PIL import Image
            img = Image.fromarray(terrain_bitmap)
            img = img.resize((self.width, self.height), Image.NEAREST)
            terrain_bitmap = np.array(img)
        
        for y in range(self.height):
            for x in range(self.width):
                pixel_color = tuple(terrain_bitmap[y, x][:3])  # RGB only
                
                # Find closest matching terrain type
                terrain_type = self._find_closest_terrain_type(pixel_color, terrain_map)
                self.grid[y][x] = FireCell(terrain_type)
    
    def _find_closest_terrain_type(self, pixel_color: Tuple[int, int, int], 
                                 terrain_map: Dict[Tuple[int, int, int], str]) -> str:
        """Find the closest matching terrain type for a pixel color"""
        if pixel_color in terrain_map:
            return terrain_map[pixel_color]
        
        # Find closest color match
        min_distance = float('inf')
        closest_terrain = 'grass'
        
        for color, terrain_type in terrain_map.items():
            distance = sum((a - b) ** 2 for a, b in zip(pixel_color, color))
            if distance < min_distance:
                min_distance = distance
                closest_terrain = terrain_type
        
        return closest_terrain
    
    def ignite_at(self, x: int, y: int) -> bool:
        """Start a fire at specific coordinates"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x].ignite()
            return True
        return False
    
    def step(self) -> Dict:
        """Advance simulation by one time step using cellular automata approach"""
        self.step_count += 1
        new_ignitions = []
        state_changes = 0
        
        # Create a copy of the current grid state for simultaneous updates (CA approach)
        next_grid_states = {}
        
        # First pass: Update all cell states and determine fire spread
        for y in range(self.height):
            for x in range(self.width):
                current_cell = self.grid[y][x]
                next_grid_states[(x, y)] = current_cell.fire_state
                
                # Update burning cells (similar to CA: burning -> burned)
                if current_cell.fire_state == 1:  # Currently burning
                    # Update burn time
                    current_cell.burn_time += 1
                    
                    # Check if cell should burn out (like CA: burning becomes ash)
                    if (current_cell.burn_time >= current_cell.max_burn_time or 
                        self.weather.precipitation > 5.0):  # Heavy rain extinguishes
                        next_grid_states[(x, y)] = 2  # Becomes burned
                        current_cell.fuel_load = 0
                        state_changes += 1
                    
                    # Spread fire to neighbors (CA fire spread logic)
                    self._spread_fire_to_neighbors(x, y, new_ignitions)
                
                elif current_cell.fire_state == 0:  # Normal cell
                    # Check for spontaneous ignition (like CA spontaneous ignition)
                    if (current_cell.can_ignite() and 
                        random.random() < Config.IGNITION_PROBABILITY):
                        new_ignitions.append((x, y))
        
        # Second pass: Apply all state changes simultaneously (CA approach)
        for (x, y), new_state in next_grid_states.items():
            if self.grid[y][x].fire_state != new_state:
                self.grid[y][x].fire_state = new_state
                state_changes += 1
        
        # Apply new ignitions from fire spread
        for x, y in new_ignitions:
            if self.grid[y][x].can_ignite():
                self.grid[y][x].ignite()
                state_changes += 1
        
        # Update statistics
        self._update_statistics()
        
        return {
            'step': self.step_count,
            'new_ignitions': len(new_ignitions),
            'state_changes': state_changes,
            'burning_cells': self.burning_cells,
            'burned_cells': self.burned_cells,
            'total_burned_area_km2': self.total_burned_area
        }
    
    def _spread_fire_to_neighbors(self, x: int, y: int, new_ignitions: List[Tuple[int, int]]):
        """Spread fire to neighboring cells using CA-style rules"""
        # CA-style 4-directional spread (or 8-directional for more realistic spread)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # 4-directional like basic CA
        # For 8-directional: directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        current_cell = self.grid[y][x]
        base_spread_rate = current_cell.terrain_props['spread_rate']
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # Check bounds
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbor_cell = self.grid[ny][nx]
                
                # Can only spread to flammable cells (like CA: only spread to trees)
                if neighbor_cell.can_ignite():
                    # Calculate spread probability based on terrain and weather
                    spread_prob = self._calculate_spread_probability(x, y, nx, ny, base_spread_rate)
                    
                    # CA-style probabilistic spread
                    if random.random() < spread_prob:
                        new_ignitions.append((nx, ny))
    
    def _get_spread_candidates(self, x: int, y: int) -> List[Tuple[int, int, float]]:
        """Get neighboring cells with spread probabilities"""
        candidates = []
        base_spread_rate = self.grid[y][x].terrain_props['spread_rate']
        
        # 8-directional spread with wind influence
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < self.width and 0 <= ny < self.height:
                # Calculate wind influence
                spread_prob = self._calculate_spread_probability(
                    x, y, nx, ny, base_spread_rate
                )
                candidates.append((nx, ny, spread_prob))
        
        return candidates
    
    def _calculate_spread_probability(self, from_x: int, from_y: int, 
                                    to_x: int, to_y: int, base_rate: float) -> float:
        """Calculate fire spread probability considering wind and terrain"""
        
        # Direction of spread
        dx, dy = to_x - from_x, to_y - from_y
        spread_angle = np.arctan2(dy, dx) * 180 / np.pi
        
        # Wind influence
        wind_radians = np.radians(self.weather.wind_direction)
        wind_dx, wind_dy = np.sin(wind_radians), np.cos(wind_radians)
        
        # Dot product for wind alignment (-1 to 1)
        wind_alignment = (dx * wind_dx + dy * wind_dy) / np.sqrt(dx*dx + dy*dy)
        wind_multiplier = 1.0 + (wind_alignment * self.weather.wind_speed / 20.0)
        
        # Terrain factors
        target_cell = self.grid[to_y][to_x]
        terrain_factor = target_cell.terrain_props['spread_rate']
        
        # Weather factors
        humidity_factor = max(0.1, 1.0 - self.weather.humidity / 100.0)
        temp_factor = min(2.0, max(0.5, (self.weather.temperature - 10) / 30.0))
        
        # Combine all factors
        final_probability = (base_rate * terrain_factor * wind_multiplier * 
                           humidity_factor * temp_factor * Config.SPREAD_PROBABILITY)
        
        return min(1.0, max(0.0, final_probability))
    
    def _update_statistics(self):
        """Update simulation statistics"""
        self.burning_cells = 0
        self.burned_cells = 0
        
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x].fire_state == 1:
                    self.burning_cells += 1
                elif self.grid[y][x].fire_state == 2:
                    self.burned_cells += 1
        
        # Estimate burned area (assuming each cell represents ~25m²)
        cell_area_km2 = 0.000025  # 25m² in km²
        self.total_burned_area = self.burned_cells * cell_area_km2
    
    def get_fire_state_array(self) -> np.ndarray:
        """Get current fire state as numpy array for visualization"""
        state_array = np.zeros((self.height, self.width), dtype=np.uint8)
        
        for y in range(self.height):
            for x in range(self.width):
                state_array[y, x] = self.grid[y][x].fire_state
        
        return state_array
    
    def get_terrain_state_array(self) -> np.ndarray:
        """Get terrain types as numpy array"""
        terrain_array = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        for y in range(self.height):
            for x in range(self.width):
                color = self.grid[y][x].terrain_props['color']
                terrain_array[y, x] = color
        
        return terrain_array
    
    def reset(self):
        """Reset simulation to initial state"""
        self.step_count = 0
        self.burning_cells = 0
        self.burned_cells = 0
        self.total_burned_area = 0.0
        
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                cell.fire_state = 0
                cell.burn_time = 0
                # Restore fuel load based on terrain type
                cell.fuel_load = cell.terrain_props['fuel_load']
    
    def set_weather(self, weather: WeatherConditions):
        """Update weather conditions"""
        self.weather = weather
    
    def is_active(self) -> bool:
        """Check if simulation has active fires"""
        return self.burning_cells > 0
    
    def get_cell_state(self, row: int, col: int) -> str:
        """Get the fire state of a specific cell"""
        if (0 <= row < self.height and 0 <= col < self.width):
            cell = self.grid[row][col]
            if cell.fire_state == 0:
                return 'normal'
            elif cell.fire_state == 1:
                return 'burning'
            elif cell.fire_state == 2:
                return 'burned'
            elif cell.fire_state == 3:
                return 'smoldering'
        return 'normal'
    
    def get_cell_terrain(self, row: int, col: int) -> str:
        """Get the terrain type of a specific cell"""
        if (0 <= row < self.height and 0 <= col < self.width):
            return self.grid[row][col].terrain_type
        return 'grass'
    
    def get_all_fire_states(self) -> List[List[str]]:
        """Get fire states for all cells in the grid"""
        states = []
        for row in range(self.height):
            row_states = []
            for col in range(self.width):
                row_states.append(self.get_cell_state(row, col))
            states.append(row_states)
        return states
    
    def random_ignite(self, num_ignitions: int = None, ignition_probability: float = 0.02) -> int:
        """
        Randomly ignite flammable cells across the grid using cellular automata approach
        
        Args:
            num_ignitions: Number of fires to start. If None, uses probability-based ignition
            ignition_probability: Probability for each flammable cell to ignite (if num_ignitions is None)
            
        Returns:
            Number of cells actually ignited
        """
        flammable_cells = []
        
        # Find all flammable cells (similar to CA implementation)
        for y in range(self.height):
            for x in range(self.width):
                cell = self.grid[y][x]
                # Only ignite cells that can burn (like trees in CA)
                if (cell.can_ignite() and 
                    cell.terrain_type in ['forest', 'grass', 'shrub', 'agriculture']):
                    flammable_cells.append((y, x))
        
        if not flammable_cells:
            return 0
        
        ignited_count = 0
        
        if num_ignitions is not None:
            # Ignite a specific number of random cells (like manual ignition in CA)
            num_to_ignite = min(num_ignitions, len(flammable_cells))
            selected_cells = random.sample(flammable_cells, num_to_ignite)
            
            for y, x in selected_cells:
                cell = self.grid[y][x]
                if cell.can_ignite():
                    cell.ignite()  # Set fire state to burning (like state 2 in CA)
                    ignited_count += 1
        else:
            # Use probability-based ignition (like spontaneous ignition in CA)
            for y, x in flammable_cells:
                if random.random() < ignition_probability:
                    cell = self.grid[y][x]
                    if cell.can_ignite():
                        cell.ignite()
                        ignited_count += 1
        
        # Update statistics after ignition
        self._update_statistics()
        
        return ignited_count

    def get_flammable_cell_count(self) -> int:
        """Get the total number of flammable cells in the grid"""
        count = 0
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x].can_ignite():
                    count += 1
        return count
