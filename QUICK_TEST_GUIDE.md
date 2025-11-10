# Quick Test Guide - Terrain Extraction

## Instant Test Commands

### Test 1: Forest Detection (Pacific Northwest)
```javascript
// Paste in browser console
fetch('/api/terrain/classify-grid', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        lat: 47.5, lon: -121.7,
        grid_size: 20, cell_size_degrees: 0.001
    })
}).then(r => r.json()).then(d => {
    console.log('Stats:', d.statistics.terrain_counts);
    console.log('Should see: forest as majority');
})
```

### Test 2: Water Detection (Lake Tahoe)
```javascript
fetch('/api/terrain/classify-grid', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        lat: 39.1, lon: -120.0,
        grid_size: 20, cell_size_degrees: 0.001
    })
}).then(r => r.json()).then(d => {
    console.log('Stats:', d.statistics.terrain_counts);
    console.log('Should see: water as significant portion');
})
```

### Test 3: Mixed Terrain (Central Park NYC)
```javascript
fetch('/api/terrain/classify-grid', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        lat: 40.785, lon: -73.968,
        grid_size: 20, cell_size_degrees: 0.001
    })
}).then(r => r.json()).then(d => {
    console.log('Stats:', d.statistics.terrain_counts);
    console.log('Should see: mix of grass, forest, urban');
})
```

### Test 4: Debug Single Cell
```javascript
fetch('/api/terrain/debug-cell', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        lat: 40.785, lon: -73.968
    })
}).then(r => r.json()).then(d => {
    console.log('Terrain:', d.terrain_type);
    console.log('Sample pixels:', d.sample_pixels.slice(0, 5));
})
```

## Visual Check

### In the App:
1. Select area on map
2. Click "Load Terrain"
3. **Check colors:**
   - Blue = Water ✅
   - Dark Green = Forest ✅
   - Light Green = Grass ✅
   - Gray = Urban ✅
   - Gold = Agriculture ✅

## Quick Fixes

### "No tiles downloaded"
```bash
# Wait 30 seconds, then retry
# Or reduce grid size to 10x10
```

### "Wrong terrain type"
1. Check Network tab → Look for `arcgisonline.com`
2. If only `openstreetmap.org`, satellite tiles blocked
3. Try different location

### "Grid offset from map"
1. Reload page
2. Reselect area
3. Check browser zoom is 100%

## Expected Results

| Location | Expected Dominant Terrain |
|----------|---------------------------|
| Lake Tahoe (39.1, -120.0) | water (40%+), forest (30%+) |
| Pacific NW (47.5, -121.7) | forest (60%+) |
| Central Park (40.785, -73.968) | grass (40%+), urban (30%+) |
| Iowa Farm (41.5, -88.5) | agriculture (50%+), grass (30%+) |
| Sahara (25.0, 5.0) | bare_ground (80%+) |

## Terrain Color Reference

```
Water:        #4682B4 (Steel Blue)     - Cannot burn
Urban:        #808080 (Gray)           - Very hard to burn
Forest:       #228B22 (Forest Green)   - High flammability
Grass:        #90EE90 (Light Green)    - Very high flammability
Shrub:        #9ACD32 (Yellow Green)   - Moderate-high
Agriculture:  #DAA520 (Goldenrod)      - Moderate
Bare Ground:  #D2B48C (Tan)            - Low flammability
```

## Success Criteria

✅ **Working Correctly If:**
- Forest areas show dark green
- Lakes/rivers show blue
- Cities show gray
- Fire doesn't cross water
- Grid aligns with map features

❌ **Problem If:**
- Everything shows as grass
- No blue (water) detected
- Grid appears offset
- Terrain says "unknown"
