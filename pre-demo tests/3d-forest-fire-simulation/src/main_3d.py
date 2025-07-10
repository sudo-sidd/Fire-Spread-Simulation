#!/usr/bin/env python3
"""
3D Forest Fire Simulation using Ursina with proper headless configuration
"""

import sys
import os

# Configure Panda3D BEFORE importing Ursina
from panda3d.core import loadPrcFileData

# Try different configurations for headless mode
loadPrcFileData("", "window-type offscreen")
loadPrcFileData("", "framebuffer-hardware false")
loadPrcFileData("", "framebuffer-software true")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "show-frame-rate-meter false")

# Alternative: Try to use a virtual framebuffer
try:
    loadPrcFileData("", "gl-version 3 2")
except:
    pass

# Now import Ursina
from ursina import *

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.fire_model import FireModel
from graphics.renderer_3d import Renderer3D
from graphics.camera_controller import CameraController

class FireSimulation3D(Entity):
    def __init__(self):
        super().__init__()
        self.grid_size = 30  # Smaller grid for better performance
        self.cell_size = 1
        self.fire_model = FireModel(self.grid_size, self.grid_size)
        self.renderer = Renderer3D(self.fire_model, self.cell_size)
        
        # Start multiple fires for more interesting simulation
        self.fire_model.ignite(self.grid_size // 2, self.grid_size // 2)
        self.fire_model.ignite(self.grid_size // 4, self.grid_size // 4)
        self.fire_model.ignite(3 * self.grid_size // 4, 3 * self.grid_size // 4)
        
        self.setup_scene()
        self.setup_camera()
        
        # Simulation control
        self.simulation_running = True
        self.step_count = 0
        self.max_steps = 500

    def setup_scene(self):
        # Set up lighting
        DirectionalLight(
            parent=scene,
            y=2,
            z=3,
            shadows=True,
            rotation=(45, -45, 45)
        )
        
        # Add some ambient light
        AmbientLight(color=color.rgba(100, 100, 100, 0.1))
        
        # Initial forest render
        self.renderer.render_forest()

    def setup_camera(self):
        # Position camera to get a good view of the grid
        camera.position = (self.grid_size // 2, self.grid_size // 2, self.grid_size // 2 + 20)
        camera.rotation_x = 60
        camera.rotation_y = 45
        
        # Set up camera controls
        EditorCamera()

    def update(self):
        if self.simulation_running and self.step_count < self.max_steps:
            # Update fire simulation every few frames for better visualization
            if int(time.time() * 2) != getattr(self, 'last_update_time', 0):
                self.last_update_time = int(time.time() * 2)
                self.fire_model.spread_fire()
                self.renderer.update_forest()
                self.step_count += 1
                
                if self.step_count % 50 == 0:
                    print(f"Simulation step: {self.step_count}")
        
        # Stop simulation after max steps
        if self.step_count >= self.max_steps:
            if self.simulation_running:
                print("Simulation completed!")
                self.simulation_running = False

def main():
    try:
        print("Starting 3D Forest Fire Simulation...")
        
        # Create Ursina app with specific settings
        app = Ursina(
            title='3D Forest Fire Simulation',
            borderless=False,
            fullscreen=False,
            size=(1024, 768),
            vsync=False
        )
        
        # Create the simulation
        simulation = FireSimulation3D()
        
        # Add instructions
        Text(
            'WASD: Move camera\nMouse: Look around\nESC: Quit',
            position=(-0.8, 0.4),
            scale=0.5,
            color=color.white,
            background=True
        )
        
        # Add quit function
        def input(key):
            if key == 'escape':
                quit()
        
        print("3D simulation started successfully!")
        print("Use WASD to move, mouse to look around, ESC to quit")
        
        app.run()
        
    except Exception as e:
        print(f"3D simulation failed: {e}")
        print("\nThis could be due to:")
        print("1. Missing or outdated graphics drivers")
        print("2. No display available (running on headless system)")
        print("3. OpenGL not supported")
        print("\nTrying alternative approaches...")
        
        # Try with different settings
        try_alternative_3d()

def try_alternative_3d():
    """Try alternative 3D visualization approaches"""
    print("\nTrying alternative 3D visualization...")
    
    try:
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D
        import numpy as np
        
        # Create 3D matplotlib visualization
        print("Using matplotlib 3D visualization...")
        
        # Add the src directory to the path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from simulation.fire_model import FireModel
        
        # Create simulation
        grid_size = 20
        fire_model = FireModel(grid_size, grid_size)
        
        # Start fires
        fire_model.ignite(grid_size // 2, grid_size // 2)
        fire_model.ignite(grid_size // 4, grid_size // 4)
        
        # Create 3D plot
        fig = plt.figure(figsize=(12, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # Run simulation steps and create 3D visualization
        for step in range(50):
            if step % 10 == 0:
                fire_model.spread_fire()
                
                # Clear previous plot
                ax.clear()
                
                # Get current state
                grid_state = fire_model.get_state()
                
                # Create 3D grid visualization
                for y in range(grid_size):
                    for x in range(grid_size):
                        state = grid_state[y][x]
                        if state != 0:  # Don't show empty cells
                            # Create a cube at position (x, y, 0) with height based on state
                            height = 1 if state == 1 else (2 if state == 2 else 0.5)
                            
                            # Color based on state
                            if state == 1:  # Tree
                                color = 'green'
                            elif state == 2:  # Burning
                                color = 'red'
                            else:  # Burned
                                color = 'gray'
                            
                            # Draw cube
                            ax.bar3d(x, y, 0, 1, 1, height, color=color, alpha=0.8)
                
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Height')
                ax.set_title(f'3D Forest Fire Simulation - Step {step}')
                
                # Set equal aspect ratio
                ax.set_xlim(0, grid_size)
                ax.set_ylim(0, grid_size)
                ax.set_zlim(0, 3)
                
                plt.pause(0.5)  # Pause for animation effect
        
        plt.show()
        print("3D visualization completed!")
        
    except ImportError:
        print("matplotlib not available for 3D fallback")
    except Exception as e:
        print(f"3D fallback failed: {e}")

if __name__ == "__main__":
    main()
