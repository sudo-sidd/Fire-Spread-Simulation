#!/bin/bash

echo "================================"
echo "Fire Spread Simulation - Startup"
echo "================================"
echo ""
echo "✓ Cellular Automata Fixes Applied:"
echo "  - Water cannot burn (is_flammable: False)"
echo "  - Terrain-specific ignition thresholds"
echo "  - Enhanced fire spread calculations"
echo ""
echo "✓ Terrain Extraction Fixes Applied:"
echo "  - Satellite imagery (ESRI World Imagery)"
echo "  - Enhanced color classification"
echo "  - Better vegetation detection"
echo ""
echo "Starting Flask server on http://localhost:5000"
echo "================================"
echo ""

# Set Python to unbuffered mode for better logging
export PYTHONUNBUFFERED=1

# Run the app
python app.py
