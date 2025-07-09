# filepath: /3d-forest-fire-simulation/3d-forest-fire-simulation/src/utils/config.py

# Grid and display settings
GRID_SIZE = 100  # Grid will be 100x100
CELL_SIZE = 1    # Each cell will be 1 unit in 3D space
FPS = 60         # Frames per second

# Fire simulation parameters
IGNITION_PROBABILITY = 0.01  # Probability of spontaneous ignition
SPREAD_PROBABILITY = 0.3      # Probability fire spreads to adjacent cells
BURN_TIME = 3                 # How many steps a cell burns before becoming ash

# Colors for different cell states
COLORS = {
    "empty": (0.5, 0.25, 0),    # Brown for empty ground/dirt
    "tree": (0, 0.5, 0),        # Green for trees
    "burning": (1, 0, 0),       # Red for burning trees
    "burned": (0.25, 0.25, 0.25) # Dark gray for burned areas
}