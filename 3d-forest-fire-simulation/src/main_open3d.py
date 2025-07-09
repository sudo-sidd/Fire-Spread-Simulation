#!/usr/bin/env python3
"""
3D Forest Fire Simulation using Open3D for better 3D visualization
This should work better on systems with graphics issues
"""

import sys
import os
import numpy as np
import time

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.fire_model import FireModel

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    print("Open3D not available, falling back to matplotlib 3D")

class FireSimulation3DOpen3D:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.cell_size = 1.0
        self.fire_model = FireModel(grid_size, grid_size)
        
        # Start multiple fires
        self.fire_model.ignite(grid_size // 2, grid_size // 2)
        self.fire_model.ignite(grid_size // 4, grid_size // 4)
        self.fire_model.ignite(3 * grid_size // 4, 3 * grid_size // 4)
        
        # Initialize Open3D
        if OPEN3D_AVAILABLE:
            self.vis = o3d.visualization.Visualizer()
            self.vis.create_window(window_name="3D Forest Fire Simulation", width=1024, height=768)
            
            # Create initial geometry
            self.point_cloud = o3d.geometry.PointCloud()
            self.vis.add_geometry(self.point_cloud)
            
            # Set up camera
            self.setup_camera()
        
        self.step_count = 0
        self.max_steps = 200

    def setup_camera(self):
        if OPEN3D_AVAILABLE:
            ctr = self.vis.get_view_control()
            ctr.set_lookat([self.grid_size/2, self.grid_size/2, 0])
            ctr.set_up([0, 0, 1])
            ctr.set_front([1, 1, 1])
            ctr.set_zoom(0.5)

    def create_3d_points(self):
        """Create 3D point cloud from current fire model state"""
        points = []
        colors = []
        
        grid_state = self.fire_model.get_state()
        
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                state = grid_state[y][x]
                
                if state != 0:  # Don't show empty cells
                    # Create multiple points for each cell to make it more visible
                    for i in range(5):  # 5 points per cell
                        for j in range(5):
                            px = x + i * 0.2
                            py = y + j * 0.2
                            
                            # Height based on state
                            if state == 1:  # Tree
                                pz = np.random.uniform(0.5, 2.0)  # Random tree height
                                color = [0, 0.8, 0]  # Green
                            elif state == 2:  # Burning
                                pz = np.random.uniform(1.0, 3.0)  # Taller flames
                                color = [1, np.random.uniform(0.3, 0.7), 0]  # Red-orange
                            else:  # Burned
                                pz = np.random.uniform(0.1, 0.5)  # Low ash
                                color = [0.3, 0.3, 0.3]  # Gray
                            
                            points.append([px, py, pz])
                            colors.append(color)
        
        return np.array(points), np.array(colors)

    def update_visualization(self):
        """Update the 3D visualization"""
        if OPEN3D_AVAILABLE:
            points, colors = self.create_3d_points()
            
            self.point_cloud.points = o3d.utility.Vector3dVector(points)
            self.point_cloud.colors = o3d.utility.Vector3dVector(colors)
            
            self.vis.update_geometry(self.point_cloud)
            self.vis.poll_events()
            self.vis.update_renderer()

    def run_simulation(self):
        """Run the interactive 3D simulation"""
        if not OPEN3D_AVAILABLE:
            self.run_fallback_3d()
            return
        
        print("Starting 3D Forest Fire Simulation with Open3D...")
        print("Close the window to stop the simulation")
        
        # Initial visualization
        self.update_visualization()
        
        while self.vis.poll_events() and self.step_count < self.max_steps:
            # Update simulation
            self.fire_model.spread_fire()
            self.step_count += 1
            
            # Update visualization
            self.update_visualization()
            
            if self.step_count % 10 == 0:
                print(f"Simulation step: {self.step_count}")
            
            time.sleep(0.1)  # Control simulation speed
        
        self.vis.destroy_window()
        print("Simulation completed!")

    def run_fallback_3d(self):
        """Fallback 3D visualization using matplotlib"""
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            
            print("Using matplotlib 3D visualization...")
            
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            for step in range(50):
                if step % 2 == 0:
                    self.fire_model.spread_fire()
                    
                    # Clear previous plot
                    ax.clear()
                    
                    # Get current state
                    grid_state = self.fire_model.get_state()
                    
                    # Create 3D visualization
                    xs, ys, zs = [], [], []
                    colors = []
                    
                    for y in range(self.grid_size):
                        for x in range(self.grid_size):
                            state = grid_state[y][x]
                            if state != 0:
                                # Add multiple points for each cell
                                for i in range(3):
                                    for j in range(3):
                                        xs.append(x + i * 0.3)
                                        ys.append(y + j * 0.3)
                                        
                                        if state == 1:  # Tree
                                            zs.append(np.random.uniform(0.5, 2.0))
                                            colors.append('green')
                                        elif state == 2:  # Burning
                                            zs.append(np.random.uniform(1.0, 3.0))
                                            colors.append('red')
                                        else:  # Burned
                                            zs.append(np.random.uniform(0.1, 0.5))
                                            colors.append('gray')
                    
                    # Plot points
                    ax.scatter(xs, ys, zs, c=colors, s=20, alpha=0.8)
                    
                    ax.set_xlabel('X')
                    ax.set_ylabel('Y')
                    ax.set_zlabel('Height')
                    ax.set_title(f'3D Forest Fire Simulation - Step {step}')
                    
                    # Set limits
                    ax.set_xlim(0, self.grid_size)
                    ax.set_ylim(0, self.grid_size)
                    ax.set_zlim(0, 3)
                    
                    plt.pause(0.2)
            
            plt.show()
            
        except Exception as e:
            print(f"3D visualization failed: {e}")

def main():
    print("3D Forest Fire Simulation")
    print("=" * 30)
    
    if OPEN3D_AVAILABLE:
        print("Using Open3D for 3D visualization")
    else:
        print("Open3D not available, using matplotlib fallback")
        print("To install Open3D: pip install open3d")
    
    # Create and run simulation
    sim = FireSimulation3DOpen3D(grid_size=20)
    sim.run_simulation()

if __name__ == "__main__":
    main()
