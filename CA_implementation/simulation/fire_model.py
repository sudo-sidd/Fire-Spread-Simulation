import random
from ..utils.config import IGNITION_PROBABILITY, SPREAD_PROBABILITY

class FireModel:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # 0 = empty, 1 = tree, 2 = burning, 3 = burned
        self.grid = [[1 for _ in range(width)] for _ in range(height)]  # Start with trees everywhere
        
        # Add some random empty spaces
        for y in range(height):
            for x in range(width):
                if random.random() < 0.1:  # 10% chance of empty space
                    self.grid[y][x] = 0

    def ignite(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height and self.grid[y][x] == 1:
            self.grid[y][x] = 2  # 2 represents burning

    def spread_fire(self):
        new_grid = [row[:] for row in self.grid]
        
        for y in range(self.height):
            for x in range(self.width):
                current_cell = self.grid[y][x]
                
                if current_cell == 2:  # If burning
                    new_grid[y][x] = 3  # Becomes burned
                    
                    # Spread to neighbors
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.width and 0 <= ny < self.height and 
                            self.grid[ny][nx] == 1 and random.random() < SPREAD_PROBABILITY):
                            new_grid[ny][nx] = 2  # Ignite neighboring tree
                
                elif current_cell == 1:  # If tree (healthy)
                    # Small chance of spontaneous ignition
                    if random.random() < IGNITION_PROBABILITY:
                        new_grid[y][x] = 2
        
        self.grid = new_grid

    def reset(self):
        self.grid = [[1 for _ in range(self.width)] for _ in range(self.height)]
        # Add some random empty spaces
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < 0.1:
                    self.grid[y][x] = 0

    def get_state(self):
        return self.grid