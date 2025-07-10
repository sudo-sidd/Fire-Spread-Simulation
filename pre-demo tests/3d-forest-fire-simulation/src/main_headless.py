#!/usr/bin/env python3
"""
Headless version of the fire simulation using matplotlib for visualization.
This version works without OpenGL and can run on headless systems.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap
import time

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.fire_model import FireModel

class HeadlessFireSimulation:
    def __init__(self, grid_size=100):
        self.grid_size = grid_size
        self.fire_model = FireModel(grid_size, grid_size)
        
        # Start a fire in the center
        self.fire_model.ignite(grid_size // 2, grid_size // 2)
        
        # Create custom colormap
        # 0: empty (brown), 1: tree (green), 2: burning (red), 3: burned (gray)
        colors = ['#8B4513', '#228B22', '#FF0000', '#808080']
        self.cmap = ListedColormap(colors)
        
        # Setup matplotlib
        self.fig, self.ax = plt.subplots(figsize=(10, 10))
        self.ax.set_title('Forest Fire Simulation')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        
        # Initialize the image
        self.im = self.ax.imshow(np.array(self.fire_model.get_state()), 
                                cmap=self.cmap, vmin=0, vmax=3, animated=True)
        
        # Add colorbar
        cbar = plt.colorbar(self.im, ax=self.ax, ticks=[0, 1, 2, 3])
        cbar.set_ticklabels(['Empty', 'Tree', 'Burning', 'Burned'])
        
    def update_animation(self, frame):
        """Update function for animation"""
        self.fire_model.spread_fire()
        grid_state = np.array(self.fire_model.get_state())
        self.im.set_array(grid_state)
        return [self.im]
    
    def run_animation(self, interval=100, frames=1000):
        """Run the animated simulation"""
        ani = animation.FuncAnimation(self.fig, self.update_animation, 
                                    frames=frames, interval=interval, blit=True)
        plt.show()
        return ani
    
    def run_steps(self, steps=100):
        """Run simulation for a specific number of steps and show final result"""
        print(f"Running simulation for {steps} steps...")
        
        for step in range(steps):
            self.fire_model.spread_fire()
            if step % 10 == 0:
                print(f"Step {step}/{steps}")
        
        # Show final state
        grid_state = np.array(self.fire_model.get_state())
        plt.figure(figsize=(10, 10))
        plt.imshow(grid_state, cmap=self.cmap, vmin=0, vmax=3)
        plt.title(f'Forest Fire Simulation - Final State (Step {steps})')
        plt.xlabel('X')
        plt.ylabel('Y')
        
        # Add colorbar
        cbar = plt.colorbar(ticks=[0, 1, 2, 3])
        cbar.set_ticklabels(['Empty', 'Tree', 'Burning', 'Burned'])
        
        plt.show()
        
        # Print statistics
        unique, counts = np.unique(grid_state, return_counts=True)
        state_counts = dict(zip(unique, counts))
        total_cells = grid_state.size
        
        print("\nFinal Statistics:")
        print(f"Empty cells: {state_counts.get(0, 0)} ({state_counts.get(0, 0)/total_cells*100:.1f}%)")
        print(f"Tree cells: {state_counts.get(1, 0)} ({state_counts.get(1, 0)/total_cells*100:.1f}%)")
        print(f"Burning cells: {state_counts.get(2, 0)} ({state_counts.get(2, 0)/total_cells*100:.1f}%)")
        print(f"Burned cells: {state_counts.get(3, 0)} ({state_counts.get(3, 0)/total_cells*100:.1f}%)")

def main():
    print("Starting headless fire simulation...")
    
    # Choose simulation mode
    print("\nChoose simulation mode:")
    print("1. Animated visualization (requires display)")
    print("2. Step-by-step simulation (headless friendly)")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
    except:
        choice = "2"  # Default to headless mode
    
    # Create simulation
    sim = HeadlessFireSimulation(grid_size=50)  # Use smaller grid for better performance
    
    if choice == "1":
        print("Starting animated simulation...")
        try:
            sim.run_animation(interval=50, frames=200)
        except Exception as e:
            print(f"Animation failed: {e}")
            print("Falling back to step-by-step mode...")
            sim.run_steps(100)
    else:
        print("Running step-by-step simulation...")
        sim.run_steps(100)

if __name__ == "__main__":
    main()
