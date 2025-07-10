#!/usr/bin/env python3
"""
Forest Fire Simulation with Real Terrain Data
=============================================

This script integrates real-world terrain data extraction with cellular automata-based
forest fire simulation. It uses the TerrianExtract module to get land cover data from
satellite imagery and the CA-implementation module to simulate fire spread.

Author: AI Assistant
Date: June 26, 2025
"""

import pygame
import numpy as np
import sys
import os

# Add module paths for local packages
# sys.path.append(os.path.join(os.path.dirname(__file__), "TerrianExtract"))
# sys.path.append(os.path.join(os.path.dirname(__file__), "CA-implementation"))

# Import our modules
try:
    # Import TerrainExtractor
    from TerrianExtract.main import TerrainExtractor
    
    # Import CA implementation modules
    from CA_implementation.simulation.fire_model import FireModel
    from CA_implementation.graphics.renderer import Renderer
    from CA_implementation.utils.config import GRID_SIZE, CELL_SIZE, FPS
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all modules are in the correct directories.")
    print("Required modules:")
    print("  - TerrianExtract/main.py (TerrainExtractor class)")
    print("  - CA-implementation/simulation/fire_model.py (FireModel class)")
    print("  - CA-implementation/graphics/renderer.py (Renderer class)")
    print("  - CA-implementation/utils/config.py (configuration constants)")
    sys.exit(1)


class ForestFireSimulation:
    """Main simulation class that integrates terrain extraction and fire simulation."""
    
    def __init__(self):
        self.terrain_extractor = TerrainExtractor()
        self.fire_model = None
        self.renderer = None
        self.screen = None
        self.clock = None
        self.terrain_grid = None
        self.lat = None
        self.lon = None
        self.radius = None
        
        # Color mapping for different cell states
        self.colors = {
            0: (139, 69, 19),    # Brown for empty/dirt
            1: (0, 128, 0),      # Green for trees
            2: (255, 0, 0),      # Red for burning
            3: (64, 64, 64)      # Dark gray for burned
        }
    
    def get_user_input(self):
        """Get coordinates and radius from user input."""
        print("=" * 60)
        print("🔥 FOREST FIRE SIMULATION WITH REAL TERRAIN DATA 🔥")
        print("=" * 60)
        print("\nThis simulation will:")
        print("1. Extract real terrain data from satellite imagery")
        print("2. Convert land cover data to forest grid")
        print("3. Simulate fire spread using cellular automata")
        print("\nEnter location details:")
        
        try:
            # Example coordinates for different regions
            print("\nExample locations:")
            print("  - Delhi, India: 28.6139, 77.2090")
            print("  - California, USA: 36.7783, -119.4179")
            print("  - Amazon, Brazil: -3.4653, -62.2159")
            print("  - Siberia, Russia: 60.0000, 105.0000")
            
            self.lat = float(input("\nEnter latitude: "))
            self.lon = float(input("Enter longitude: "))
            self.radius = float(input("Enter radius in kilometers (recommend 1-5): "))
            
            print(f"\n✓ Location set: {self.lat:.4f}, {self.lon:.4f}")
            print(f"✓ Radius: {self.radius} km")
            return True
            
        except ValueError:
            print("❌ Invalid input. Please enter numeric values.")
            return self.get_user_input()
        except KeyboardInterrupt:
            print("\n\n👋 Simulation cancelled by user.")
            return False
    
    def extract_terrain_data(self):
        """Extract terrain data using TerrainExtractor."""
        print(f"\n📡 Extracting terrain data...")
        print(f"   Location: {self.lat:.4f}, {self.lon:.4f}")
        print(f"   Radius: {self.radius} km")
        print("   This may take 30-60 seconds...")
        
        try:
            # Set location
            self.terrain_extractor.set_location(self.lat, self.lon)
            
            # Extract land cover matrix
            land_cover_matrix = self.terrain_extractor.extract_land_cover_matrix(
                radius_km=self.radius,
                save_plot=True,
                plot_filename=f'terrain_{self.lat}_{self.lon}_{self.radius}km.png'
            )
            
            print(f"✅ Successfully extracted terrain data")
            print(f"   Matrix shape: {land_cover_matrix.shape}")
            return land_cover_matrix
            
        except Exception as e:
            print(f"❌ Failed to extract terrain data: {e}")
            print("   Using default random forest instead...")
            return None
    
    def convert_land_cover_to_forest_grid(self, land_cover_matrix, target_size=None):
        """
        Convert land cover matrix to forest grid for fire simulation.
        
        ESA WorldCover classes:
        - 10: Tree cover (Forest) -> becomes trees (1)
        - 20: Shrubland -> becomes trees (1) with lower density
        - 30: Grassland -> becomes empty (0)
        - 40: Cropland -> becomes empty (0)
        - 50: Built-up -> becomes empty (0)
        - 60: Bare/sparse vegetation -> becomes empty (0)
        - 70: Snow and ice -> becomes empty (0)
        - 80: Permanent water bodies -> becomes empty (0)
        - 90: Herbaceous wetland -> becomes empty (0)
        - 95: Mangroves -> becomes trees (1)
        - 100: Moss and lichen -> becomes empty (0)
        """
        if target_size is None:
            target_size = GRID_SIZE
        
        print(f"🔄 Converting land cover to {target_size}x{target_size} forest grid...")
        
        # Simple resize using numpy interpolation
        original_height, original_width = land_cover_matrix.shape
        
        # Create indices for resampling
        y_indices = np.linspace(0, original_height - 1, target_size).astype(int)
        x_indices = np.linspace(0, original_width - 1, target_size).astype(int)
        
        # Resample the matrix
        resized_matrix = land_cover_matrix[np.ix_(y_indices, x_indices)]
        
        # Convert to forest grid based on land cover classes
        forest_grid = []
        tree_count = 0
        
        for y in range(target_size):
            row = []
            for x in range(target_size):
                land_cover_class = resized_matrix[y][x]
                
                # Map land cover classes to forest states
                if land_cover_class == 10:  # Tree cover/Forest
                    row.append(1)  # Tree
                    tree_count += 1
                elif land_cover_class == 20:  # Shrubland (50% chance of tree)
                    if np.random.random() < 0.5:
                        row.append(1)  # Tree
                        tree_count += 1
                    else:
                        row.append(0)  # Empty
                elif land_cover_class == 95:  # Mangroves
                    row.append(1)  # Tree
                    tree_count += 1
                else:  # All other classes become empty
                    row.append(0)  # Empty
            
            forest_grid.append(row)
        
        tree_percentage = (tree_count / (target_size * target_size)) * 100
        print(f"✅ Conversion complete!")
        print(f"   Trees: {tree_count}/{target_size*target_size} cells ({tree_percentage:.1f}%)")
        
        # If too few trees, add some randomly
        if tree_percentage < 5:
            print("⚠️  Very few trees detected. Adding random trees for better simulation...")
            for y in range(target_size):
                for x in range(target_size):
                    if forest_grid[y][x] == 0 and np.random.random() < 0.3:
                        forest_grid[y][x] = 1
                        tree_count += 1
            
            new_percentage = (tree_count / (target_size * target_size)) * 100
            print(f"   Updated trees: {tree_count} ({new_percentage:.1f}%)")
        
        return forest_grid
    
    def create_fire_model_with_terrain(self, terrain_grid=None):
        """Create fire model with terrain data."""
        self.fire_model = FireModel(GRID_SIZE, GRID_SIZE)
        
        if terrain_grid is not None:
            # Use terrain data
            self.fire_model.grid = terrain_grid
            print("✅ Fire model initialized with real terrain data")
        else:
            # Use default random forest
            print("✅ Fire model initialized with default random forest")
        
        return self.fire_model
    
    def initialize_pygame(self):
        """Initialize pygame and create display."""
        pygame.init()
        
        # Create display
        self.screen = pygame.display.set_mode((GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE))
        title = f"Forest Fire Simulation - {self.lat:.4f}, {self.lon:.4f} ({self.radius}km)"
        pygame.display.set_caption(title)
        
        # Create clock and renderer
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen, CELL_SIZE, self.colors)
        
        print("✅ Pygame initialized")
    
    def start_initial_fire(self):
        """Start initial fire in the simulation."""
        center_x, center_y = GRID_SIZE // 2, GRID_SIZE // 2
        
        # Try to start fire at center
        if self.fire_model.grid[center_y][center_x] == 1:
            self.fire_model.ignite(center_x, center_y)
            print(f"🔥 Initial fire started at center ({center_x}, {center_y})")
            return True
        
        # Find the first tree and start fire there
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.fire_model.grid[y][x] == 1:
                    self.fire_model.ignite(x, y)
                    print(f"🔥 Initial fire started at ({x}, {y})")
                    return True
        
        print("❌ No trees found for initial fire!")
        return False
    
    def print_controls(self):
        """Print simulation controls."""
        print("\n" + "=" * 50)
        print("🎮 SIMULATION CONTROLS")
        print("=" * 50)
        print("🖱️  Left click    : Start fire at mouse position")
        print("⌨️  R key        : Reset simulation")
        print("⌨️  ESC key      : Exit simulation")
        print("⌨️  SPACE key    : Pause/unpause simulation")
        print("🖥️  Close window : Exit simulation")
        print("⏰ Simulation runs automatically at", FPS, "FPS")
        print("=" * 50)
    
    def run_simulation(self):
        """Main simulation loop."""
        if not self.get_user_input():
            return
        
        # Extract terrain data
        land_cover_matrix = self.extract_terrain_data()
        
        # Convert to forest grid
        if land_cover_matrix is not None:
            try:
                self.terrain_grid = self.convert_land_cover_to_forest_grid(land_cover_matrix)
            except Exception as e:
                print(f"❌ Failed to convert terrain data: {e}")
                self.terrain_grid = None
        
        # Initialize simulation components
        self.initialize_pygame()
        self.create_fire_model_with_terrain(self.terrain_grid)
        
        # Start initial fire
        if not self.start_initial_fire():
            print("❌ Cannot start simulation without trees!")
            pygame.quit()
            return
        
        # Print controls
        self.print_controls()
        
        # Simulation state
        running = True
        paused = False
        
        print("\n🚀 Starting simulation...")
        
        # Main simulation loop
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    elif event.key == pygame.K_r:
                        # Reset simulation
                        self.create_fire_model_with_terrain(self.terrain_grid)
                        self.start_initial_fire()
                        paused = False
                        print("🔄 Simulation reset")
                    
                    elif event.key == pygame.K_SPACE:
                        # Toggle pause
                        paused = not paused
                        status = "paused" if paused else "resumed"
                        print(f"⏸️ Simulation {status}")
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Start fire at mouse position
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    grid_x = mouse_x // CELL_SIZE
                    grid_y = mouse_y // CELL_SIZE
                    
                    if (0 <= grid_x < GRID_SIZE and 0 <= grid_y < GRID_SIZE 
                        and self.fire_model.grid[grid_y][grid_x] == 1):
                        self.fire_model.ignite(grid_x, grid_y)
                        print(f"🔥 Fire started at ({grid_x}, {grid_y})")
            
            # Update simulation (if not paused)
            if not paused:
                self.fire_model.spread_fire()
            
            # Render
            self.screen.fill((0, 0, 0))  # Black background
            self.renderer.draw_grid(self.fire_model.get_state())
            pygame.display.flip()
            self.clock.tick(FPS)
        
        # Cleanup
        pygame.quit()
        print("\n👋 Simulation ended. Thank you!")


def main():
    """Main entry point."""
    try:
        simulation = ForestFireSimulation()
        simulation.run_simulation()
    except KeyboardInterrupt:
        print("\n\n👋 Simulation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
        print("Please check your internet connection and try again.")


if __name__ == "__main__":
    main()
