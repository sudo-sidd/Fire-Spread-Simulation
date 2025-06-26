# Forest Fire Simulation

A pygame-based forest fire simulation using cellular automata.

**Required Libraries:**

* pygame

## Features

- Real-time forest fire spread simulation
- Interactive fire starting with mouse clicks
- Realistic fire propagation based on cellular automata rules
- Visual representation with different colors for different states

## Cell States

- **Brown**: Empty ground/dirt
- **Green**: Healthy trees
- **Red**: Burning trees
- **Dark Gray**: Burned areas

## Controls

- **Mouse Click**: Start a fire at the clicked location
- **R Key**: Reset the simulation
- **Close Window**: Exit the simulation

## Configuration

You can modify the simulation parameters in `utils/config.py`:

- `GRID_SIZE`: Size of the simulation grid
- `CELL_SIZE`: Size of each cell in pixels
- `FPS`: Frames per second
- `IGNITION_PROBABILITY`: Chance of spontaneous ignition
- `SPREAD_PROBABILITY`: Chance fire spreads to adjacent cells
