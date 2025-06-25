# Grid and display settings
GRID_SIZE = 100  # Grid will be 100x100
CELL_SIZE = 5    # Each cell will be 5x5 pixels
FPS = 10         # Frames per second

# Fire simulation parameters
IGNITION_PROBABILITY = 0.0001  # Probability of spontaneous ignition
SPREAD_PROBABILITY = 0.3       # Probability fire spreads to adjacent cells
BURN_TIME = 5                  # How many steps a cell burns before becoming ash

# Colors for different cell states
COLORS = {
    "empty": (255, 255, 255),    # White
    "tree": (0, 128, 0),         # Green
    "burning": (255, 0, 0),      # Red
    "burned": (64, 64, 64),      # Dark gray
    "ash": (128, 128, 128)       # Light gray
}