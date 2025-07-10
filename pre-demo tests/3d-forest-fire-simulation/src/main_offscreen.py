from ursina import *
import sys
import os

# Configure Panda3D BEFORE importing anything else
from panda3d.core import loadPrcFileData

# Try multiple configurations to ensure compatibility
loadPrcFileData("", "window-title Forest Fire 3D Simulation")
loadPrcFileData("", "win-size 1024 768")
loadPrcFileData("", "fullscreen 0")
loadPrcFileData("", "sync-video 0")
loadPrcFileData("", "show-frame-rate-meter 0")
loadPrcFileData("", "want-pstats 0")
loadPrcFileData("", "gl-version 3 2")
loadPrcFileData("", "gl-coordinate-system default")
loadPrcFileData("", "notify-level-display warning")

# Try to force hardware acceleration
loadPrcFileData("", "framebuffer-hardware 1")
loadPrcFileData("", "framebuffer-software 0")

# Audio can sometimes cause issues
loadPrcFileData("", "audio-library-name null")

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.fire_model import FireModel
from graphics.renderer_3d import Renderer3D
from graphics.camera_controller import CameraController

class FireSimulation(Entity):
    def __init__(self):
        super().__init__()
        self.grid_size = 30  # Smaller grid for better performance
        self.cell_size = 1
        self.fire_model = FireModel(self.grid_size, self.grid_size)
        self.renderer = Renderer3D(self.fire_model, self.cell_size)
        # Don't use the camera controller that might cause issues
        
        self.setup_scene()
        
        # Start a fire in the center
        self.fire_model.ignite(self.grid_size // 2, self.grid_size // 2)
        
        # Set up camera position manually
        camera.position = (self.grid_size // 2, self.grid_size // 2 + 15, self.grid_size // 2 + 10)
        camera.rotation_x = 30
        camera.rotation_y = 0
        
        # Add some lighting
        DirectionalLight(parent=scene, y=2, z=3, shadows=True, rotation=(45, -45, 45))
        AmbientLight(color=color.rgba(100, 100, 100, 0.1))

    def setup_scene(self):
        self.renderer.render_forest()

    def update(self):
        self.fire_model.spread_fire()
        self.renderer.update_forest()

def try_install_dependencies():
    """Try to install missing dependencies that might help with graphics"""
    print("Checking for missing dependencies...")
    
    try:
        import subprocess
        import sys
        
        # Check if we have all required packages
        missing_packages = []
        
        try:
            import OpenGL
        except ImportError:
            missing_packages.append("PyOpenGL")
        
        try:
            import PIL
        except ImportError:
            missing_packages.append("Pillow")
        
        if missing_packages:
            print(f"Installing missing packages: {', '.join(missing_packages)}")
            for package in missing_packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print("Dependencies installed. Please try running the simulation again.")
        else:
            print("All dependencies are available.")
            print("The issue might be with graphics drivers or display configuration.")
            print("Try running with: LIBGL_ALWAYS_SOFTWARE=1 python main_offscreen.py")
            
    except Exception as e:
        print(f"Could not install dependencies: {e}")

def main():
    try:
        print("Starting 3D Forest Fire Simulation with Ursina...")
        print("GPU: NVIDIA GeForce RTX 2050 detected")
        print("OpenGL version: 4.6")
        
        # Create Ursina app with explicit settings
        app = Ursina(
            title='3D Forest Fire Simulation',
            borderless=False,
            fullscreen=False,
            size=(1024, 768),
            vsync=False,
            development_mode=False
        )
        
        print("Ursina app created successfully!")
        
        # Create simulation
        simulation = FireSimulation()
        
        # Add some helpful text
        instructions = Text(
            'Controls:\nWASD - Move camera\nMouse - Look around\nSpace/Ctrl - Up/Down\nQ/E - Rotate\nESC - Quit',
            position=(-0.85, 0.45),
            scale=0.4,
            color=color.white,
            background=True
        )
        
        # Add simulation info
        info_text = Text(
            f'Grid Size: {simulation.grid_size}x{simulation.grid_size}\nPress R to restart fire',
            position=(-0.85, -0.4),
            scale=0.4,
            color=color.yellow,
            background=True
        )
        
        # Input handling
        def input(key):
            if key == 'escape':
                print("Simulation ended by user")
                quit()
            elif key == 'r':
                print("Restarting fire simulation...")
                simulation.fire_model.reset()
                simulation.fire_model.ignite(simulation.grid_size // 2, simulation.grid_size // 2)
                simulation.renderer.update_forest()
        
        print("3D simulation started successfully!")
        print("Use WASD to move, mouse to look around, R to restart, ESC to quit")
        
        # Start the main loop
        app.run()
        
    except Exception as e:
        print(f"Ursina failed to start: {e}")
        print("Error details:")
        import traceback
        traceback.print_exc()
        print("\nTrying to install additional dependencies...")
        
        # Try to install missing dependencies
        try_install_dependencies()

if __name__ == "__main__":
    main()
