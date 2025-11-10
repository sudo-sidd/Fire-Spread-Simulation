# Terrain Extraction Debugging Guide

## Issues Identified and Fixed

### Issue 1: Using OSM Rendered Maps Instead of Satellite Imagery
**Problem:** OpenStreetMap tiles are rendered maps with roads, labels, and styled features - NOT raw satellite imagery. This makes RGB color-based terrain detection very unreliable.

**Solution:** 
- Updated `download_tile()` to try ESRI World Imagery (satellite) first
- Falls back to OSM only if satellite imagery unavailable
- Satellite imagery provides actual ground cover colors for classification

### Issue 2: Poor Color-Based Classification
**Problem:** Simple RGB range checking didn't work well because:
- OSM tiles have text labels, road overlays
- Vegetation appears in various shades
- Urban areas have mixed colors

**Solution - Enhanced `classify_pixel_terrain()`:**
```python
# Water detection
if b > 100 and b > r + 30 and b > g + 10:
    return 'water'

# Vegetation using NDVI-like metric
green_ratio = (g - r) / (g + r)
if green_ratio > 0.15:  # Strong vegetation
    if g < 130:
        return 'forest'  # Dark green
    else:
        return 'grass'   # Bright green
```

### Issue 3: Scale and Coordinate Alignment
**Problem:** Grid cells not aligning properly with map coordinates.

**Current Calculation:**
```python
# Cell size in degrees (default 0.001° ≈ 111 meters)
cell_size_degrees = 0.001

# Grid center at selected lat/lon
half_size = grid_size * cell_size_degrees / 2

# Each cell's coordinates
cell_lat = center_lat - half_size + (row + 0.5) * cell_size_degrees
cell_lon = center_lon - half_size + (col + 0.5) * cell_size_degrees
```

**For 50x50 grid at 0.001° per cell:**
- Total area: 0.05° x 0.05° (≈ 5.5km x 5.5km)
- Each cell: ~111m x 111m
- Grid starts at northwest corner
- Row 0 = northernmost cells
- Col 0 = westernmost cells

### Issue 4: Terrain Type "Unknown"
**Problem:** Classification defaulting to 'grass' when no clear match found.

**Root Causes:**
1. OSM tiles showing roads/labels instead of ground cover
2. Mixed pixel colors in urban areas
3. Tile download failures

**Fixes:**
- Better satellite imagery source
- Enhanced NDVI-like vegetation detection
- Improved logging to track classification decisions
- Better fallback handling

## Testing the Fixes

### Test 1: Check Tile Source
```python
# In browser console after loading terrain:
# Check network tab for tile requests
# Should see: server.arcgisonline.com (satellite)
# Not just: tile.openstreetmap.org
```

### Test 2: Verify Coordinates
```python
# Select a location with known terrain (e.g., Central Park NYC)
lat = 40.785091
lon = -73.968285

# Grid should:
# - Center on this point
# - Extend ±0.025° (~2.75km) in each direction
# - Show green (forest/grass) in park area
# - Show gray (urban) around edges
```

### Test 3: Check Classification Logic
Enable debug logging in `map_tile_service.py`:
```python
# Should see logs like:
# "Cell at (40.7851, -73.9683): sampled 100 pixels, 
#  votes: {'forest': 60, 'grass': 30, 'urban': 10}, result: forest"
```

### Test 4: Visual Verification
1. Load terrain for a known area
2. Compare with satellite view in Google Maps
3. Check if colors match:
   - Forest areas → Dark green (#228B22)
   - Grass/parks → Light green (#90EE90)
   - Water → Blue (#4682B4)
   - Urban → Gray (#808080)

## Common Issues and Solutions

### "No tiles downloaded, using synthetic terrain"
**Causes:**
- Network timeout
- ESRI/OSM servers down
- Rate limiting

**Solutions:**
- Check network connection
- Reduce grid size temporarily
- Wait a moment and retry

### "Unknown terrain type" or mostly 'grass'
**Causes:**
- OSM tiles being used (not satellite)
- Poor color detection on mixed pixels
- White text labels on tiles

**Solutions:**
- Verify satellite tiles are loading
- Check browser console for 403/429 errors
- Try different location
- Reduce grid size for faster testing

### Grid appears offset from map
**Causes:**
- Cell size mismatch between frontend and backend
- Coordinate calculation error
- Map projection issues

**Solutions:**
- Verify `cellSizeDegrees` matches in JS and Python (0.001)
- Check grid center coordinates in both systems
- Ensure consistent row/col indexing (0-based)

### Fire spreads across water
**Causes:**
- Water classified as 'grass' or other flammable terrain
- Classification not detecting blue pixels

**Solutions:**
- Check terrain grid colors (water should be #4682B4)
- Verify water cells have `is_flammable: False`
- Look at classification votes in logs

## Improved Classification Algorithm

### Before:
```python
# Simple range check
if r_min <= r <= r_max and g_min <= g <= g_max and b_min <= b <= b_max:
    return terrain_type
```

### After:
```python
# Priority-based detection:

# 1. Water (blue dominant)
if b > r + 30 and b > g + 10:
    return 'water'

# 2. Urban (neutral colors)
if abs(r - g) < 30 and abs(g - b) < 30 and r > 80:
    return 'urban'

# 3. Vegetation (green analysis)
green_ratio = (g - r) / (g + r)
if green_ratio > 0.15:
    return 'forest' if g < 130 else 'grass'

# 4. Soil/agriculture (red/yellow)
if r > g and r > b and r > 100:
    return 'agriculture' if g > 80 else 'bare_ground'
```

## Debugging Checklist

- [ ] Check browser console for tile download errors
- [ ] Verify satellite tiles loading (not just OSM)
- [ ] Check terrain statistics after classification
- [ ] Verify grid alignment with map
- [ ] Test known locations (parks, lakes, cities)
- [ ] Check cell colors match terrain types
- [ ] Verify water is non-flammable
- [ ] Test fire spread respects terrain boundaries

## Recommended Test Locations

### Forest Areas:
- Black Forest, Germany: 48.5, 8.2
- Amazon Rainforest: -3.4, -62.2
- Pacific Northwest: 47.5, -121.7

### Mixed Terrain:
- San Francisco Bay: 37.8, -122.4 (water, urban, grass)
- Central Park NYC: 40.785, -73.968 (park in city)
- Rural farmland: 41.5, -88.5 (agriculture, grass)

### Water Bodies:
- Lake Tahoe: 39.1, -120.0
- Great Lakes: 45.0, -85.0
- Ocean coastline: Any coastal city

## Performance Monitoring

### Expected Times:
- Tile download (50x50 grid): 2-5 seconds
- Classification: 1-3 seconds
- Total: 3-8 seconds

### If Slower:
- Network latency
- Too many tiles (reduce grid size)
- Server rate limiting

### Optimization Tips:
- Cache tiles locally (future enhancement)
- Use lower zoom for larger grids
- Implement progressive loading
