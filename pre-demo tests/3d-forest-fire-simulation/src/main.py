from ursina import *
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.fire_model import FireModel
from graphics.renderer_3d import Renderer3D
from graphics.camera_controller import CameraController

class FireSimulation(Entity):
    def __init__(self):
        super().__init__()
        self.grid_size = 100
        self.cell_size = 1
        self.fire_model = FireModel(self.grid_size, self.grid_size)
        self.renderer = Renderer3D(self.fire_model, self.cell_size)
        self.camera_controller = CameraController()

        self.setup_scene()
        
        # Start a fire in the center
        self.fire_model.ignite(self.grid_size // 2, self.grid_size // 2)

    def setup_scene(self):
        self.renderer.render_forest()

    def update(self):
        self.fire_model.spread_fire()
        self.renderer.update_forest()

def main():
    app = Ursina()
    simulation = FireSimulation()
    app.run()

if __name__ == "__main__":
    main()