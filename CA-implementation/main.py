import pygame
from simulation.fire_model import FireModel
from graphics.renderer import Renderer
from utils.config import GRID_SIZE, CELL_SIZE, FPS

def main():
    pygame.init()
    screen = pygame.display.set_mode((GRID_SIZE * CELL_SIZE, GRID_SIZE * CELL_SIZE))
    pygame.display.set_caption("Forest Fire Simulation")

    clock = pygame.time.Clock()
    fire_model = FireModel(GRID_SIZE, GRID_SIZE)
    renderer = Renderer(screen, CELL_SIZE, {
        0: (139, 69, 19),    # Brown for empty/dirt
        1: (0, 128, 0),      # Green for trees
        2: (255, 0, 0),      # Red for burning
        3: (64, 64, 64)      # Dark gray for burned
    })

    # Start with some trees and initial fire
    fire_model.ignite(GRID_SIZE // 2, GRID_SIZE // 2)  # Start fire in center

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Allow user to click to start fires
                mouse_x, mouse_y = pygame.mouse.get_pos()
                grid_x = mouse_x // CELL_SIZE
                grid_y = mouse_y // CELL_SIZE
                fire_model.ignite(grid_x, grid_y)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset simulation
                    fire_model.reset()
                    fire_model.ignite(GRID_SIZE // 2, GRID_SIZE // 2)

        fire_model.spread_fire()
        
        # Clear screen
        screen.fill((0, 0, 0))  # Black background
        renderer.draw_grid(fire_model.get_state())
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()