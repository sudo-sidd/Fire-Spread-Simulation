# Cellular Automata Fire Simulation - Terrain-Based Improvements

## Overview
Fixed critical issues in the cellular automata fire simulation where terrain properties were not being properly respected, particularly for water and other non-flammable terrain types.

## Issues Fixed

### 1. **Water and Non-Flammable Terrain Burning**
**Problem:** Water, beaches, and other non-flammable terrains were catching fire and spreading flames.

**Solution:**
- Added `is_flammable` flag to each terrain type in `cellular_automata_engine.py`
- Water now has:
  - `spread_probability: 0.0` (cannot spread fire)
  - `max_burn_duration: 0` (cannot burn)
  - `is_flammable: False` (explicitly non-flammable)
  - `ignition_threshold: 999.0` (impossible to ignite)
- Beach terrain also marked as non-flammable

### 2. **Terrain-Specific Ignition Thresholds**
**Problem:** All terrain types had the same ignition difficulty, making it unrealistic.

**Solution:** Added unique `ignition_threshold` values for each terrain type:
```python
'water': 999.0      # Impossible to ignite
'beach': 0.95       # Very hard to ignite
'bare_ground': 0.85 # Hard to ignite (minimal fuel)
'urban': 0.9        # Very hard to ignite
'desert': 0.8       # Hard to ignite (low fuel)
'agriculture': 0.4  # Moderate
'shrub': 0.35       # Moderately easy
'forest': 0.3       # Easy to ignite
'grass': 0.2        # Very easy to ignite
```

### 3. **Enhanced Fire Spread Calculations**
**Problem:** Fire spread didn't properly check terrain flammability before attempting to spread.

**Solution in `_calculate_spread_probability()`:**
```python
# Check if target terrain is flammable
if not target_params.get('is_flammable', True):
    return 0.0  # Non-flammable terrain cannot catch fire

# If base probability is 0 (like water), immediately return 0
if base_prob == 0.0:
    return 0.0
```

### 4. **Proper Cell Initialization**
**Problem:** All cells initialized with same fuel load and moisture, regardless of terrain.

**Solution in `initialize_from_terrain_grid()`:**
- **Moisture levels by terrain:**
  - Water: 1.0 (always wet)
  - Urban/Bare ground/Desert: 0.2 (low moisture)
  - Agriculture/Grass: 0.5 (medium moisture)
  - Forest/Shrub: 0.6 (higher moisture)

- **Fuel load:**
  - Non-flammable terrain (water, beach): 0.0
  - Flammable terrain: 1.0

### 5. **Terrain Properties in Map Tiles Service**
**Problem:** Terrain classification didn't include fire-related properties.

**Solution:** Added `_get_terrain_properties()` method in `map_tile_service.py`:
```python
'water': {
    'moisture_retention': 1.0,
    'flammability': 0.0,
    'fuel_density': 0.0,
    'is_flammable': False
}
'grass': {
    'moisture_retention': 0.5,
    'flammability': 0.9,
    'fuel_density': 0.8,
    'is_flammable': True
}
# ... etc for all terrain types
```

## Technical Details

### Cell State Properties
Each cell in the simulation now properly maintains:
- `terrain_type`: String identifier (forest, water, grass, etc.)
- `burn_state`: Current fire state (UNBURNED, BURNING, BURNED)
- `burn_intensity`: 0.0 - 1.0 (heat of fire)
- `burn_duration`: Ticks spent burning
- `moisture`: 0.0 - 1.0 (affects ignition)
- `fuel_load`: 0.0 - 1.0 (remaining combustible material)
- `temperature`: Current temperature in Celsius

### Fire Spread Algorithm
The simulation now properly:
1. **Checks terrain flammability** before attempting ignition
2. **Calculates moisture resistance** based on terrain type
3. **Applies terrain-specific spread rates** 
4. **Respects environmental conditions** (wind, humidity, temperature, rain)
5. **Uses proper fuel consumption rates** per terrain type

### Visual Representation
- Each terrain type displays with its specific color
- Water appears as blue and is visually distinguishable
- Fire overlay only appears on actually burning/burned cells
- Tooltips show terrain type and fire properties

## Testing Recommendations

### Test Scenarios:
1. **Water Test:** 
   - Create fire near water body
   - Verify fire does NOT spread across water
   - Verify clicking water cells shows ignition failure

2. **Urban-Wildland Interface:**
   - Place fire in grass near urban area
   - Verify fire spreads slowly/minimally to urban cells
   - Verify urban cells are hard to ignite

3. **Mixed Terrain:**
   - Create simulation with forest, grass, water, and urban
   - Verify each terrain behaves with correct burn rates
   - Check that fire naturally stops at water boundaries

4. **Fuel Depletion:**
   - Run simulation until fuel is depleted
   - Verify cells become BURNED and stop spreading
   - Verify burned cells show correct visual state

## Files Modified

1. **`Demo-app/core/cellular_automata_engine.py`**
   - Added `is_flammable` and `ignition_threshold` to terrain parameters
   - Enhanced `ignite_cell()` to check terrain flammability
   - Updated `_calculate_spread_probability()` with flammability checks
   - Improved `initialize_from_terrain_grid()` with terrain-specific moisture/fuel
   - Fixed `reset()` to properly restore terrain-based defaults

2. **`Demo-app/services/map_tile_service.py`**
   - Added `_get_terrain_properties()` method
   - Enhanced grid classification to include fire properties
   - Updated synthetic grid generation with properties

## Expected Behavior

### Water Bodies:
- ✅ **Cannot be ignited** (ignition attempts return false)
- ✅ **Do not spread fire** (spread probability = 0.0)
- ✅ **Act as natural firebreaks**
- ✅ **Maintain blue color visualization**

### Different Terrain Types:
- ✅ **Grass:** Burns quickly, spreads fast
- ✅ **Forest:** Burns longer, spreads moderately
- ✅ **Shrub:** Medium burn rate and spread
- ✅ **Agriculture:** Moderate flammability
- ✅ **Urban:** Very slow spread, hard to ignite
- ✅ **Bare ground/Desert:** Minimal spread, hard to ignite
- ✅ **Water/Beach:** Non-flammable

## Performance Impact
- Minimal impact on performance
- Additional property checks are simple boolean/numeric comparisons
- Terrain classification happens once during initialization
- Fire spread calculations remain O(1) per cell check

## Future Enhancements
1. Add terrain-based smoke generation
2. Implement firebreak effectiveness based on width
3. Add seasonal vegetation moisture variations
4. Include elevation-based fire spread (uphill faster)
5. Implement fire spotting for certain conditions

## Conclusion
The cellular automata engine now properly respects terrain properties, with water and other non-flammable surfaces acting as realistic firebreaks. Each terrain type has unique fire characteristics that create more realistic and scientifically accurate fire spread simulations.
