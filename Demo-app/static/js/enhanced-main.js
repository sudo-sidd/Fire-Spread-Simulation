/**
 * Enhanced Fire Simulation App - Vector Tile Based Implementation
 * Works with OSM vector tiles and enhanced cellular automaton engine
 */

class EnhancedFireSimulationApp {
    constructor() {
        this.map = null;
        this.gridOverlay = null;
        this.fireOverlay = null;
        this.currentSimulationId = null;
        this.isSimulationRunning = false;
        this.simulationInterval = null;
        this.selectedLocation = null;
        this.terrainGrid = null;
        this.gridSize = 50;
        this.currentGridState = null;
        this.environmentalConditions = {
            temperature: 25,
            humidity: 50,
            wind_speed: 10,
            wind_direction: 'north',
            rain_probability: 0.0
        };
        
        this.init();
    }
    
    init() {
        this.initializeMap();
        this.setupEventListeners();
        this.initializeControls();
        this.updateEnvironmentalDisplay();
        
        console.log('Enhanced Fire Simulation App initialized');
    }
    
    initializeMap() {
        // Initialize Leaflet map
        this.map = L.map('worldMap').setView([39.8283, -98.5795], 4);
        
        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);
        
        // Add click handler for location selection
        this.map.on('click', (e) => {
            this.selectLocation(e.latlng.lat, e.latlng.lng);
        });
        
        // Add drawing controls for area selection
        this.initializeDrawingControls();
    }
    
    initializeDrawingControls() {
        // Rectangle selection for area
        this.drawControl = new L.Control.Draw({
            position: 'topright',
            draw: {
                polygon: false,
                circle: false,
                circlemarker: false,
                marker: false,
                polyline: false,
                rectangle: {
                    shapeOptions: {
                        color: '#ff7800',
                        weight: 2,
                        fillOpacity: 0.1
                    }
                }
            },
            edit: false
        });
        
        this.map.addControl(this.drawControl);
        
        this.map.on('draw:created', (e) => {
            const layer = e.layer;
            const bounds = layer.getBounds();
            
            // Remove previous selection
            if (this.selectionLayer) {
                this.map.removeLayer(this.selectionLayer);
            }
            
            this.selectionLayer = layer;
            this.map.addLayer(layer);
            
            // Use center of rectangle for terrain analysis
            const center = bounds.getCenter();
            this.selectLocation(center.lat, center.lng);
        });
    }
    
    setupEventListeners() {
        // Area selection button
        document.getElementById('selectAreaBtn').addEventListener('click', () => {
            if (this.selectedLocation) {
                this.loadTerrainData();
            } else {
                this.showToast('Error', 'Please select a location on the map first', 'error');
            }
        });
        
        // Simulation controls
        document.getElementById('createSimBtn').addEventListener('click', () => {
            this.createSimulation();
        });
        
        document.getElementById('startBtn').addEventListener('click', () => {
            this.toggleSimulation();
        });
        
        document.getElementById('stepBtn').addEventListener('click', () => {
            this.stepSimulation();
        });
        
        document.getElementById('resetBtn').addEventListener('click', () => {
            this.resetSimulation();
        });
        
        // Environmental controls
        document.getElementById('tempSlider').addEventListener('input', (e) => {
            this.environmentalConditions.temperature = parseInt(e.target.value);
            this.updateEnvironmentalDisplay();
            this.updateSimulationConditions();
        });
        
        document.getElementById('humiditySlider').addEventListener('input', (e) => {
            this.environmentalConditions.humidity = parseInt(e.target.value);
            this.updateEnvironmentalDisplay();
            this.updateSimulationConditions();
        });
        
        document.getElementById('windSpeedSlider').addEventListener('input', (e) => {
            this.environmentalConditions.wind_speed = parseInt(e.target.value);
            this.updateEnvironmentalDisplay();
            this.updateSimulationConditions();
        });
        
        document.getElementById('windDirection').addEventListener('change', (e) => {
            this.environmentalConditions.wind_direction = e.target.value;
            this.updateEnvironmentalDisplay();
            this.updateSimulationConditions();
        });
        
        document.getElementById('rainSlider').addEventListener('input', (e) => {
            this.environmentalConditions.rain_probability = parseFloat(e.target.value);
            this.updateEnvironmentalDisplay();
            this.updateSimulationConditions();
        });
        
        // Grid size control
        document.getElementById('gridSize').addEventListener('change', (e) => {
            this.gridSize = parseInt(e.target.value);
            document.getElementById('gridSizeDisplay').textContent = `${this.gridSize}x${this.gridSize}`;
        });
        
        // Fire ignition on grid click
        this.setupFireIgnition();
    }
    
    setupFireIgnition() {
        // Handle clicking on the grid to ignite fires
        this.map.on('click', (e) => {
            if (this.currentSimulationId && this.gridOverlay && this.terrainGrid) {
                const { row, col } = this.latLngToGridCell(e.latlng.lat, e.latlng.lng);
                if (row >= 0 && row < this.gridSize && col >= 0 && col < this.gridSize) {
                    this.igniteFireAtCell(row, col);
                }
            }
        });
    }
    
    latLngToGridCell(lat, lng) {
        if (!this.terrainGrid || !this.selectedLocation) {
            return { row: -1, col: -1 };
        }
        
        const centerLat = this.selectedLocation.lat;
        const centerLng = this.selectedLocation.lng;
        const cellSizeDegrees = 0.001;
        const halfSize = this.gridSize * cellSizeDegrees / 2;
        
        // Calculate relative position
        const relLat = lat - (centerLat - halfSize);
        const relLng = lng - (centerLng - halfSize);
        
        // Convert to grid coordinates
        const row = Math.floor(relLat / cellSizeDegrees);
        const col = Math.floor(relLng / cellSizeDegrees);
        
        return { row, col };
    }
    
    initializeControls() {
        // Initialize slider displays
        this.updateEnvironmentalDisplay();
        document.getElementById('gridSizeDisplay').textContent = `${this.gridSize}x${this.gridSize}`;
        
        // Set initial values
        document.getElementById('tempSlider').value = this.environmentalConditions.temperature;
        document.getElementById('humiditySlider').value = this.environmentalConditions.humidity;
        document.getElementById('windSpeedSlider').value = this.environmentalConditions.wind_speed;
        document.getElementById('windDirection').value = this.environmentalConditions.wind_direction;
        document.getElementById('rainSlider').value = this.environmentalConditions.rain_probability;
        document.getElementById('gridSize').value = this.gridSize;
    }
    
    updateEnvironmentalDisplay() {
        document.getElementById('tempDisplay').textContent = `${this.environmentalConditions.temperature}°C`;
        document.getElementById('humidityDisplay').textContent = `${this.environmentalConditions.humidity}%`;
        document.getElementById('windSpeedDisplay').textContent = `${this.environmentalConditions.wind_speed} km/h`;
        document.getElementById('windDirectionDisplay').textContent = this.environmentalConditions.wind_direction.toUpperCase();
        document.getElementById('rainDisplay').textContent = `${(this.environmentalConditions.rain_probability * 100).toFixed(0)}%`;
    }
    
    selectLocation(lat, lng) {
        this.selectedLocation = { lat, lng };
        
        // Remove existing marker
        if (this.locationMarker) {
            this.map.removeLayer(this.locationMarker);
        }
        
        // Add new marker
        this.locationMarker = L.marker([lat, lng]).addTo(this.map);
        
        // Update UI
        document.getElementById('selectedLocation').textContent = 
            `Selected: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        
        // Enable area selection button
        document.getElementById('selectAreaBtn').disabled = false;
        
        console.log(`Location selected: ${lat}, ${lng}`);
    }
    
    async loadTerrainData() {
        if (!this.selectedLocation) {
            this.showToast('Error', 'No location selected', 'error');
            return;
        }
        
        this.showToast('Loading', 'Analyzing terrain with satellite imagery...', 'info');
        
        try {
            // Use the NEW terrain classification API with satellite imagery
            const response = await fetch('/api/terrain/classify-grid', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    lat: this.selectedLocation.lat,
                    lon: this.selectedLocation.lng,
                    grid_size: this.gridSize,
                    cell_size_degrees: 0.001
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.terrainGrid = data.grid_classification;
                this.displayTerrainGrid(data);
                this.updateTerrainStatistics(data.statistics);
                this.showToast('Success', 'Terrain data loaded successfully', 'success');
                
                // Enable simulation creation
                document.getElementById('createSimBtn').disabled = false;
            } else {
                throw new Error(data.message || 'Failed to load terrain data');
            }
        } catch (error) {
            console.error('Error loading terrain data:', error);
            this.showToast('Error', error.message, 'error');
        }
    }
    
    displayTerrainGrid(data) {
        // Remove existing grid overlay
        if (this.gridOverlay) {
            this.map.removeLayer(this.gridOverlay);
        }
        
        // Create new grid overlay
        this.gridOverlay = L.layerGroup();
        
        const cellSizeDegrees = 0.001;
        const halfSize = this.gridSize * cellSizeDegrees / 2;
        const centerLat = this.selectedLocation.lat;
        const centerLng = this.selectedLocation.lng;
        
        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                const cell = this.terrainGrid[row][col];
                
                // Calculate cell bounds
                const cellLat = centerLat - halfSize + (row + 0.5) * cellSizeDegrees;
                const cellLng = centerLng - halfSize + (col + 0.5) * cellSizeDegrees;
                
                const bounds = [
                    [cellLat - cellSizeDegrees/2, cellLng - cellSizeDegrees/2],
                    [cellLat + cellSizeDegrees/2, cellLng + cellSizeDegrees/2]
                ];
                
                // Create rectangle for cell
                const rectangle = L.rectangle(bounds, {
                    color: cell.color,
                    fillColor: cell.color,
                    fillOpacity: 0.6,
                    weight: 0.5,
                    opacity: 0.8
                });
                
                // Add tooltip with cell info
                rectangle.bindTooltip(
                    `Terrain: ${cell.terrain_type}<br>` +
                    `Position: (${row}, ${col})<br>` +
                    `Coordinates: ${cellLat.toFixed(4)}, ${cellLng.toFixed(4)}`,
                    { permanent: false, direction: 'center' }
                );
                
                this.gridOverlay.addLayer(rectangle);
            }
        }
        
        this.gridOverlay.addTo(this.map);
        
        // Zoom to grid area
        const bounds = [
            [centerLat - halfSize, centerLng - halfSize],
            [centerLat + halfSize, centerLng + halfSize]
        ];
        this.map.fitBounds(bounds);
    }\n    \n    updateTerrainStatistics(statistics) {\n        const statsContainer = document.getElementById('terrainStats');\n        if (!statsContainer) return;\n        \n        let html = '<h4>Terrain Statistics</h4>';\n        \n        for (const [terrain, count] of Object.entries(statistics.terrain_counts)) {\n            const percentage = ((count / statistics.total_cells) * 100).toFixed(1);\n            html += `<div class=\"stat-item\">`;\n            html += `<span class=\"terrain-label\">${terrain}:</span> `;\n            html += `<span class=\"terrain-count\">${count} cells (${percentage}%)</span>`;\n            html += `</div>`;\n        }\n        \n        html += `<div class=\"stat-total\">Total: ${statistics.total_cells} cells</div>`;\n        \n        statsContainer.innerHTML = html;\n    }\n    \n    async createSimulation() {\n        if (!this.terrainGrid) {\n            this.showToast('Error', 'No terrain data available', 'error');\n            return;\n        }\n        \n        this.showToast('Creating', 'Initializing fire simulation...', 'info');\n        \n        try {\n            const response = await fetch('/api/enhanced-simulation/create', {\n                method: 'POST',\n                headers: {\n                    'Content-Type': 'application/json'\n                },\n                body: JSON.stringify({\n                    grid_classification: this.terrainGrid,\n                    grid_size: this.gridSize,\n                    environmental_conditions: this.environmentalConditions,\n                    center_lat: this.selectedLocation.lat,\n                    center_lon: this.selectedLocation.lng,\n                    cell_size_degrees: 0.001\n                })\n            });\n            \n            const data = await response.json();\n            \n            if (data.success) {\n                this.currentSimulationId = data.simulation_id;\n                this.currentGridState = null;\n                \n                this.showToast('Success', 'Fire simulation created successfully', 'success');\n                \n                // Enable simulation controls\n                this.enableSimulationControls(true);\n                \n                // Update simulation info\n                this.updateSimulationInfo(data);\n                \n                console.log('Simulation created:', data.simulation_id);\n            } else {\n                throw new Error(data.message || 'Failed to create simulation');\n            }\n        } catch (error) {\n            console.error('Error creating simulation:', error);\n            this.showToast('Error', error.message, 'error');\n        }\n    }\n    \n    enableSimulationControls(enable) {\n        document.getElementById('startBtn').disabled = !enable;\n        document.getElementById('stepBtn').disabled = !enable;\n        document.getElementById('resetBtn').disabled = !enable;\n        \n        const envControls = document.querySelectorAll('.env-control');\n        envControls.forEach(control => {\n            control.disabled = !enable;\n        });\n    }\n    \n    updateSimulationInfo(data) {\n        const infoContainer = document.getElementById('simulationInfo');\n        if (!infoContainer) return;\n        \n        let html = '<h4>Simulation Status</h4>';\n        html += `<div>ID: ${this.currentSimulationId}</div>`;\n        html += `<div>Grid Size: ${data.grid_size}x${data.grid_size}</div>`;\n        html += `<div>Status: ${this.isSimulationRunning ? 'Running' : 'Paused'}</div>`;\n        \n        if (data.initial_statistics) {\n            html += `<div>Total Cells: ${data.initial_statistics.total_cells}</div>`;\n            html += `<div>Unburned: ${data.initial_statistics.unburned}</div>`;\n            html += `<div>Burning: ${data.initial_statistics.burning}</div>`;\n            html += `<div>Burned: ${data.initial_statistics.burned}</div>`;\n        }\n        \n        infoContainer.innerHTML = html;\n    }\n    \n    async igniteFireAtCell(row, col, intensity = 1.0) {\n        if (!this.currentSimulationId) {\n            this.showToast('Error', 'No active simulation', 'error');\n            return;\n        }\n        \n        try {\n            const response = await fetch('/api/enhanced-simulation/ignite', {\n                method: 'POST',\n                headers: {\n                    'Content-Type': 'application/json'\n                },\n                body: JSON.stringify({\n                    simulation_id: this.currentSimulationId,\n                    row: row,\n                    col: col,\n                    intensity: intensity\n                })\n            });\n            \n            const data = await response.json();\n            \n            if (data.success) {\n                this.currentGridState = data.grid_state;\n                this.updateFireVisualization();\n                this.updateSimulationStats(data.statistics);\n                \n                this.showToast('Fire Ignited', `Fire started at grid cell (${row}, ${col})`, 'success');\n            } else {\n                this.showToast('Ignition Failed', data.message, 'warning');\n            }\n        } catch (error) {\n            console.error('Error igniting fire:', error);\n            this.showToast('Error', error.message, 'error');\n        }\n    }\n    \n    updateFireVisualization() {\n        if (!this.currentGridState) return;\n        \n        // Remove existing fire overlay\n        if (this.fireOverlay) {\n            this.map.removeLayer(this.fireOverlay);\n        }\n        \n        this.fireOverlay = L.layerGroup();\n        \n        const cellSizeDegrees = 0.001;\n        const halfSize = this.gridSize * cellSizeDegrees / 2;\n        const centerLat = this.selectedLocation.lat;\n        const centerLng = this.selectedLocation.lng;\n        \n        for (let row = 0; row < this.gridSize; row++) {\n            for (let col = 0; col < this.gridSize; col++) {\n                const cell = this.currentGridState[row][col];\n                \n                if (cell.burn_state !== 'unburned') {\n                    const cellLat = centerLat - halfSize + (row + 0.5) * cellSizeDegrees;\n                    const cellLng = centerLng - halfSize + (col + 0.5) * cellSizeDegrees;\n                    \n                    const bounds = [\n                        [cellLat - cellSizeDegrees/2, cellLng - cellSizeDegrees/2],\n                        [cellLat + cellSizeDegrees/2, cellLng + cellSizeDegrees/2]\n                    ];\n                    \n                    let color, fillOpacity;\n                    \n                    if (cell.burn_state === 'burning') {\n                        // Burning cells - red to orange based on intensity\n                        const intensity = cell.burn_intensity;\n                        color = `rgba(255, ${Math.floor(165 * (1 - intensity))}, 0, 0.8)`;\n                        fillOpacity = 0.7 + (intensity * 0.3);\n                    } else if (cell.burn_state === 'burned') {\n                        // Burned cells - dark gray/black\n                        color = 'rgba(64, 64, 64, 0.8)';\n                        fillOpacity = 0.6;\n                    }\n                    \n                    const fireRect = L.rectangle(bounds, {\n                        color: color,\n                        fillColor: color,\n                        fillOpacity: fillOpacity,\n                        weight: 1,\n                        opacity: 0.9\n                    });\n                    \n                    fireRect.bindTooltip(\n                        `Status: ${cell.burn_state}<br>` +\n                        `Intensity: ${(cell.burn_intensity * 100).toFixed(1)}%<br>` +\n                        `Duration: ${cell.burn_duration}<br>` +\n                        `Fuel: ${(cell.fuel_load * 100).toFixed(1)}%<br>` +\n                        `Moisture: ${(cell.moisture * 100).toFixed(1)}%`,\n                        { permanent: false, direction: 'center' }\n                    );\n                    \n                    this.fireOverlay.addLayer(fireRect);\n                }\n            }\n        }\n        \n        this.fireOverlay.addTo(this.map);\n    }\n    \n    updateSimulationStats(statistics) {\n        const statsContainer = document.getElementById('simulationStats');\n        if (!statsContainer) return;\n        \n        let html = '<h4>Fire Statistics</h4>';\n        html += `<div class=\"stat-item\">Unburned: ${statistics.unburned} cells</div>`;\n        html += `<div class=\"stat-item\">Burning: ${statistics.burning} cells</div>`;\n        html += `<div class=\"stat-item\">Burned: ${statistics.burned} cells</div>`;\n        html += `<div class=\"stat-item\">Average Intensity: ${(statistics.avg_intensity * 100).toFixed(1)}%</div>`;\n        html += `<div class=\"stat-item\">Average Temperature: ${statistics.avg_temperature.toFixed(1)}°C</div>`;\n        html += `<div class=\"stat-item\">Fuel Remaining: ${(statistics.fuel_remaining * 100).toFixed(1)}%</div>`;\n        \n        statsContainer.innerHTML = html;\n    }\n    \n    async toggleSimulation() {\n        if (this.isSimulationRunning) {\n            this.stopSimulation();\n        } else {\n            this.startSimulation();\n        }\n    }\n    \n    startSimulation() {\n        if (!this.currentSimulationId) {\n            this.showToast('Error', 'No active simulation', 'error');\n            return;\n        }\n        \n        this.isSimulationRunning = true;\n        document.getElementById('startBtn').textContent = 'Pause';\n        \n        // Run simulation steps automatically\n        this.simulationInterval = setInterval(() => {\n            this.stepSimulation();\n        }, 1000); // 1 step per second\n        \n        this.showToast('Started', 'Fire simulation is now running', 'success');\n    }\n    \n    stopSimulation() {\n        this.isSimulationRunning = false;\n        document.getElementById('startBtn').textContent = 'Start';\n        \n        if (this.simulationInterval) {\n            clearInterval(this.simulationInterval);\n            this.simulationInterval = null;\n        }\n        \n        this.showToast('Paused', 'Fire simulation paused', 'info');\n    }\n    \n    async stepSimulation(steps = 1) {\n        if (!this.currentSimulationId) {\n            this.showToast('Error', 'No active simulation', 'error');\n            return;\n        }\n        \n        try {\n            const response = await fetch('/api/enhanced-simulation/step', {\n                method: 'POST',\n                headers: {\n                    'Content-Type': 'application/json'\n                },\n                body: JSON.stringify({\n                    simulation_id: this.currentSimulationId,\n                    steps: steps\n                })\n            });\n            \n            const data = await response.json();\n            \n            if (data.success) {\n                this.currentGridState = data.grid_state;\n                this.updateFireVisualization();\n                this.updateSimulationStats(data.statistics);\n                \n                // Stop simulation if no more active fires\n                if (!data.is_active && this.isSimulationRunning) {\n                    this.stopSimulation();\n                    this.showToast('Complete', 'Fire simulation has ended', 'info');\n                }\n                \n                console.log(`Simulation step ${data.current_tick}: ${data.statistics.burning} burning cells`);\n            } else {\n                throw new Error(data.message || 'Failed to step simulation');\n            }\n        } catch (error) {\n            console.error('Error stepping simulation:', error);\n            this.showToast('Error', error.message, 'error');\n        }\n    }\n    \n    async resetSimulation() {\n        if (!this.currentSimulationId) {\n            this.showToast('Error', 'No active simulation', 'error');\n            return;\n        }\n        \n        // Stop if running\n        if (this.isSimulationRunning) {\n            this.stopSimulation();\n        }\n        \n        try {\n            const response = await fetch('/api/enhanced-simulation/reset', {\n                method: 'POST',\n                headers: {\n                    'Content-Type': 'application/json'\n                },\n                body: JSON.stringify({\n                    simulation_id: this.currentSimulationId\n                })\n            });\n            \n            const data = await response.json();\n            \n            if (data.success) {\n                this.currentGridState = data.grid_state;\n                this.updateFireVisualization();\n                this.updateSimulationStats(data.statistics);\n                \n                this.showToast('Reset', 'Simulation reset to initial state', 'success');\n            } else {\n                throw new Error(data.message || 'Failed to reset simulation');\n            }\n        } catch (error) {\n            console.error('Error resetting simulation:', error);\n            this.showToast('Error', error.message, 'error');\n        }\n    }\n    \n    async updateSimulationConditions() {\n        if (!this.currentSimulationId) return;\n        \n        try {\n            const response = await fetch('/api/enhanced-simulation/update-conditions', {\n                method: 'POST',\n                headers: {\n                    'Content-Type': 'application/json'\n                },\n                body: JSON.stringify({\n                    simulation_id: this.currentSimulationId,\n                    conditions: this.environmentalConditions\n                })\n            });\n            \n            const data = await response.json();\n            \n            if (!data.success) {\n                console.error('Failed to update environmental conditions:', data.error);\n            }\n        } catch (error) {\n            console.error('Error updating environmental conditions:', error);\n        }\n    }\n    \n    showToast(title, message, type = 'info') {\n        // Simple toast notification\n        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();\n        \n        const toast = document.createElement('div');\n        toast.className = `toast toast-${type}`;\n        toast.innerHTML = `\n            <strong>${title}</strong><br>\n            ${message}\n        `;\n        \n        toastContainer.appendChild(toast);\n        \n        // Auto-remove after 3 seconds\n        setTimeout(() => {\n            if (toast.parentNode) {\n                toast.parentNode.removeChild(toast);\n            }\n        }, 3000);\n    }\n    \n    createToastContainer() {\n        const container = document.createElement('div');\n        container.id = 'toastContainer';\n        container.style.cssText = `\n            position: fixed;\n            top: 20px;\n            right: 20px;\n            z-index: 1000;\n        `;\n        document.body.appendChild(container);\n        return container;\n    }\n}\n\n// Initialize the application when the page loads\ndocument.addEventListener('DOMContentLoaded', () => {\n    window.fireSimApp = new EnhancedFireSimulationApp();\n});
