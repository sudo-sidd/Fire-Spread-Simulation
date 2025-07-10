from ursina import *

class Renderer3D:
    def __init__(self, fire_model, cell_size):
        self.fire_model = fire_model
        self.grid_size = fire_model.width  # Use the fire_model dimensions
        self.cell_size = cell_size
        self.entities = []

        # Create the 3D grid representation
        self.create_grid()

    def create_grid(self):
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                # Create a cube for each cell in the grid
                entity = self.create_cube(x, y)
                self.entities.append(entity)

    def create_cube(self, x, y):
        # Create a cube entity at the specified grid position
        cube = Entity(model='cube', color=color.green, position=(x * self.cell_size, 0, y * self.cell_size), scale=self.cell_size)
        return cube

    def render_forest(self):
        """Initial render of the forest"""
        self.update_forest()

    def update_forest(self):
        """Update the forest visualization based on current fire model state"""
        grid_state = self.fire_model.get_state()
        self.update_grid(grid_state)

    def update_grid(self, grid_state):
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                state = grid_state[y][x]
                self.update_cube_color(self.entities[y * self.grid_size + x], state)

    def update_cube_color(self, cube, state):
        if state == 0:  # Empty
            cube.color = color.brown
        elif state == 1:  # Tree
            cube.color = color.green
        elif state == 2:  # Burning
            cube.color = color.red
        elif state == 3:  # Burned
            cube.color = color.gray