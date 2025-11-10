# 🔥 HOW TO SEE THE CHANGES

## Quick Start (3 Steps)

### Step 1: Restart the Server
```bash
cd /home/zoryu/projects/Fire-Spread-Simulation/Demo-app

# Kill old server
pkill -f "python.*app.py"

# Start fresh
./start.sh
# OR
python app.py
```

### Step 2: Open Test Page
Open your browser to:
```
http://localhost:5000/test
```

This test page will verify:
- ✅ Water cannot burn (cellular automata fix)
- ✅ Satellite imagery is being used
- ✅ Terrain classification is working

### Step 3: Run Tests
Click the test buttons on the test page to verify changes are working!

---

## Alternative: Manual Testing

### Open Main App
```
http://localhost:5000/
```

### Test Water Cannot Burn:
1. Select a location with water (e.g., Lake Tahoe: 39.1, -120.0)
2. Click "Load Terrain Data"
3. Look for **blue cells** (water) in the grid
4. Click "Create Simulation"
5. Try to click on a blue water cell
6. Fire should **NOT ignite** on water ✅

### Test Terrain Classification:
1. Open browser DevTools (F12)
2. Go to Network tab
3. Click "Load Terrain Data"
4. Look for requests to:
   - ✅ `server.arcgisonline.com` (satellite imagery - GOOD!)
   - ❌ Only `tile.openstreetmap.org` (rendered maps - old behavior)

---

## Verify Changes in Code

### Check Cellular Automata:
```bash
grep -n "is_flammable" Demo-app/core/cellular_automata_engine.py
```
Should show lines with `'is_flammable': False` for water

### Check Satellite Imagery:
```bash
grep -n "arcgisonline" Demo-app/services/map_tile_service.py
```
Should show ESRI World Imagery URL

---

## Common Issues

### "I don't see the test page"
- Make sure server is running
- Check http://localhost:5000/health first
- Then try http://localhost:5000/test

### "Server not starting"
```bash
# Check if port 5000 is in use
lsof -i :5000

# Kill it if needed
pkill -f "python.*app.py"

# Start again
python app.py
```

### "Changes not showing up"
1. Hard refresh browser: Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. Clear browser cache
3. Restart Flask server
4. Check you're editing files in `/Demo-app/` not elsewhere

---

## What Should You See?

### ✅ Cellular Automata Fixes Working:
- Water cells show as **blue** (#4682B4)
- Clicking water cells shows "Cannot ignite" message
- Fire does NOT spread across water boundaries
- Different terrain types have different burn rates

### ✅ Terrain Extraction Fixes Working:
- Terrain classification completes in 4-8 seconds
- Forest areas show as **dark green**
- Water bodies show as **blue**
- Grid aligns with map features
- Statistics show realistic terrain distribution

### ❌ If NOT Working:
- All cells show as grass/green
- Fire spreads across water
- "Unknown" terrain types
- Grid appears offset
- Takes too long to load

---

## Test Locations

### Lake Tahoe (Water Test)
```
Lat: 39.1
Lon: -120.0
Expected: 30-50% water cells
```

### Central Park NYC (Mixed Terrain)
```
Lat: 40.785
Lon: -73.968
Expected: Mix of grass, forest, urban
```

### Pacific Northwest (Forest)
```
Lat: 47.5
Lon: -121.7
Expected: 60%+ forest
```

---

## Files That Were Changed

1. **Demo-app/core/cellular_automata_engine.py**
   - Added `is_flammable` property
   - Enhanced ignition checks
   - Terrain-specific thresholds

2. **Demo-app/services/map_tile_service.py**
   - Satellite imagery (ESRI)
   - Better color classification
   - Enhanced logging

3. **Demo-app/api/terrain_api.py**
   - Added debug endpoint

4. **Demo-app/app.py**
   - Added /test route

5. **Demo-app/templates/test.html**
   - New test page (just created!)

---

## Need More Help?

### Check Logs:
```bash
# Server logs show what's happening
# Look for:
# - "Downloaded X tiles at zoom level 16"
# - "Terrain distribution: {...}"
# - "Cell at (lat, lon): ... result: forest"
```

### Debug Mode:
The server runs in debug mode - any Python changes should auto-reload.
If not working, restart manually.

### Browser Console:
Open DevTools → Console to see JavaScript errors or network issues
