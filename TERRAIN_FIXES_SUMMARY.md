# Terrain Extraction Fixes - Summary

## Problems Identified

### 1. ❌ Wrong Imagery Source
**Issue:** Using OpenStreetMap rendered tiles instead of satellite imagery
- OSM tiles show roads, labels, and styled features
- Makes RGB color detection very unreliable
- "Forest" areas might appear white due to labels

**Fix:** ✅ Use satellite imagery first
```python
urls = [
    # ESRI World Imagery (satellite) - FIRST PRIORITY
    f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}",
    # OSM as fallback only
    f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
]
```

### 2. ❌ Poor Color Classification
**Issue:** Simple RGB range checking didn't detect vegetation properly

**Fix:** ✅ Enhanced classification algorithm
```python
# Water detection (blue dominant)
if b > 100 and b > r + 30 and b > g + 10:
    return 'water'

# Vegetation using NDVI-like metric
green_ratio = (g - r) / (g + r)
if green_ratio > 0.15:  # Vegetation present
    if g < 130:
        return 'forest'  # Dark green
    else:
        return 'grass'   # Bright green

# Urban areas (neutral colors)
if abs(r - g) < 30 and abs(g - b) < 30 and r > 80:
    return 'urban'
```

### 3. ❌ Scale Misalignment
**Issue:** Grid cells not aligning properly with map view

**Verification:** Grid coordinate calculation is correct:
```python
# For 50x50 grid with 0.001° cells:
total_area = 0.05° x 0.05° ≈ 5.5km x 5.5km
each_cell = 0.001° ≈ 111 meters

# Cell positions (verified):
cell_lat = center_lat - half_size + (row + 0.5) * cell_size
cell_lon = center_lon - half_size + (col + 0.5) * cell_size
```

**Note:** Alignment issues are usually due to:
- Tile download failures
- Using OSM instead of satellite tiles
- Browser zoom level vs tile zoom mismatch

### 4. ❌ "Unknown" Terrain Types
**Root Cause:** Defaulting to 'grass' when classification fails

**Fix:** ✅ Better logging and fallback handling
```python
logger.debug(f"Cell at ({lat:.4f}, {lon:.4f}): "
            f"sampled {sample_count} pixels, "
            f"votes: {terrain_votes}, "
            f"result: {dominant_terrain}")
```

## What Changed

### File: `Demo-app/services/map_tile_service.py`

#### 1. Enhanced Tile Download
```python
async def download_tile(...):
    # Try satellite imagery first
    urls = [
        f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}",
        f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"  # Fallback
    ]
```

#### 2. Improved Classification
```python
def classify_pixel_terrain(self, rgb):
    # Priority-based detection:
    # 1. Water (blue)
    # 2. Urban (gray)
    # 3. Vegetation (green ratio analysis)
    # 4. Soil/agriculture (brown/yellow)
    # 5. Fallback to range-based matching
```

#### 3. Better Logging
```python
logger.info(f"Cell size: {cell_size_degrees}° (~{cell_size_degrees * 111000:.1f}m)")
logger.info(f"Downloaded {len(tiles)} tiles at zoom level {zoom}")
logger.info(f"Terrain distribution: {terrain_stats}")
```

### File: `Demo-app/api/terrain_api.py`

#### Added Debug Endpoint
```python
@terrain_bp.route('/debug-cell', methods=['POST'])
def debug_cell_classification():
    # Returns detailed classification info for testing
    # Shows RGB values of sample pixels
    # Shows what each pixel was classified as
```

## How to Use the Fixes

### 1. Test with Known Locations

#### Forest Test:
```javascript
// In browser console
fetch('/api/terrain/classify-grid', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        lat: 47.5,      // Pacific Northwest
        lon: -121.7,
        grid_size: 20,  // Small for testing
        cell_size_degrees: 0.001
    })
}).then(r => r.json()).then(console.log)
```

#### Mixed Terrain Test:
```javascript
// Central Park NYC
{
    lat: 40.785,
    lon: -73.968,
    grid_size: 30
}
```

### 2. Check Tile Sources

**In Browser DevTools → Network Tab:**
- Look for: `arcgisonline.com` (good - satellite)
- Avoid: Only `openstreetmap.org` (not ideal)

### 3. Verify Classifications

**Check browser console logs:**
```
Terrain distribution: {
    'forest': 120,
    'grass': 85,
    'urban': 45,
    'water': 10
}
```

### 4. Debug Specific Cell

```javascript
// Test classification for a single point
fetch('/api/terrain/debug-cell', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        lat: 40.785,
        lon: -73.968
    })
}).then(r => r.json()).then(console.log)

// Returns RGB values and classification for sample pixels
```

## Expected Behavior After Fixes

### ✅ Water Bodies
- Lakes/rivers appear as **blue** (#4682B4)
- Classified as 'water'
- Cannot burn (is_flammable: False)

### ✅ Forest Areas
- Dense trees appear as **dark green** (#228B22)
- Classified as 'forest'
- High flammability, spreads fire effectively

### ✅ Grass/Parks
- Open areas appear as **light green** (#90EE90)
- Classified as 'grass'
- Very high flammability, fast spread

### ✅ Urban Areas
- Buildings/roads appear as **gray** (#808080)
- Classified as 'urban'
- Low flammability, slow spread

### ✅ Grid Alignment
- Grid cells align with map features
- 50x50 grid covers ~5.5km x 5.5km
- Each cell represents ~111m x 111m

## Troubleshooting

### Still Getting "Unknown" Terrain?

**Check:**
1. Network tab - are tiles downloading?
2. Console errors - any 403/429 responses?
3. Try smaller grid (20x20) for faster testing
4. Try different location

**Debug:**
```javascript
// Enable debug logging
localStorage.setItem('debug', 'true')
```

### Grid Appears Offset?

**Verify:**
1. Center coordinates match between map and classification
2. Cell size is consistent (0.001°)
3. Zoom level appropriate for area size

**Fix:**
- Reload page
- Clear browser cache
- Try clicking to reselect area

### Tiles Not Downloading?

**Causes:**
- ESRI rate limiting
- Network issues
- CORS problems

**Solutions:**
- Wait 1-2 minutes and retry
- Use smaller grid size
- Check browser console for errors

### Wrong Terrain Types?

**Check:**
1. Are satellite tiles loading? (not OSM)
2. Is the area actually what you expect?
3. Test with known locations (parks, lakes)

**Verify:**
```javascript
// Use debug endpoint
fetch('/api/terrain/debug-cell', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ lat: YOUR_LAT, lon: YOUR_LON })
}).then(r => r.json()).then(data => {
    console.log('Terrain:', data.terrain_type);
    console.log('Sample pixels:', data.sample_pixels);
})
```

## Performance Notes

### Expected Times:
- Tile download (50x50): 3-6 seconds
- Classification: 1-2 seconds
- **Total: 4-8 seconds**

### Optimization:
- Reduce grid size for testing (20x20)
- Use appropriate zoom level
- Avoid very large grids (100x100+)

## Next Steps

### Recommended Improvements:
1. **Tile caching** - Store downloaded tiles
2. **Progressive loading** - Show partial results
3. **Multiple imagery sources** - Sentinel, Landsat
4. **ML classification** - Use trained model
5. **Elevation data** - Add topography

### Testing Checklist:
- [ ] Satellite tiles loading (not OSM)
- [ ] Forest areas show as dark green
- [ ] Water bodies show as blue
- [ ] Grid aligns with map
- [ ] Fire doesn't cross water
- [ ] Terrain stats look reasonable

## Summary

**Main Fixes:**
1. ✅ Use satellite imagery instead of OSM rendered tiles
2. ✅ Enhanced color classification with NDVI-like vegetation detection
3. ✅ Better logging for debugging
4. ✅ Debug endpoint for testing specific locations

**Result:**
- More accurate terrain detection
- Better forest/grass identification
- Water properly classified as non-flammable
- Improved grid alignment visibility

**Test It:**
Try known locations with obvious terrain types (parks, lakes, forests) to verify the improvements!
