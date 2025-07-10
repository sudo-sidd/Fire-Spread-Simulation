from ursina import Entity, color, curve
import random

class Terrain:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[1 for _ in range(width)] for _ in range(height)]  # Start with trees everywhere
        
        # Add some random empty spaces
        for y in range(height):
            for x in range(width):
                if random.random() < 0.1:  # 10% chance of empty space
                    self.grid[y][x] = 0

        self.generate_terrain()

    def generate_terrain(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1:  # Tree
                    Entity(model='cube', color=color.green, position=(x, 0, y), scale=(1, 1, 1))
                elif self.grid[y][x] == 0:  # Empty space
                    Entity(model='cube', color=color.brown, position=(x, 0, y), scale=(1, 1, 1))

    def reset(self):
        self.grid = [[1 for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < 0.1:
                    self.grid[y][x] = 0
        self.generate_terrain()