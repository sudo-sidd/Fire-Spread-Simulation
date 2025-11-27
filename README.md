# Fire Spread Simulation - with cellular automata
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green)](https://flask.palletsprojects.com/)

A wildfire simulation experiment developed for a hackathon, exploring different approaches to fire spread modeling - from basic cellular automata implementations to interactive web applications with real-world data integration.

## Demo Video

<video width="100%" controls>
  <source src="./assets/firesim.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

*Full demo video showing the interactive web application in action*

## Project Overview

This hackathon project experiments with various fire simulation techniques and implementations. The journey progressed from simple 2D cellular automata models to a fully-featured web application with real terrain data and weather integration.

## Experimental Modules

### 1. Basic Cellular Automata Implementation (`CA_implementation/`)

**Purpose:** Initial proof-of-concept for fire spread using cellular automata

**Technology:** Python + Pygame

**Features:**

- Simple grid-based fire propagation
- Mouse-click fire ignition
- Real-time visualization
- Basic reset functionality

**Key Learning:** Understanding fundamental cellular automata rules for fire spread modeling

### 2. 3D Visualization Experiments (`3d-forest-fire-simulation/`)

**Purpose:** Explore 3D rendering approaches for fire simulation

**Multiple Implementations:**

- **`main_software3d.py`** - Software-based 3D rendering (most successful)
- **`main_voxel.py`** - Matplotlib 3D voxel visualization
- **`main_opengl.py`** - Pure OpenGL implementation (graphics driver issues)
- **`main_3d.py`** - Ursina engine approach
- **`main_headless.py`** - 2D matplotlib fallback

**Key Challenge:** Graphics compatibility across different systems led to multiple rendering approaches

### 3. Real-World Data Integration (`Datasets/`)

**Purpose:** Incorporate actual meteorological and terrain data

**Components:**

- **ERA5 Weather Data (`ERA5.py`)** - Fetching real weather conditions from ECMWF
- **Land Use/Land Cover (`LULC-script.py`)** - Satellite-based terrain classification
- **Terrain Extraction (`TerrainExtract/`)** - Digital elevation model processing

**Key Innovation:** Moving from synthetic data to real-world conditions for more accurate modeling

## Final Web Application (`Demo-app/`)

The culmination of all experiments - a professional web application that combines all learnings into an interactive platform.

### Core Features

#### Interactive Map Selection

- Click anywhere on the world map to select simulation area
- Search locations by address or coordinates
- Real-time terrain extraction from satellite imagery
- Support for various terrain types (forest, grass, urban, water)

#### Advanced Fire Simulation Engine

- Cellular automata-based fire spread modeling
- Real terrain data integration with elevation
- Multiple fire ignition points support
- Configurable fire behavior parameters

#### Weather System Integration

- Adjustable wind speed and direction with visual indicators
- Humidity and temperature controls
- Precipitation effects on fire behavior
- Real-time weather data from ERA5 datasets

#### Real-time Analytics

- Active burning cells count and total burned area
- Simulation step tracking and spread rate analysis
- Fire intensity heatmaps and progression statistics

### Technical Architecture

```text
Demo-app/
├── api/                           # RESTful API endpoints
│   ├── map_api.py                # Interactive map endpoints
│   ├── simulation_api.py         # Basic fire simulation
│   ├── enhanced_simulation_api.py # Advanced features
│   └── terrain_api.py            # Terrain data processing
│
├── core/                         # Simulation engines
│   ├── cellular_automata_engine.py # CA simulation logic
│   ├── fire_engine.py             # Fire behavior modeling
│   └── config.py                  # Global configuration
│
├── services/                     # Data processing services
│   ├── map_tile_service.py       # Map tile processing
│   ├── terrain_service.py        # Elevation & terrain
│   ├── vector_tile_service.py    # Vector data handling
│   └── visualization_service.py  # Rendering pipeline
│
├── static/ & templates/          # Frontend assets
│   ├── js/enhanced-main.js       # Interactive UI
│   ├── css/main.css             # Styling
│   └── index.html               # Main interface
│
└── app.py                       # Flask application entry point
```

## Quick Setup

### Run the Web Application

```bash
cd Demo-app
pip install -r requirements.txt
python app.py
```

Access at: [http://localhost:5000](http://localhost:5000)

### Try the Experiments

```bash
# Basic 2D cellular automata
cd "pre-demo tests/CA_implementation"
python main.py

# 3D visualization (recommended version)
cd "pre-demo tests/3d-forest-fire-simulation"
python main_software3d.py

# Data extraction experiments
cd "pre-demo tests/Datasets"
python ERA5.py
```

## Technical Highlights

### Cellular Automata Implementation

- Moore neighborhood (8-cell) fire spread calculation
- State transitions: Empty → Tree → Burning → Burned
- Environmental factors: wind direction, humidity, temperature
- Probabilistic spread based on conditions

### Real-Time Data Processing

- Live terrain extraction from mapping services
- Weather data integration from ERA5 datasets
- Slope-based fire acceleration using digital elevation models
- Land cover classification for fire behavior coefficients

### Performance Optimizations

- Vectorized NumPy operations for cellular automata
- Efficient Canvas API rendering
- Asynchronous data fetching
- Memory management for large simulation grids

## Project Structure

```text
Fire-Spread-Simulation/
├── Demo-app/                    # Main web application
├── pre-demo tests/             # Experimental modules
│   ├── 3d-forest-fire-simulation/
│   ├── CA_implementation/
│   ├── Datasets/
│   └── TerrainExtract/
├── assets/                     # Demo video and media
└── README.md
```

## Hackathon Learnings

This project demonstrates the evolution from simple concepts to a complex system:

1. **Started simple** - Basic cellular automata with Pygame
2. **Explored alternatives** - Multiple 3D rendering approaches to handle compatibility issues
3. **Added realism** - Real-world data integration for accurate modeling
4. **Built for users** - Professional web interface for interactive simulation

The final web application successfully combines cellular automata theory, real-world data processing, and modern web technologies into a functional fire simulation platform.

---

Built for hackathon experimentation and learning
