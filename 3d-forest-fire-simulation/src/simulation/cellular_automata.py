class CellularAutomata:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[1 for _ in range(width)] for _ in range(height)]  # Start with trees everywhere

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
                            self.grid[ny][nx] == 1):
                            new_grid[ny][nx] = 2  # Ignite neighboring tree
                
                elif current_cell == 1:  # If tree (healthy)
                    # Small chance of spontaneous ignition
                    if random.random() < IGNITION_PROBABILITY:
                        new_grid[y][x] = 2
        
        self.grid = new_grid

    def reset(self):
        self.grid = [[1 for _ in range(self.width)] for _ in range(self.height)]

    def get_state(self):
        return self.grid