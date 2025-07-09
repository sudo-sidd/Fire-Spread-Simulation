#!/usr/bin/env python3
"""
3D Forest Fire Simulation using Pygame + OpenGL
This should work better with NVIDIA GPUs and modern OpenGL
"""

import sys
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math
import time

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.fire_model import FireModel

class FireSimulation3DOpenGL:
    def __init__(self, grid_size=25):
        self.grid_size = grid_size
        self.cell_size = 1.0
        self.fire_model = FireModel(grid_size, grid_size)
        
        # Camera settings
        self.camera_pos = [grid_size // 2, grid_size // 2 + 20, grid_size // 2 + 15]
        self.camera_rot = [30, 0]  # pitch, yaw
        self.mouse_sensitivity = 0.1
        self.move_speed = 0.5
        
        # Simulation settings
        self.step_count = 0
        self.auto_step = True
        self.step_delay = 0.2
        self.last_step_time = time.time()
        
        # Start fires
        self.fire_model.ignite(grid_size // 2, grid_size // 2)
        self.fire_model.ignite(grid_size // 4, grid_size // 4)
        self.fire_model.ignite(3 * grid_size // 4, 3 * grid_size // 4)
        
        # Colors for different states
        self.colors = {
            0: (0.6, 0.4, 0.2),  # Empty - brown
            1: (0.0, 0.8, 0.0),  # Tree - green
            2: (1.0, 0.2, 0.0),  # Burning - red
            3: (0.4, 0.4, 0.4)   # Burned - gray
        }
        
        # Initialize pygame and OpenGL
        self.init_display()
        self.init_opengl()

    def init_display(self):
        """Initialize pygame display"""
        pygame.init()
        self.display = (1024, 768)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Forest Fire Simulation - OpenGL")
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def init_opengl(self):
        """Initialize OpenGL settings"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Set up lighting
        glLightfv(GL_LIGHT0, GL_POSITION, (1, 1, 1, 0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1, 1, 1, 1))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
        
        # Set up perspective
        gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 1000.0)
        
        # Set background color
        glClearColor(0.5, 0.8, 1.0, 1.0)  # Sky blue

    def draw_cube(self, x, y, z, size, color):
        """Draw a cube at the specified position"""
        glColor3f(*color)
        glPushMatrix()
        glTranslatef(x, z, y)  # Note: OpenGL Y is up, but our grid Y is forward
        glScalef(size, size, size)
        
        # Draw cube faces
        glBegin(GL_QUADS)
        
        # Front face
        glNormal3f(0, 0, 1)
        glVertex3f(-0.5, -0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        
        # Back face
        glNormal3f(0, 0, -1)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        
        # Top face
        glNormal3f(0, 1, 0)
        glVertex3f(-0.5, 0.5, -0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(0.5, 0.5, -0.5)
        
        # Bottom face
        glNormal3f(0, -1, 0)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, -0.5, 0.5)
        glVertex3f(-0.5, -0.5, 0.5)
        
        # Right face
        glNormal3f(1, 0, 0)
        glVertex3f(0.5, -0.5, -0.5)
        glVertex3f(0.5, 0.5, -0.5)
        glVertex3f(0.5, 0.5, 0.5)
        glVertex3f(0.5, -0.5, 0.5)
        
        # Left face
        glNormal3f(-1, 0, 0)
        glVertex3f(-0.5, -0.5, -0.5)
        glVertex3f(-0.5, -0.5, 0.5)
        glVertex3f(-0.5, 0.5, 0.5)
        glVertex3f(-0.5, 0.5, -0.5)
        
        glEnd()
        glPopMatrix()

    def render_forest(self):
        """Render the 3D forest"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Apply camera transformations
        glLoadIdentity()
        glRotatef(self.camera_rot[0], 1, 0, 0)  # Pitch
        glRotatef(self.camera_rot[1], 0, 1, 0)  # Yaw
        glTranslatef(-self.camera_pos[0], -self.camera_pos[1], -self.camera_pos[2])
        
        # Get current grid state
        grid_state = self.fire_model.get_state()
        
        # Draw grid
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                state = grid_state[y][x]
                
                if state == 0:  # Empty - just ground
                    self.draw_cube(x, y, 0, 0.9, self.colors[0])
                elif state == 1:  # Tree - trunk + leaves
                    # Draw trunk
                    self.draw_cube(x, y, 0.5, 0.3, (0.6, 0.3, 0.1))
                    # Draw leaves
                    height = np.random.uniform(1.5, 2.5)
                    self.draw_cube(x, y, height, 1.2, self.colors[1])
                elif state == 2:  # Burning - animated fire
                    # Draw burning base
                    self.draw_cube(x, y, 0.5, 0.8, (0.8, 0.4, 0.0))
                    # Draw flames
                    flame_height = 2.0 + 0.5 * math.sin(time.time() * 5 + x + y)
                    flame_color = (1.0, 0.3 + 0.2 * math.sin(time.time() * 3), 0.0)
                    self.draw_cube(x, y, flame_height, 0.6, flame_color)
                elif state == 3:  # Burned - ash
                    self.draw_cube(x, y, 0.2, 0.8, self.colors[3])
        
        # Draw ground plane
        glColor3f(0.3, 0.6, 0.2)  # Green grass
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-2, 0, -2)
        glVertex3f(self.grid_size + 2, 0, -2)
        glVertex3f(self.grid_size + 2, 0, self.grid_size + 2)
        glVertex3f(-2, 0, self.grid_size + 2)
        glEnd()
        
        pygame.display.flip()

    def handle_input(self):
        """Handle keyboard and mouse input"""
        keys = pygame.key.get_pressed()
        
        # Movement
        if keys[K_w]:
            self.camera_pos[2] -= self.move_speed
        if keys[K_s]:
            self.camera_pos[2] += self.move_speed
        if keys[K_a]:
            self.camera_pos[0] -= self.move_speed
        if keys[K_d]:
            self.camera_pos[0] += self.move_speed
        if keys[K_SPACE]:
            self.camera_pos[1] += self.move_speed
        if keys[K_LCTRL]:
            self.camera_pos[1] -= self.move_speed
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == K_ESCAPE):
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == K_r:
                    print("Restarting simulation...")
                    self.fire_model.reset()
                    self.fire_model.ignite(self.grid_size // 2, self.grid_size // 2)
                    self.step_count = 0
                elif event.key == K_SPACE:
                    self.auto_step = not self.auto_step
                    print(f"Auto-step: {'ON' if self.auto_step else 'OFF'}")
            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.rel
                self.camera_rot[1] += mouse_x * self.mouse_sensitivity
                self.camera_rot[0] -= mouse_y * self.mouse_sensitivity
                # Clamp pitch
                self.camera_rot[0] = max(-90, min(90, self.camera_rot[0]))
        
        return True

    def update_simulation(self):
        """Update the fire simulation"""
        current_time = time.time()
        if self.auto_step and current_time - self.last_step_time > self.step_delay:
            self.fire_model.spread_fire()
            self.step_count += 1
            self.last_step_time = current_time
            
            if self.step_count % 10 == 0:
                print(f"Simulation step: {self.step_count}")

    def run(self):
        """Main game loop"""
        print("3D Forest Fire Simulation - OpenGL")
        print("Controls:")
        print("  WASD - Move camera")
        print("  Mouse - Look around")
        print("  Space - Toggle auto-step")
        print("  R - Restart simulation")
        print("  Ctrl - Move down")
        print("  ESC - Quit")
        
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Handle input
            running = self.handle_input()
            
            # Update simulation
            self.update_simulation()
            
            # Render
            self.render_forest()
            
            # Control frame rate
            clock.tick(60)
        
        pygame.quit()
        print("Simulation ended.")

def main():
    try:
        print("Starting 3D Forest Fire Simulation with OpenGL...")
        print("GPU: NVIDIA GeForce RTX 2050")
        print("Using Pygame + OpenGL for better compatibility")
        
        sim = FireSimulation3DOpenGL(grid_size=20)
        sim.run()
        
    except Exception as e:
        print(f"OpenGL simulation failed: {e}")
        import traceback
        traceback.print_exc()
        
        print("\nIf you're getting OpenGL errors, try:")
        print("1. Update your graphics drivers")
        print("2. Run with: LIBGL_ALWAYS_SOFTWARE=1 python main_opengl.py")
        print("3. Or use the matplotlib version: python main_voxel.py")

if __name__ == "__main__":
    main()
