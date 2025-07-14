# Fire Spread Simulation Web Application

A professional web application for simulating fire spread on real-world terrain using cellular automata and interactive map selection.

## Features

### 🗺️ Interactive Map Selection
- Click anywhere on the world map to select simulation area
- Search locations by address or coordinates
- Real-time terrain extraction from satellite imagery
- Support for various terrain types (forest, grass, urban, water, etc.)

### 🔥 Advanced Fire Simulation
- Cellular automata-based fire spread modeling
- Real terrain data integration
- Weather condition effects (wind, humidity, temperature)
- Multiple fire ignition points
- Real-time visualization with fire effects

### 🌦️ Weather System
- Adjustable wind speed and direction
- Humidity and temperature controls
- Precipitation effects on fire behavior
- Visual wind direction indicator

### 📊 Real-time Statistics
- Active burning cells count
- Total burned area (km²)
- Simulation step tracking
- Fire spread analytics

### 🎮 Simulation Controls
- Play/pause simulation
- Single-step execution
- Adjustable simulation speed
- Reset functionality
- Export simulation data

## Installation

### Prerequisites
- **Python 3.11 or higher** - Required for optimal performance and compatibility

1. **Clone the repository**
   ```bash
   cd /mnt/data/PROJECTS/Fire-Spread-Simulation-/web-fire-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up directories**
   ```bash
   mkdir -p temp data static/images
   ```

4. **Install Chrome/Chromium** (for terrain extraction)
   ```bash
   # Ubuntu/Debian
   sudo apt-get install chromium-browser
   
   # Or install Google Chrome from official source
   ```

## Running the Application

1. **Start the development server**
   ```bash
   python app.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5000`

3. **For production deployment**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

## Usage Guide

### 1. Select Location
- **Map Selection**: Click anywhere on the world map
- **Search**: Use the search box to find specific locations
- **Coordinates**: Enter latitude/longitude manually
- **Extract Terrain**: Click "Select Area" to process the location

### 2. Start Fire Simulation
- **Ignite Fire**: Click on the terrain map to start fires
- **Multiple Points**: Click multiple locations for complex scenarios
- **Weather**: Adjust wind, humidity, and temperature settings

### 3. Control Simulation
- **Play**: Start automatic simulation progression
- **Step**: Advance simulation manually one step at a time
- **Speed**: Adjust simulation speed (1-10 scale)
- **Reset**: Return to initial terrain state

### 4. Monitor Progress
- **Statistics**: Real-time fire spread metrics
- **Visualization**: Color-coded fire states and terrain
- **Export**: Download simulation data as JSON

## Terrain Types and Colors

| Terrain Type | Color | Fire Behavior |
|-------------|-------|---------------|
| 🌲 Forest | Dark Green | High fuel load, medium spread |
| 🌾 Grass | Light Green | Medium fuel load, fast spread |
| 🏘️ Urban | Gray | Low fuel load, slow spread |
| 🌊 Water | Blue | No fuel, fire barrier |
| 🌾 Agriculture | Gold | Medium fuel load, medium spread |
| 🌿 Shrub | Olive | Medium fuel load, medium spread |
| 🏔️ Bare Ground | Brown | Very low fuel load, very slow spread |

## Fire States

| State | Color | Description |
|-------|-------|-------------|
| Normal | Terrain Color | Unburned vegetation/terrain |
| 🔥 Burning | Bright Red | Active fire |
| ⚫ Burned | Dark Gray | Completely burned out |
| 🟠 Smoldering | Orange | Dying fire |

## API Endpoints

### Map API (`/api/map/`)
- `POST /select-area` - Extract terrain from coordinates
- `GET /geocode` - Convert address to coordinates
- `GET /nearby-features` - Get geographic features

### Simulation API (`/api/simulation/`)
- `POST /create` - Create new simulation
- `POST /ignite` - Start fire at coordinates
- `POST /step` - Advance simulation
- `POST /weather` - Update weather conditions
- `POST /reset` - Reset simulation
- `GET /status/<id>` - Get simulation status
- `GET /export/<id>` - Export simulation data

### Terrain API (`/api/terrain/`)
- `POST /extract` - Extract terrain bitmap
- `POST /analyze` - Analyze terrain composition
- `GET /presets` - Get terrain presets

## Configuration

Edit `core/config.py` to customize:

- **Grid size**: Simulation resolution
- **Fire parameters**: Spread probability, burn time
- **Terrain types**: Add new terrain categories
- **Colors**: Customize visualization colors
- **Weather**: Default weather conditions

## Architecture

```
web-fire-app/
├── app.py                 # Flask application entry point
├── requirements.txt       # Python dependencies
├── core/                  # Core simulation engine
│   ├── config.py         # Configuration settings
│   └── fire_engine.py    # Fire simulation logic
├── api/                   # REST API endpoints
│   ├── map_api.py        # Map and location services
│   ├── simulation_api.py # Simulation control
│   └── terrain_api.py    # Terrain processing
├── services/              # Business logic services
│   ├── terrain_service.py # Terrain extraction
│   └── visualization_service.py # Image processing
├── utils/                 # Utility functions
│   └── helpers.py        # Common utilities
├── static/                # Frontend assets
│   ├── css/main.css      # Stylesheets
│   └── js/main.js        # JavaScript application
└── templates/             # HTML templates
    └── index.html        # Main application page
```

## Technology Stack

### Backend
- **Flask** - Web framework
- **NumPy** - Numerical computing
- **Pillow** - Image processing
- **Selenium** - Web scraping for maps
- **Folium** - Map generation

### Frontend
- **Leaflet** - Interactive maps
- **Bootstrap 5** - UI framework
- **Font Awesome** - Icons
- **Vanilla JavaScript** - Application logic

### Visualization
- **HTML5 Canvas** - Fire simulation rendering
- **CSS3 Animations** - Visual effects
- **WebGL** - Hardware acceleration (future)

## Performance Optimization

### Server-side
- Simulation state caching
- Efficient numpy operations
- Background processing for terrain extraction
- Memory management for large simulations

### Client-side
- Canvas-based rendering
- Debounced user interactions
- Progressive image loading
- Optimized animation loops

## Deployment

### Development
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

### Production
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Using Docker
docker build -t fire-sim-app .
docker run -p 8000:8000 fire-sim-app
```

### Environment Variables
- `FLASK_ENV` - Environment (development/production)
- `SECRET_KEY` - Flask secret key
- `DEBUG` - Enable debug mode

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

This project is part of the Fire Spread Simulation research project.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Submit an issue on GitHub

## Roadmap

### Planned Features
- [ ] Real weather data integration
- [ ] 3D visualization mode
- [ ] Historical fire data overlay
- [ ] Multi-user collaboration
- [ ] Mobile app version
- [ ] Machine learning fire prediction
- [ ] Emergency response integration

### Performance Improvements
- [ ] WebGL rendering
- [ ] Worker threads for simulation
- [ ] Progressive mesh loading
- [ ] Real-time collaboration
- [ ] Offline mode support
