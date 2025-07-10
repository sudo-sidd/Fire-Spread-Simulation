import pygame

class Renderer:
    def __init__(self, screen, grid_size, colors):
        self.screen = screen
        self.grid_size = grid_size
        self.colors = colors

    def draw_grid(self, grid):
        for y in range(len(grid)):
            for x in range(len(grid[y])):
                color = self.colors[grid[y][x]]
                pygame.draw.rect(self.screen, color, (x * self.grid_size, y * self.grid_size, self.grid_size, self.grid_size))

    def update_display(self):
        pygame.display.flip()