#!/usr/bin/env python3
"""
3D Voxel-based Forest Fire Simulation
Creates a true 3D grid with cubes representing different states
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import ListedColormap
import matplotlib.animation as animation
import time

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.fire_model import FireModel

class FireSimulation3DVoxel:
    def __init__(self, grid_size=15):
        self.grid_size = grid_size
        self.fire_model = FireModel(grid_size, grid_size)
        
        # Start multiple fires for interesting dynamics
        self.fire_model.ignite(grid_size // 2, grid_size // 2)
        self.fire_model.ignite(grid_size // 4, grid_size // 4)
        self.fire_model.ignite(3 * grid_size // 4, 3 * grid_size // 4)
        
        # Set up matplotlib
        self.fig = plt.figure(figsize=(12, 10))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Colors for different states
        self.colors = {
            0: (0.8, 0.6, 0.4, 0.1),  # Empty - light brown, very transparent
            1: (0.0, 0.8, 0.0, 0.8),  # Tree - green, solid
            2: (1.0, 0.2, 0.0, 0.9),  # Burning - red, very solid
            3: (0.3, 0.3, 0.3, 0.6)   # Burned - gray, semi-transparent
        }
        
        self.step_count = 0

    def create_3d_voxels(self):
        """Create 3D voxel representation of the forest"""
        grid_state = np.array(self.fire_model.get_state())
        
        # Create a 3D array where each cell can have height
        voxels = np.zeros((self.grid_size, self.grid_size, 4), dtype=bool)
        colors = np.empty(voxels.shape + (4,), dtype=float)
        
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                state = grid_state[y][x]
                
                if state == 0:  # Empty - ground level only
                    voxels[x, y, 0] = True
                    colors[x, y, 0] = self.colors[0]
                elif state == 1:  # Tree - multiple levels
                    height = np.random.randint(1, 4)  # Trees have random height 1-3
                    for z in range(height):
                        voxels[x, y, z] = True
                        # Gradient from brown (base) to green (top)
                        if z == 0:
                            colors[x, y, z] = (0.6, 0.4, 0.2, 0.8)  # Brown trunk
                        else:
                            colors[x, y, z] = self.colors[1]  # Green leaves
                elif state == 2:  # Burning - tall flames
                    height = np.random.randint(2, 4)  # Flames are 2-3 levels high
                    for z in range(height):
                        voxels[x, y, z] = True
                        # Gradient from red to orange-yellow
                        if z == 0:
                            colors[x, y, z] = (1.0, 0.0, 0.0, 0.9)  # Red base
                        else:
                            colors[x, y, z] = (1.0, 0.5, 0.0, 0.8)  # Orange flames
                elif state == 3:  # Burned - ash on ground
                    voxels[x, y, 0] = True
                    colors[x, y, 0] = self.colors[3]
        
        return voxels, colors

    def update_plot(self):
        """Update the 3D plot"""
        self.ax.clear()
        
        # Create voxels
        voxels, colors = self.create_3d_voxels()
        
        # Plot voxels
        self.ax.voxels(voxels, facecolors=colors, alpha=0.8)
        
        # Set labels and title
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Height')
        self.ax.set_title(f'3D Forest Fire Simulation - Step {self.step_count}')
        
        # Set equal aspect ratio and limits
        self.ax.set_xlim(0, self.grid_size)
        self.ax.set_ylim(0, self.grid_size)
        self.ax.set_zlim(0, 4)
        
        # Set viewing angle
        self.ax.view_init(elev=30, azim=45)

    def run_interactive(self):
        """Run interactive 3D simulation"""
        print("Starting 3D Voxel Forest Fire Simulation...")
        print("Close the window to stop the simulation")
        
        plt.ion()  # Turn on interactive mode
        
        try:
            while True:
                # Update simulation
                self.fire_model.spread_fire()
                self.step_count += 1
                
                # Update visualization
                self.update_plot()
                plt.pause(0.5)  # Pause for animation
                
                if self.step_count % 10 == 0:
                    print(f"Step: {self.step_count}")
                    
                    # Print statistics
                    grid_state = np.array(self.fire_model.get_state())
                    unique, counts = np.unique(grid_state, return_counts=True)
                    state_counts = dict(zip(unique, counts))
                    total_cells = grid_state.size
                    
                    print(f"  Trees: {state_counts.get(1, 0)} ({state_counts.get(1, 0)/total_cells*100:.1f}%)")
                    print(f"  Burning: {state_counts.get(2, 0)} ({state_counts.get(2, 0)/total_cells*100:.1f}%)")
                    print(f"  Burned: {state_counts.get(3, 0)} ({state_counts.get(3, 0)/total_cells*100:.1f}%)")
                
                # Stop if no more burning cells
                if state_counts.get(2, 0) == 0 and self.step_count > 10:
                    print("Fire has been extinguished!")
                    break
                    
                if self.step_count > 200:  # Maximum steps
                    print("Maximum steps reached!")
                    break
                    
        except KeyboardInterrupt:
            print("Simulation stopped by user")
        except Exception as e:
            print(f"Simulation stopped: {e}")
        finally:
            plt.ioff()  # Turn off interactive mode
            plt.show()  # Keep final plot open

    def run_animation(self):
        """Run as animation"""
        print("Starting animated 3D simulation...")
        
        def animate(frame):
            if frame > 0:
                self.fire_model.spread_fire()
                self.step_count = frame
            
            self.update_plot()
            
            # Print progress
            if frame % 10 == 0 and frame > 0:
                print(f"Animation frame: {frame}")
            
            return []
        
        # Create animation
        ani = animation.FuncAnimation(
            self.fig, animate, frames=100, interval=500, blit=False, repeat=False
        )
        
        plt.show()
        return ani

def main():
    print("3D Voxel Forest Fire Simulation")
    print("=" * 35)
    print("This creates a true 3D grid-based visualization")
    print("Trees have height, fires create flames, burned areas show ash")
    print()
    
    # Choose simulation mode
    print("Choose simulation mode:")
    print("1. Interactive (step-by-step with statistics)")
    print("2. Animation (automatic playback)")
    
    try:
        choice = input("Enter choice (1 or 2, default 1): ").strip()
        if not choice:
            choice = "1"
    except:
        choice = "1"
    
    # Create simulation
    sim = FireSimulation3DVoxel(grid_size=12)  # Smaller grid for better performance
    
    if choice == "2":
        ani = sim.run_animation()
    else:
        sim.run_interactive()

if __name__ == "__main__":
    main()
