/**
 * Fire Spread Simulation - Main JavaScript Application
 */

class FireSimulationApp {
    constructor() {
        this.map = null;
        this.gridOverlay = null;
        this.fireOverlay = null;
        this.currentSimulationId = null;
        this.isSimulationRunning = false;
        this.simulationInterval = null;
        this.selectedLocation = null;
        this.terrainData = null;
        this.gridSize = 50; // 50x50 grid cells
        this.selectedBounds = null;
        
        this.init();
    }
    
    init() {
        this.initializeMap();
        this.setupEventListeners();
        this.initializeControls();
        
        console.log('Fire Simulation App initialized');
    }
    
    initializeMap() {
        // Initialize Leaflet map
        this.map = L.map('worldMap').setView([39.8283, -98.5795], 4);
        
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(this.map);
        
        // Add click handler for location selection
        this.map.on('click', (e) => {
            this.selectLocation(e.latlng.lat, e.latlng.lng);
        });
    }
    
    async createGridOverlay(lat, lon) {
        // Show loading indicator
        this.showToast('Loading', 'Analyzing terrain from satellite imagery...', 'info');
        
        // Calculate grid parameters
        const cellSizeDegrees = 0.001; // Approximately 100m at equator
        const rows = this.gridSize;
        const cols = this.gridSize;
        
        // Calculate bounds
        const halfLat = (cellSizeDegrees * rows) / 2;
        const halfLon = (cellSizeDegrees * cols) / 2;
        
        this.selectedBounds = {
            north: lat + halfLat,
            south: lat - halfLat,
            east: lon + halfLon,
            west: lon - halfLon
        };
        
        try {
            // Get terrain classification from real map tiles
            const response = await fetch('/api/terrain/classify-grid', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lat: lat,
                    lon: lon,
                    grid_size: this.gridSize,
                    cell_size_degrees: cellSizeDegrees
                })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.message || 'Failed to classify terrain');
            }
            
            console.log('Terrain classification completed:', data.statistics);
            
            // Create grid cells with real terrain classification
            this.gridCells = [];
            this.terrainStatistics = data.statistics;
            this.legendColors = data.legend_colors;
            
            for (let row = 0; row < rows; row++) {
                this.gridCells[row] = [];
                for (let col = 0; col < cols; col++) {
                    const cellData = data.grid_classification[row][col];
                    const cellLat = cellData.lat;
                    const cellLon = cellData.lon;
                    
                    const bounds = [
                        [cellLat - cellSizeDegrees/2, cellLon - cellSizeDegrees/2],
                        [cellLat + cellSizeDegrees/2, cellLon + cellSizeDegrees/2]
                    ];
                    
                    const cell = L.rectangle(bounds, {
                        fillColor: cellData.color,
                        fillOpacity: 0.7,
                        color: '#000',
                        weight: 0.3,
                        className: 'grid-cell'
                    });
                    
                    // Store cell data
                    cell.gridRow = row;
                    cell.gridCol = col;
                    cell.terrainType = cellData.terrain_type;
                    cell.fireState = 'normal'; // normal, burning, burned
                    cell.originalColor = cellData.color;
                    
                    // Add click handler for fire ignition
                    cell.on('click', (e) => {
                        if (this.currentSimulationId) {
                            this.igniteFireAtGridCell(row, col);
                        }
                        L.DomEvent.stopPropagation(e);
                    });
                    
                    // Add hover effects
                    cell.on('mouseover', (e) => {
                        e.target.setStyle({
                            weight: 2,
                            fillOpacity: 0.9
                        });
                    });
                    
                    cell.on('mouseout', (e) => {
                        if (e.target.fireState === 'normal') {
                            e.target.setStyle({
                                weight: 0.3,
                                fillOpacity: 0.7
                            });
                        }
                    });
                    
                    // Add tooltip with terrain info
                    cell.bindTooltip(
                        `Terrain: ${cellData.terrain_type}<br>` +
                        `Grid: (${row}, ${col})<br>` +
                        `Click to ignite fire`,
                        {
                            permanent: false,
                            direction: 'top'
                        }
                    );
                    
                    this.gridCells[row][col] = cell;
                }
            }
            
            // Create layer group for grid
            this.gridOverlay = L.layerGroup(this.gridCells.flat()).addTo(this.map);
            
            // Add boundary rectangle
            this.boundaryRect = L.rectangle([
                [this.selectedBounds.south, this.selectedBounds.west],
                [this.selectedBounds.north, this.selectedBounds.east]
            ], {
                fillOpacity: 0,
                color: '#ff0000',
                weight: 3,
                dashArray: '10, 10'
            }).addTo(this.map);
            
            // Fit map to grid
            this.map.fitBounds([
                [this.selectedBounds.south, this.selectedBounds.west],
                [this.selectedBounds.north, this.selectedBounds.east]
            ]);
            
            // Update terrain legend
            this.updateTerrainLegend(data.statistics, this.legendColors);
            
            this.showToast('Success', 'Terrain analysis completed!', 'success');
            
        } catch (error) {
            console.error('Error creating grid overlay:', error);
            this.showToast('Error', `Failed to analyze terrain: ${error.message}`, 'error');
            
            // Fallback to synthetic terrain
            this.createSyntheticGridOverlay(lat, lon, cellSizeDegrees);
        }
    }
    
    createSyntheticGridOverlay(lat, lon, cellSizeDegrees) {
        // Fallback synthetic terrain generation
        console.log('Creating synthetic grid overlay as fallback');
        
        const rows = this.gridSize;
        const cols = this.gridSize;
        
        // Simple terrain colors
        const terrainColors = {
            'forest': '#228B22',
            'grass': '#90EE90',
            'urban': '#808080',
            'water': '#4682B4',
            'agriculture': '#DAA520',
            'shrub': '#9ACD32',
            'bare_ground': '#D2B48C'
        };
        
        this.gridCells = [];
        
        for (let row = 0; row < rows; row++) {
            this.gridCells[row] = [];
            for (let col = 0; col < cols; col++) {
                const cellLat = this.selectedBounds.south + (row + 0.5) * cellSizeDegrees;
                const cellLon = this.selectedBounds.west + (col + 0.5) * cellSizeDegrees;
                
                const bounds = [
                    [cellLat - cellSizeDegrees/2, cellLon - cellSizeDegrees/2],
                    [cellLat + cellSizeDegrees/2, cellLon + cellSizeDegrees/2]
                ];
                
                // Determine synthetic terrain type
                const terrainType = this.determineTerrainType(row, col);
                
                const cell = L.rectangle(bounds, {
                    fillColor: terrainColors[terrainType],
                    fillOpacity: 0.7,
                    color: '#000',
                    weight: 0.3,
                    className: 'grid-cell'
                });
                
                // Store cell data
                cell.gridRow = row;
                cell.gridCol = col;
                cell.terrainType = terrainType;
                cell.fireState = 'normal';
                cell.originalColor = terrainColors[terrainType];
                
                // Add click handler for fire ignition
                cell.on('click', (e) => {
                    if (this.currentSimulationId) {
                        this.igniteFireAtGridCell(row, col);
                    }
                    L.DomEvent.stopPropagation(e);
                });
                
                // Add tooltip
                cell.bindTooltip(
                    `Terrain: ${terrainType}<br>Grid: (${row}, ${col})<br>Click to ignite fire`,
                    { permanent: false, direction: 'top' }
                );
                
                this.gridCells[row][col] = cell;
            }
        }
        
        // Create layer group for grid
        this.gridOverlay = L.layerGroup(this.gridCells.flat()).addTo(this.map);
        
        this.legendColors = terrainColors;
        this.showToast('Notice', 'Using synthetic terrain data', 'warning');
    }
    
    classifyGridCells(terrainData) {
        // Apply terrain classification to grid cells based on the terrain bitmap
        if (!terrainData || !terrainData.color_map) return;
        
        // Convert color map
        const colorMap = {};
        for (const [colorStr, terrainType] of Object.entries(terrainData.color_map)) {
            colorMap[terrainType] = colorStr;
        }
        
        // Terrain colors mapping
        const terrainColors = {
            'forest': '#228B22',      // Forest green
            'grass': '#90EE90',       // Light green
            'urban': '#808080',       // Gray
            'water': '#4682B4',       // Steel blue
            'agriculture': '#DAA520',  // Goldenrod
            'shrub': '#9ACD32',       // Yellow green
            'bare_ground': '#D2B48C'   // Tan
        };
        
        // Randomly assign terrain types based on geographic logic
        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                const cell = this.gridCells[row][col];
                
                // Use some geographic logic for terrain assignment
                let terrainType = this.determineTerrainType(row, col);
                
                cell.terrainType = terrainType;
                cell.setStyle({
                    fillColor: terrainColors[terrainType] || '#90EE90',
                    fillOpacity: 0.7
                });
                
                // Add tooltip with terrain info
                cell.bindTooltip(`Terrain: ${terrainType}<br>Grid: (${row}, ${col})`, {
                    permanent: false,
                    direction: 'top'
                });
            }
        }
    }
    
    determineTerrainType(row, col) {
        // Simple geographic-based terrain determination
        const centerRow = this.gridSize / 2;
        const centerCol = this.gridSize / 2;
        const distanceFromCenter = Math.sqrt((row - centerRow)**2 + (col - centerCol)**2);
        
        // Random factor
        const random = Math.random();
        
        // Water bodies (rivers, lakes) - more likely in certain patterns
        if (random < 0.08 && (col % 10 < 2 || row % 15 < 2)) {
            return 'water';
        }
        
        // Urban areas - more likely in center
        if (distanceFromCenter < this.gridSize * 0.2 && random < 0.15) {
            return 'urban';
        }
        
        // Forest - random patches
        if (random < 0.4) {
            return 'forest';
        }
        
        // Agriculture - in middle distances
        if (distanceFromCenter > this.gridSize * 0.2 && distanceFromCenter < this.gridSize * 0.4 && random < 0.7) {
            return 'agriculture';
        }
        
        // Shrubland
        if (random < 0.8) {
            return 'shrub';
        }
        
        // Default to grass
        return 'grass';
    }
    
    async igniteFireAtGridCell(row, col) {
        if (!this.currentSimulationId) return;
        
        try {
            const response = await fetch('/api/simulation/ignite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulation_id: this.currentSimulationId,
                    x: col,
                    y: row
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateGridVisualization(data.visualization);
                this.updateStatistics(data.statistics);
                this.showToast('Fire Started', `Ignited at grid (${row}, ${col})`, 'warning');
            } else {
                this.showToast('Ignition Failed', data.message, 'error');
            }
        } catch (error) {
            this.showToast('Error', error.message, 'error');
        }
    }
    
    updateGridVisualization(visualizationData) {
        // Update grid cells based on fire simulation state
        if (!visualizationData || !this.gridCells) return;
        
        // If visualization data is base64 image, we need to parse it into grid states
        // For now, we'll simulate the fire spread visually on the grid
        // In a full implementation, the backend would return grid state data
        
        // Placeholder: update some cells to show fire spread
        // This should be replaced with actual fire state data from the backend
        console.log('Updating grid visualization with:', visualizationData);
    }
    
    updateFireStatesFromSimulation() {
        // This method should be called after each simulation step
        // to update the grid cell colors based on fire states
        if (!this.currentSimulationId || !this.gridCells) return;
        
        // Get fire state data from backend
        this.getSimulationFireStates().then(fireStates => {
            if (fireStates) {
                this.updateGridWithFireStates(fireStates);
            } else {
                // Fallback to visual fire spread simulation
                this.simulateFireSpreadOnGrid();
            }
        });
    }
    
    async getSimulationFireStates() {
        // Get current fire states from the simulation backend
        try {
            const response = await fetch(`/api/simulation/${this.currentSimulationId}/state`);
            const data = await response.json();
            
            if (data.success && data.fire_states) {
                return data.fire_states;
            }
        } catch (error) {
            console.log('Could not get fire states from backend:', error.message);
        }
        
        return null;
    }
    
    updateGridWithFireStates(fireStates) {
        // Update grid cells based on actual simulation fire states
        const fireColors = {
            'normal': null, // Use original terrain color
            'burning': '#FF4500', // Orange red
            'burned': '#2F2F2F'   // Dark gray
        };
        
        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                if (!this.gridCells[row] || !this.gridCells[row][col]) continue;
                
                const cell = this.gridCells[row][col];
                const fireState = fireStates[row] && fireStates[row][col] ? 
                                fireStates[row][col] : 'normal';
                
                cell.fireState = fireState;
                
                if (fireState === 'normal') {
                    // Use original terrain color
                    cell.setStyle({
                        fillColor: cell.originalColor,
                        fillOpacity: 0.7
                    });
                } else {
                    // Use fire state color
                    cell.setStyle({
                        fillColor: fireColors[fireState],
                        fillOpacity: 0.9
                    });
                }
                
                // Update tooltip
                const terrainType = cell.terrainType;
                cell.setTooltipContent(
                    `Terrain: ${terrainType}<br>` +
                    `Fire State: ${fireState}<br>` +
                    `Grid: (${row}, ${col})<br>` +
                    (fireState === 'normal' ? 'Click to ignite fire' : '')
                );
            }
        }
    }
    
    simulateFireSpreadOnGrid() {
        // Simple visual fire spread simulation for demonstration
        // This should be replaced with actual backend fire state data
        
        const fireColors = {
            'normal': null, // Use terrain color
            'burning': '#FF4500', // Orange red
            'burned': '#2F2F2F'   // Dark gray
        };
        
        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                const cell = this.gridCells[row][col];
                
                if (cell.fireState === 'burning') {
                    // Chance to burn out
                    if (Math.random() < 0.1) {
                        cell.fireState = 'burned';
                        cell.setStyle({
                            fillColor: fireColors.burned,
                            fillOpacity: 0.8
                        });
                    }
                    
                    // Spread to neighbors
                    this.spreadFireToNeighbors(row, col);
                } else if (cell.fireState === 'normal' && cell.terrainType !== 'water') {
                    // Check if fire should start from burning neighbors
                    if (this.hasFireNeighbor(row, col) && Math.random() < 0.05) {
                        cell.fireState = 'burning';
                        cell.setStyle({
                            fillColor: fireColors.burning,
                            fillOpacity: 0.9
                        });
                    }
                }
            }
        }
    }
    
    spreadFireToNeighbors(row, col) {
        const directions = [[-1,-1], [-1,0], [-1,1], [0,-1], [0,1], [1,-1], [1,0], [1,1]];
        
        for (const [dr, dc] of directions) {
            const newRow = row + dr;
            const newCol = col + dc;
            
            if (newRow >= 0 && newRow < this.gridSize && newCol >= 0 && newCol < this.gridSize) {
                const neighborCell = this.gridCells[newRow][newCol];
                
                if (neighborCell.fireState === 'normal' && 
                    neighborCell.terrainType !== 'water' && 
                    neighborCell.terrainType !== 'urban' &&
                    Math.random() < 0.1) {
                    
                    neighborCell.fireState = 'burning';
                    neighborCell.setStyle({
                        fillColor: '#FF4500',
                        fillOpacity: 0.9
                    });
                }
            }
        }
    }
    
    hasFireNeighbor(row, col) {
        const directions = [[-1,-1], [-1,0], [-1,1], [0,-1], [0,1], [1,-1], [1,0], [1,1]];
        
        for (const [dr, dc] of directions) {
            const newRow = row + dr;
            const newCol = col + dc;
            
            if (newRow >= 0 && newRow < this.gridSize && newCol >= 0 && newCol < this.gridSize) {
                const neighborCell = this.gridCells[newRow][newCol];
                if (neighborCell.fireState === 'burning') {
                    return true;
                }
            }
        }
        return false;
    }
    
    setupEventListeners() {
        // Location controls
        document.getElementById('searchBtn').addEventListener('click', () => this.searchLocation());
        document.getElementById('selectAreaBtn').addEventListener('click', () => this.selectCurrentArea());
        
        // Simulation controls
        document.getElementById('randomIgniteBtn').addEventListener('click', () => this.startRandomFires());
        document.getElementById('playBtn').addEventListener('click', () => this.startSimulation());
        document.getElementById('pauseBtn').addEventListener('click', () => this.pauseSimulation());
        document.getElementById('stepBtn').addEventListener('click', () => this.stepSimulation());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetSimulation());
        
        // Weather controls
        document.getElementById('updateWeatherBtn').addEventListener('click', () => this.updateWeather());
        
        // Weather sliders
        this.setupWeatherSliders();
        
        // Other controls
        document.getElementById('toggleMapBtn').addEventListener('click', () => this.toggleMapVisibility());
        document.getElementById('exportBtn').addEventListener('click', () => this.exportSimulation());
        
        // Enter key for search
        document.getElementById('addressInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchLocation();
        });
    }
    
    setupWeatherSliders() {
        const sliders = [
            { id: 'windSpeed', valueId: 'windSpeedValue', suffix: ' km/h' },
            { id: 'windDirection', valueId: 'windDirectionValue', suffix: '°' },
            { id: 'humidity', valueId: 'humidityValue', suffix: '%' },
            { id: 'temperature', valueId: 'temperatureValue', suffix: '°C' }
        ];
        
        sliders.forEach(slider => {
            const element = document.getElementById(slider.id);
            const valueElement = document.getElementById(slider.valueId);
            
            element.addEventListener('input', (e) => {
                valueElement.textContent = e.target.value + slider.suffix;
                
                // Update wind indicator for wind direction
                if (slider.id === 'windDirection') {
                    this.updateWindIndicator(e.target.value);
                }
            });
        });
    }
    
    updateWindIndicator(direction) {
        const indicator = document.getElementById('windIndicator');
        if (indicator) {
            indicator.style.transform = `translate(-50%, -50%) rotate(${direction}deg)`;
        }
    }
    
    initializeControls() {
        // Disable simulation controls initially
        this.setSimulationControlsEnabled(false);
    }
    
    selectLocation(lat, lon) {
        // Update input fields
        document.getElementById('latInput').value = lat.toFixed(4);
        document.getElementById('lonInput').value = lon.toFixed(4);
        
        // Store selected location
        this.selectedLocation = { lat, lon };
        
        // Add marker to map
        if (this.locationMarker) {
            this.map.removeLayer(this.locationMarker);
        }
        
        this.locationMarker = L.marker([lat, lon]).addTo(this.map);
        this.map.setView([lat, lon], 12);
        
        this.showToast('Location selected', 'Click "Select Area" to extract terrain data', 'success');
    }
    
    async searchLocation() {
        const address = document.getElementById('addressInput').value.trim();
        if (!address) return;
        
        this.showLoading('Searching location...', 'Finding coordinates for the specified address');
        
        try {
            const response = await fetch(`/api/map/geocode?address=${encodeURIComponent(address)}`);
            const data = await response.json();
            
            if (data.success) {
                this.selectLocation(data.coordinates.lat, data.coordinates.lon);
                this.hideLoading();
            } else {
                throw new Error(data.error || 'Geocoding failed');
            }
        } catch (error) {
            this.hideLoading();
            this.showToast('Search Error', error.message, 'error');
        }
    }
    
    async selectCurrentArea() {
        const lat = parseFloat(document.getElementById('latInput').value);
        const lon = parseFloat(document.getElementById('lonInput').value);
        
        if (isNaN(lat) || isNaN(lon)) {
            this.showToast('Invalid Coordinates', 'Please enter valid latitude and longitude', 'error');
            return;
        }

        console.log('=== STARTING TERRAIN EXTRACTION ===');
        console.log(`Coordinates: lat=${lat}, lon=${lon}`);
        console.log(`Grid size: ${this.gridSize}`);
        
        this.showLoading('Extracting Terrain...', 'Processing satellite imagery and generating terrain data');
        
        try {
            console.log('Making API call to /api/map/select-area...');
            const response = await fetch('/api/map/select-area', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    lat: lat,
                    lon: lon,
                    zoom: 15,
                    grid_size: [this.gridSize, this.gridSize]
                })
            });
            
            console.log('API response received:', response.status, response.statusText);
            const data = await response.json();
            console.log('API response data:', data);
            
            console.log('Terrain API response:', {
                success: data.success,
                hasGridClassification: !!data.grid_classification,
                hasLegendColors: !!data.legend_colors,
                gridSize: data.statistics?.grid_size,
                totalCells: data.statistics?.total_cells
            });
            
            if (data.success) {
                console.log('Success response received, setting terrainData...');
                this.terrainData = data;
                
                console.log('Creating 2D grid overlay from classification...');
                // Create 2D grid overlay using the grid classification
                this.create2DGridOverlay(data, lat, lon);
                
                console.log('Creating simulation...');
                // Create simulation
                await this.createSimulation();
                
                console.log('Hiding loading and showing success toast...');
                this.hideLoading();
                this.showToast('2D Grid Created', 'Click on grid cells to start fires', 'success');
                console.log('=== 2D GRID CREATION COMPLETED SUCCESSFULLY ===');
            } else {
                console.error('API returned error:', data.error);
                throw new Error(data.error || 'Failed to create 2D grid');
            }
        } catch (error) {
            console.error('Error in selectCurrentArea:', error);
            this.hideLoading();
            this.showToast('Terrain Error', error.message, 'error');
        }
    }
    
    async createSimulation() {
        try {
            const response = await fetch('/api/simulation/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    width: this.gridSize,
                    height: this.gridSize,
                    terrain_data: {
                        bitmap: this.terrainData.terrain_image,
                        color_map: this.terrainData.color_map
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentSimulationId = data.simulation_id;
                this.setSimulationControlsEnabled(true);
                console.log('Simulation created:', data.simulation_id);
            } else {
                throw new Error(data.error || 'Failed to create simulation');
            }
        } catch (error) {
            this.showToast('Simulation Error', error.message, 'error');
        }
    }
    
    displayTerrain(terrainImageBase64) {
        console.log('Displaying terrain image:', terrainImageBase64 ? 'Image data received' : 'No image data');
        
        const img = new Image();
        img.onload = () => {
            console.log('Terrain image loaded successfully');
            this.simulationContext.clearRect(0, 0, this.simulationCanvas.width, this.simulationCanvas.height);
            this.simulationContext.drawImage(img, 0, 0, this.simulationCanvas.width, this.simulationCanvas.height);
            console.log('Terrain drawn to canvas');
        };
        
        img.onerror = (error) => {
            console.error('Failed to load terrain image:', error);
            this.showToast('Image Error', 'Failed to load terrain image', 'error');
            
            // Draw a placeholder pattern
            this.drawPlaceholderTerrain();
        };
        
        if (terrainImageBase64) {
            img.src = terrainImageBase64;
        } else {
            console.error('No terrain image data provided');
            this.drawPlaceholderTerrain();
        }
    }
    
    drawPlaceholderTerrain() {
        // Draw a simple placeholder terrain pattern
        const ctx = this.simulationContext;
        const width = this.simulationCanvas.width;
        const height = this.simulationCanvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Draw grid pattern
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 1;
        
        for (let x = 0; x < width; x += 20) {
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();
        }
        
        for (let y = 0; y < height; y += 20) {
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }
        
        // Add text
        ctx.fillStyle = '#666';
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('Terrain Loading...', width/2, height/2);
        
        console.log('Placeholder terrain drawn');
    }
    
    showSimulationView() {
        console.log('Switching to simulation view');
        document.getElementById('worldMap').style.display = 'none';
        document.getElementById('simulationOverlay').style.display = 'block';
        
        // Ensure canvas is properly sized
        this.resizeCanvas();
        
        console.log('Canvas dimensions:', {
            width: this.simulationCanvas.width,
            height: this.simulationCanvas.height,
            clientWidth: this.simulationCanvas.clientWidth,
            clientHeight: this.simulationCanvas.clientHeight
        });
    }
    
    async igniteFireAtCanvasPoint(event) {
        if (!this.currentSimulationId) return;
        
        const rect = this.simulationCanvas.getBoundingClientRect();
        const x = Math.floor((event.clientX - rect.left) / rect.width * 200);
        const y = Math.floor((event.clientY - rect.top) / rect.height * 200);
        
        try {
            const response = await fetch('/api/simulation/ignite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulation_id: this.currentSimulationId,
                    x: x,
                    y: y
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayVisualization(data.visualization);
                this.updateStatistics(data.statistics);
                this.showToast('Fire Started', `Ignited at (${x}, ${y})`, 'warning');
            } else {
                this.showToast('Ignition Failed', data.message, 'error');
            }
        } catch (error) {
            this.showToast('Error', error.message, 'error');
        }
    }
    
    async startSimulation() {
        if (!this.currentSimulationId || this.isSimulationRunning) return;
        
        this.isSimulationRunning = true;
        this.updateSimulationButtons();
        
        const speed = document.getElementById('speedSlider').value;
        const interval = 1100 - (speed * 100); // Convert speed to milliseconds
        
        this.simulationInterval = setInterval(() => {
            this.stepSimulation();
        }, interval);
        
        document.body.classList.add('simulation-active');
    }
    
    pauseSimulation() {
        this.isSimulationRunning = false;
        if (this.simulationInterval) {
            clearInterval(this.simulationInterval);
            this.simulationInterval = null;
        }
        this.updateSimulationButtons();
        document.body.classList.remove('simulation-active');
    }
    
    async stepSimulation() {
        if (!this.currentSimulationId) return;
        
        try {
            const response = await fetch('/api/simulation/step', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulation_id: this.currentSimulationId,
                    steps: 1
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateGridVisualization(data.visualization);
                this.updateStatistics(data.statistics);
                
                // Also update our visual fire simulation on the grid
                this.updateFireStatesFromSimulation();
                
                // Stop simulation if no more active fires
                if (!data.statistics.is_active && this.isSimulationRunning) {
                    this.pauseSimulation();
                    this.showToast('Simulation Complete', 'No more active fires', 'success');
                }
            }
        } catch (error) {
            this.showToast('Step Error', error.message, 'error');
        }
    }
    
    async resetSimulation() {
        if (!this.currentSimulationId) return;
        
        this.pauseSimulation();
        
        try {
            const response = await fetch('/api/simulation/reset', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulation_id: this.currentSimulationId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateGridVisualization(data.visualization);
                this.updateStatistics(data.statistics);
                
                // Reset all grid cells to their original terrain state
                this.resetGridCells();
                
                this.showToast('Simulation Reset', 'Ready to start new fires', 'success');
            }
        } catch (error) {
            this.showToast('Reset Error', error.message, 'error');
        }
    }
    
    resetGridCells() {
        if (!this.gridCells) return;
        
        // Reset all cells to normal state with terrain colors
        const terrainColors = {
            'forest': '#228B22',      // Forest green
            'grass': '#90EE90',       // Light green
            'urban': '#808080',       // Gray
            'water': '#4682B4',       // Steel blue
            'agriculture': '#DAA520',  // Goldenrod
            'shrub': '#9ACD32',       // Yellow green
            'bare_ground': '#D2B48C'   // Tan
        };
        
        for (let row = 0; row < this.gridSize; row++) {
            for (let col = 0; col < this.gridSize; col++) {
                const cell = this.gridCells[row][col];
                cell.fireState = 'normal';
                cell.setStyle({
                    fillColor: terrainColors[cell.terrainType] || '#90EE90',
                    fillOpacity: 0.7
                });
            }
        }
    }
    
    async updateWeather() {
        if (!this.currentSimulationId) return;
        
        const weather = {
            wind_speed: parseFloat(document.getElementById('windSpeed').value),
            wind_direction: parseFloat(document.getElementById('windDirection').value),
            humidity: parseFloat(document.getElementById('humidity').value),
            temperature: parseFloat(document.getElementById('temperature').value),
            precipitation: 0 // TODO: Add precipitation control
        };
        
        try {
            const response = await fetch('/api/simulation/weather', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulation_id: this.currentSimulationId,
                    ...weather
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Weather Updated', 'New conditions applied to simulation', 'success');
            }
        } catch (error) {
            this.showToast('Weather Error', error.message, 'error');
        }
    }
    
    displayVisualization(imageBase64) {
        const img = new Image();
        img.onload = () => {
            this.simulationContext.clearRect(0, 0, this.simulationCanvas.width, this.simulationCanvas.height);
            this.simulationContext.drawImage(img, 0, 0, this.simulationCanvas.width, this.simulationCanvas.height);
        };
        img.src = imageBase64;
    }
    
    updateStatistics(stats) {
        document.getElementById('burningCells').textContent = stats.burning_cells || 0;
        document.getElementById('burnedCells').textContent = stats.burned_cells || 0;
        document.getElementById('currentStep').textContent = stats.step || 0;
        document.getElementById('burnedArea').textContent = (stats.total_burned_area_km2 || 0).toFixed(3);
    }
    
    setSimulationControlsEnabled(enabled) {
        const controls = ['playBtn', 'pauseBtn', 'stepBtn', 'resetBtn'];
        controls.forEach(id => {
            document.getElementById(id).disabled = !enabled;
        });
    }
    
    updateSimulationButtons() {
        document.getElementById('playBtn').disabled = this.isSimulationRunning;
        document.getElementById('pauseBtn').disabled = !this.isSimulationRunning;
    }
    
    toggleMapVisibility() {
        const worldMap = document.getElementById('worldMap');
        const isVisible = worldMap.style.display !== 'none';
        
        if (isVisible) {
            worldMap.style.display = 'none';
            document.getElementById('toggleMapBtn').innerHTML = '<i class=\"fas fa-eye\"></i> Show Map';
        } else {
            worldMap.style.display = 'block';
            document.getElementById('toggleMapBtn').innerHTML = '<i class=\"fas fa-eye-slash\"></i> Hide Map';
        }
    }
    
    async exportSimulation() {
        if (!this.currentSimulationId) {
            this.showToast('Export Error', 'No active simulation to export', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/simulation/export/${this.currentSimulationId}`);
            const data = await response.json();
            
            if (data.success) {
                // Download as JSON file
                const blob = new Blob([JSON.stringify(data.export_data, null, 2)], {
                    type: 'application/json'
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `fire_simulation_${this.currentSimulationId}.json`;
                a.click();
                URL.revokeObjectURL(url);
                
                this.showToast('Export Complete', 'Simulation data downloaded', 'success');
            }
        } catch (error) {
            this.showToast('Export Error', error.message, 'error');
        }
    }
    
    showLoading(title, subtitle) {
        document.getElementById('loadingText').textContent = title;
        document.getElementById('loadingSubtext').textContent = subtitle;
        
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }
    
    hideLoading() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (modal) modal.hide();
    }
    
    showToast(title, message, type = 'info') {
        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="toast-header">
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        `;
        
        container.appendChild(toast);
        
        // Show toast
        const bsToast = new bootstrap.Toast(toast, { delay: 5000 });
        bsToast.show();
        
        // Remove from DOM after hide
        toast.addEventListener('hidden.bs.toast', () => {
            container.removeChild(toast);
        });
    }
    
    updateTerrainLegend(statistics, legendColors) {
        // Update the terrain legend panel
        const legendPanel = document.getElementById('terrain-legend');
        if (!legendPanel) return;
        
        let legendHTML = '<h4>Terrain Classification</h4>';
        
        // Add terrain type statistics
        if (statistics && statistics.terrain_percentages) {
            legendHTML += '<div class="terrain-stats">';
            
            for (const [terrainType, percentage] of Object.entries(statistics.terrain_percentages)) {
                const color = legendColors[terrainType] || '#888888';
                const count = statistics.terrain_counts[terrainType] || 0;
                
                legendHTML += `
                    <div class="terrain-legend-item">
                        <span class="terrain-color-box" style="background-color: ${color}"></span>
                        <span class="terrain-name">${terrainType.replace('_', ' ')}</span>
                        <span class="terrain-percentage">${percentage.toFixed(1)}%</span>
                        <span class="terrain-count">(${count} cells)</span>
                    </div>
                `;
            }
            
            legendHTML += '</div>';
        }
        
        // Add fire state legend
        legendHTML += `
            <h5>Fire States</h5>
            <div class="fire-legend">
                <div class="fire-legend-item">
                    <span class="fire-color-box" style="background-color: #FF4500"></span>
                    <span>Burning</span>
                </div>
                <div class="fire-legend-item">
                    <span class="fire-color-box" style="background-color: #2F2F2F"></span>
                    <span>Burned</span>
                </div>
            </div>
        `;
        
        legendPanel.innerHTML = legendHTML;
        legendPanel.style.display = 'block';
    }
    
    create2DGridOverlay(responseData, centerLat, centerLon) {
        console.log('Creating 2D grid overlay from classification data...');
        
        // Clear existing overlays
        if (this.gridOverlay) {
            this.map.removeLayer(this.gridOverlay);
        }
        if (this.boundaryRect) {
            this.map.removeLayer(this.boundaryRect);
        }
        
        const gridClassification = responseData.grid_classification;
        const legendColors = responseData.legend_colors;
        const gridBounds = responseData.grid_bounds;
        const gridSize = responseData.statistics.grid_size;
        
        console.log(`Creating ${gridSize}x${gridSize} grid with bounds:`, gridBounds);
        
        // Initialize grid cells array
        this.gridCells = [];
        this.terrainStatistics = responseData.statistics;
        this.legendColors = legendColors;
        
        // Set selected bounds for map fitting
        this.selectedBounds = gridBounds;
        
        // Create grid cells from classification data
        for (let row = 0; row < gridSize; row++) {
            this.gridCells[row] = [];
            for (let col = 0; col < gridSize; col++) {
                const cellData = gridClassification[row][col];
                const cellLat = cellData.lat;
                const cellLon = cellData.lon;
                const cellSizeDegrees = responseData.metadata.cell_size_degrees;
                
                // Calculate cell bounds
                const bounds = [
                    [cellLat - cellSizeDegrees/2, cellLon - cellSizeDegrees/2],
                    [cellLat + cellSizeDegrees/2, cellLon + cellSizeDegrees/2]
                ];
                
                // Create rectangle for this cell
                const cell = L.rectangle(bounds, {
                    fillColor: cellData.color,
                    fillOpacity: 0.7,
                    color: '#000',
                    weight: 0.3,
                    className: 'grid-cell'
                });
                
                // Store cell data
                cell.gridRow = row;
                cell.gridCol = col;
                cell.terrainType = cellData.terrain_type;
                cell.fireState = 'normal'; // normal, burning, burned
                cell.originalColor = cellData.color;
                
                // Add click handler for fire ignition
                cell.on('click', (e) => {
                    if (this.currentSimulationId) {
                        this.igniteFireAtGridCell(row, col);
                    }
                    L.DomEvent.stopPropagation(e);
                });
                
                // Add hover effects
                cell.on('mouseover', (e) => {
                    e.target.setStyle({
                        weight: 2,
                        fillOpacity: 0.9
                    });
                });
                
                cell.on('mouseout', (e) => {
                    if (e.target.fireState === 'normal') {
                        e.target.setStyle({
                            weight: 0.3,
                            fillOpacity: 0.7
                        });
                    }
                });
                
                // Add tooltip with terrain info
                cell.bindTooltip(
                    `Terrain: ${cellData.terrain_type}<br>` +
                    `Grid: (${row}, ${col})<br>` +
                    `Coordinates: (${cellLat.toFixed(4)}, ${cellLon.toFixed(4)})<br>` +
                    `Click to ignite fire`,
                    {
                        permanent: false,
                        direction: 'top'
                    }
                );
                
                this.gridCells[row][col] = cell;
            }
        }
        
        // Create layer group for grid overlay
        this.gridOverlay = L.layerGroup(this.gridCells.flat()).addTo(this.map);
        
        // Add boundary rectangle
        this.boundaryRect = L.rectangle([
            [gridBounds.south, gridBounds.west],
            [gridBounds.north, gridBounds.east]
        ], {
            fillOpacity: 0,
            color: '#ff0000',
            weight: 3,
            dashArray: '10, 10'
        }).addTo(this.map);
        
        // Fit map to grid bounds
        this.map.fitBounds([
            [gridBounds.south, gridBounds.west],
            [gridBounds.north, gridBounds.east]
        ]);
        
        // Update terrain legend
        this.updateTerrainLegend(responseData.statistics, legendColors);
        
        console.log('2D Grid overlay created successfully!');
        console.log(`Grid contains ${gridSize}x${gridSize} = ${responseData.statistics.total_cells} cells`);
        console.log('Terrain distribution:', responseData.statistics.terrain_percentages);
    }
    
    async startRandomFires() {
        if (!this.currentSimulationId) {
            this.showToast('Error', 'No simulation area selected. Please select an area first.', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/simulation/random-ignite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    simulation_id: this.currentSimulationId,
                    num_ignitions: 3, // Start 3 random fires
                    ignition_probability: 0.02 // 2% chance per flammable cell as fallback
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.updateGridVisualization(data.visualization);
                this.updateStatistics(data.statistics);
                this.showToast('Random Fires Started', 
                    `Successfully ignited ${data.ignited_count} fires in ${data.flammable_cells} flammable areas`, 
                    'warning');
                
                // Enable simulation controls since fires are now active
                this.updateSimulationButtons();
            } else {
                this.showToast('Failed to Start Fires', data.message, 'error');
            }
        } catch (error) {
            this.showToast('Error', error.message, 'error');
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.fireSimApp = new FireSimulationApp();
});
