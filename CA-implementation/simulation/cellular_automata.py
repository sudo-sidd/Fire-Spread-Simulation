class CellularAutomata:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]

    def update_state(self):
        new_grid = [row[:] for row in self.grid]
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1:  # Tree is burning
                    new_grid[y][x] = 2  # Tree becomes ash
                elif self.grid[y][x] == 0:  # Empty space
                    if self._check_neighbors(x, y):
                        new_grid[y][x] = 1  # New tree ignites
        self.grid = new_grid

    def _check_neighbors(self, x, y):
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    if self.grid[ny][nx] == 1:  # Neighbor is burning
                        return True
        return False

    def get_state(self):
        return self.grid

    def reset(self):
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]