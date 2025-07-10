#!/usr/bin/env python3
"""
3D Forest Fire Simulation using Pygame with software 3D rendering
No OpenGL required - pure software 3D projection
"""

import sys
import os
import pygame
import numpy as np
import math
import time

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.fire_model import FireModel

class Camera:
    def __init__(self, pos, target):
        self.pos = np.array(pos, dtype=float)
        self.target = np.array(target, dtype=float)
        self.up = np.array([0, 1, 0], dtype=float)
        self.fov = 60
        self.aspect = 4/3
        self.near = 1
        self.far = 1000

    def get_view_matrix(self):
        """Calculate view matrix"""
        forward = self.target - self.pos
        forward = forward / np.linalg.norm(forward)
        
        right = np.cross(forward, self.up)
        right = right / np.linalg.norm(right)
        
        up = np.cross(right, forward)
        
        return forward, right, up

    def project_point(self, point, screen_width, screen_height):
        """Project 3D point to 2D screen coordinates"""
        # Translate to camera space
        cam_space = point - self.pos
        
        # Get camera vectors
        forward, right, up = self.get_view_matrix()
        
        # Transform to camera coordinate system
        x = np.dot(cam_space, right)
        y = np.dot(cam_space, up)
        z = np.dot(cam_space, forward)
        
        # Avoid division by zero
        if z <= 0.1:
            return None
        
        # Perspective projection
        fov_rad = math.radians(self.fov)
        scale = 1.0 / math.tan(fov_rad / 2)
        
        screen_x = (x * scale / z) * (screen_width / 2) + screen_width / 2
        screen_y = (y * scale / z) * (screen_height / 2) + screen_height / 2
        
        return (int(screen_x), int(screen_y), z)

class FireSimulation3DPygame:
    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        self.cell_size = 2.0
        self.fire_model = FireModel(grid_size, grid_size)
        
        # Initialize pygame
        pygame.init()
        self.screen_width = 1024
        self.screen_height = 768
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("3D Forest Fire Simulation - Software Rendering")
        
        # Colors
        self.colors = {
            0: (139, 69, 19),   # Empty - brown
            1: (34, 139, 34),   # Tree - green
            2: (255, 69, 0),    # Burning - red-orange
            3: (105, 105, 105)  # Burned - gray
        }
        
        # Camera setup
        center = grid_size * self.cell_size / 2
        self.camera = Camera(
            pos=[center, center + 15, center + 20],
            target=[center, 0, center]
        )
        
        # Simulation state
        self.step_count = 0
        self.auto_step = True
        self.step_delay = 0.3
        self.last_step_time = time.time()
        
        # Start fires
        self.fire_model.ignite(grid_size // 2, grid_size // 2)
        self.fire_model.ignite(grid_size // 4, grid_size // 4)
        
        # Input state
        self.keys = set()
        self.mouse_sensitivity = 0.005
        self.move_speed = 1.0
        
        print("3D Software Rendering initialized successfully!")

    def draw_cube_wireframe(self, center, size, color, depth):
        """Draw a wireframe cube with proper 3D edges"""
        half_size = size / 2
        
        # Define cube vertices (Y is up)
        vertices = [
            # Bottom face
            [center[0] - half_size, center[1] - half_size, center[2] - half_size],  # 0
            [center[0] + half_size, center[1] - half_size, center[2] - half_size],  # 1
            [center[0] + half_size, center[1] - half_size, center[2] + half_size],  # 2
            [center[0] - half_size, center[1] - half_size, center[2] + half_size],  # 3
            # Top face
            [center[0] - half_size, center[1] + half_size, center[2] - half_size],  # 4
            [center[0] + half_size, center[1] + half_size, center[2] - half_size],  # 5
            [center[0] + half_size, center[1] + half_size, center[2] + half_size],  # 6
            [center[0] - half_size, center[1] + half_size, center[2] + half_size],  # 7
        ]
        
        # Project vertices to screen
        screen_vertices = []
        for vertex in vertices:
            projected = self.camera.project_point(np.array(vertex), self.screen_width, self.screen_height)
            if projected:
                screen_vertices.append(projected)
            else:
                return  # Skip if any vertex is behind camera
        
        # Draw edges with depth-based color intensity
        depth_factor = max(0.2, min(1.0, 40.0 / depth))
        adjusted_color = tuple(int(c * depth_factor) for c in color)
        
        # Define cube edges (vertex index pairs)
        edges = [
            # Bottom face edges
            (0, 1), (1, 2), (2, 3), (3, 0),
            # Top face edges  
            (4, 5), (5, 6), (6, 7), (7, 4),
            # Vertical edges connecting bottom to top
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        
        # Draw edges with varying thickness for fire effect
        line_width = 3 if 'fire' in str(color) else 2
        
        for edge in edges:
            try:
                start = screen_vertices[edge[0]]
                end = screen_vertices[edge[1]]
                pygame.draw.line(self.screen, adjusted_color, 
                               (start[0], start[1]), (end[0], end[1]), line_width)
            except (IndexError, TypeError):
                continue

    def draw_cube_filled(self, center, size, color, depth):
        """Draw a filled cube with proper 3D faces"""
        half_size = size / 2
        
        # Define cube vertices in proper 3D space (Y is up)
        vertices = [
            # Bottom face (Y = center[1] - half_size)
            [center[0] - half_size, center[1] - half_size, center[2] - half_size],  # 0: bottom-left-front
            [center[0] + half_size, center[1] - half_size, center[2] - half_size],  # 1: bottom-right-front
            [center[0] + half_size, center[1] - half_size, center[2] + half_size],  # 2: bottom-right-back
            [center[0] - half_size, center[1] - half_size, center[2] + half_size],  # 3: bottom-left-back
            # Top face (Y = center[1] + half_size)
            [center[0] - half_size, center[1] + half_size, center[2] - half_size],  # 4: top-left-front
            [center[0] + half_size, center[1] + half_size, center[2] - half_size],  # 5: top-right-front
            [center[0] + half_size, center[1] + half_size, center[2] + half_size],  # 6: top-right-back
            [center[0] - half_size, center[1] + half_size, center[2] + half_size],  # 7: top-left-back
        ]
        
        # Project all vertices to screen
        screen_vertices = []
        for vertex in vertices:
            projected = self.camera.project_point(np.array(vertex), self.screen_width, self.screen_height)
            if projected:
                screen_vertices.append(projected)
            else:
                return  # Skip if any vertex is behind camera
        
        # Depth-based color adjustment
        depth_factor = max(0.3, min(1.0, 50.0 / depth))
        base_color = tuple(int(c * depth_factor) for c in color)
        
        # Define cube faces (vertex indices for each face)
        faces = [
            # Each face is defined by 4 vertex indices in counter-clockwise order
            ([0, 1, 5, 4], base_color, "front"),          # Front face
            ([2, 3, 7, 6], tuple(int(c * 0.7) for c in base_color), "back"),   # Back face (darker)
            ([0, 3, 7, 4], tuple(int(c * 0.8) for c in base_color), "left"),   # Left face
            ([1, 2, 6, 5], tuple(int(c * 0.8) for c in base_color), "right"),  # Right face
            ([4, 5, 6, 7], tuple(int(c * 1.0) for c in base_color), "top"),    # Top face (brightest)
            ([0, 1, 2, 3], tuple(int(c * 0.6) for c in base_color), "bottom"), # Bottom face (darkest)
        ]
        
        # Calculate face normals and draw visible faces
        camera_pos = self.camera.pos
        
        for face_indices, face_color, face_name in faces:
            try:
                # Get 3D coordinates of face vertices
                face_3d = [vertices[i] for i in face_indices]
                
                # Calculate face normal (simplified visibility check)
                v1 = np.array(face_3d[1]) - np.array(face_3d[0])
                v2 = np.array(face_3d[2]) - np.array(face_3d[0])
                normal = np.cross(v1, v2)
                normal = normal / np.linalg.norm(normal)
                
                # Vector from face center to camera
                face_center = np.mean(face_3d, axis=0)
                to_camera = camera_pos - face_center
                to_camera = to_camera / np.linalg.norm(to_camera)
                
                # Only draw faces facing the camera
                if np.dot(normal, to_camera) > 0:
                    # Convert to screen coordinates
                    screen_face = [screen_vertices[i][:2] for i in face_indices]
                    
                    # Draw the face
                    if len(screen_face) >= 3:
                        pygame.draw.polygon(self.screen, face_color, screen_face)
                        # Add edge lines for better definition
                        pygame.draw.polygon(self.screen, tuple(int(c * 0.5) for c in face_color), screen_face, 1)
                        
            except (ValueError, IndexError, ZeroDivisionError):
                # If face calculation fails, skip this face
                continue

    def render_scene(self):
        """Render the 3D scene"""
        # Clear screen
        self.screen.fill((135, 206, 235))  # Sky blue
        
        # Get grid state
        grid_state = self.fire_model.get_state()
        
        # Collect all cubes with their depths for sorting
        cubes_to_draw = []
        
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                state = grid_state[y][x]
                
                if state == 0:  # Empty - ground only
                    center = [x * self.cell_size, 0.1, y * self.cell_size]  # Y=0.1 for ground level
                    depth = np.linalg.norm(np.array(center) - self.camera.pos)
                    cubes_to_draw.append((center, self.cell_size * 0.8, self.colors[0], depth, 'ground'))
                    
                elif state == 1:  # Tree
                    # Ground
                    center = [x * self.cell_size, 0.1, y * self.cell_size]
                    depth = np.linalg.norm(np.array(center) - self.camera.pos)
                    cubes_to_draw.append((center, self.cell_size * 0.8, self.colors[0], depth, 'ground'))
                    
                    # Tree trunk (grows UP from ground)
                    trunk_center = [x * self.cell_size, 1.0, y * self.cell_size]  # Y=1.0 above ground
                    depth = np.linalg.norm(np.array(trunk_center) - self.camera.pos)
                    cubes_to_draw.append((trunk_center, self.cell_size * 0.4, (101, 67, 33), depth, 'trunk'))
                    
                    # Tree crown (grows UP from trunk)
                    crown_center = [x * self.cell_size, 2.2, y * self.cell_size]  # Y=2.2 above ground
                    depth = np.linalg.norm(np.array(crown_center) - self.camera.pos)
                    cubes_to_draw.append((crown_center, self.cell_size * 1.0, self.colors[1], depth, 'crown'))
                    
                elif state == 2:  # Burning
                    # Ground
                    center = [x * self.cell_size, 0.1, y * self.cell_size]
                    depth = np.linalg.norm(np.array(center) - self.camera.pos)
                    cubes_to_draw.append((center, self.cell_size * 0.8, (139, 69, 19), depth, 'ground'))
                    
                    # Fire (animated, grows UP from ground)
                    flame_height = 2.0 + 0.5 * math.sin(time.time() * 5 + x + y)
                    flame_center = [x * self.cell_size, flame_height, y * self.cell_size]  # Grows upward
                    depth = np.linalg.norm(np.array(flame_center) - self.camera.pos)
                    # Animated fire color
                    fire_intensity = 0.7 + 0.3 * math.sin(time.time() * 3 + x * 0.5 + y * 0.5)
                    fire_color = (255, int(69 + 100 * fire_intensity), 0)
                    cubes_to_draw.append((flame_center, self.cell_size * 0.8, fire_color, depth, 'fire'))
                    
                elif state == 3:  # Burned
                    # Ash on ground (low height)
                    center = [x * self.cell_size, 0.3, y * self.cell_size]  # Slightly above ground
                    depth = np.linalg.norm(np.array(center) - self.camera.pos)
                    cubes_to_draw.append((center, self.cell_size * 0.9, self.colors[3], depth, 'ash'))
        
        # Sort cubes by depth (back to front)
        cubes_to_draw.sort(key=lambda x: x[3], reverse=True)
        
        # Draw all cubes
        for center, size, color, depth, cube_type in cubes_to_draw:
            # All cube types are drawn as filled cubes for better 3D appearance
            self.draw_cube_filled(center, size, color, depth)
        
        # Draw ground plane
        self.draw_ground_plane()
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()

    def draw_ground_plane(self):
        """Draw a ground plane beneath the forest"""
        ground_size = self.grid_size * self.cell_size + 4
        ground_y = -0.5  # Below everything else
        
        # Define ground plane corners
        ground_corners = [
            [-2, ground_y, -2],
            [ground_size, ground_y, -2], 
            [ground_size, ground_y, ground_size],
            [-2, ground_y, ground_size]
        ]
        
        # Project to screen
        screen_corners = []
        for corner in ground_corners:
            projected = self.camera.project_point(np.array(corner), self.screen_width, self.screen_height)
            if projected:
                screen_corners.append(projected[:2])
        
        # Draw ground if all corners are visible
        if len(screen_corners) == 4:
            try:
                pygame.draw.polygon(self.screen, (85, 107, 47), screen_corners)  # Dark olive green
            except:
                pass  # Skip if drawing fails

    def draw_ui(self):
        """Draw user interface"""
        font = pygame.font.Font(None, 24)
        
        # Instructions
        instructions = [
            "WASD: Move camera",
            "Mouse: Look around", 
            "Space: Toggle auto-step",
            "R: Restart simulation",
            "ESC: Quit",
            f"Step: {self.step_count}",
            f"Auto-step: {'ON' if self.auto_step else 'OFF'}"
        ]
        
        y_offset = 10
        for instruction in instructions:
            text = font.render(instruction, True, (255, 255, 255))
            # Add black outline
            outline = font.render(instruction, True, (0, 0, 0))
            self.screen.blit(outline, (11, y_offset + 1))
            self.screen.blit(text, (10, y_offset))
            y_offset += 25

    def handle_input(self):
        """Handle input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_r:
                    print("Restarting simulation...")
                    self.fire_model.reset()
                    self.fire_model.ignite(self.grid_size // 2, self.grid_size // 2)
                    self.step_count = 0
                elif event.key == pygame.K_SPACE:
                    self.auto_step = not self.auto_step
                    print(f"Auto-step: {'ON' if self.auto_step else 'OFF'}")
                self.keys.add(event.key)
            elif event.type == pygame.KEYUP:
                self.keys.discard(event.key)
            elif event.type == pygame.MOUSEMOTION:
                if pygame.mouse.get_pressed()[0]:  # Left mouse button
                    dx, dy = event.rel
                    self.rotate_camera(dx * self.mouse_sensitivity, dy * self.mouse_sensitivity)
        
        # Handle continuous key presses
        self.handle_movement()
        return True

    def handle_movement(self):
        """Handle camera movement"""
        if pygame.K_w in self.keys:
            direction = self.camera.target - self.camera.pos
            direction = direction / np.linalg.norm(direction)
            self.camera.pos += direction * self.move_speed
            self.camera.target += direction * self.move_speed
            
        if pygame.K_s in self.keys:
            direction = self.camera.target - self.camera.pos
            direction = direction / np.linalg.norm(direction)
            self.camera.pos -= direction * self.move_speed
            self.camera.target -= direction * self.move_speed
            
        if pygame.K_a in self.keys:
            forward = self.camera.target - self.camera.pos
            right = np.cross(forward, self.camera.up)
            right = right / np.linalg.norm(right)
            self.camera.pos -= right * self.move_speed
            self.camera.target -= right * self.move_speed
            
        if pygame.K_d in self.keys:
            forward = self.camera.target - self.camera.pos
            right = np.cross(forward, self.camera.up)
            right = right / np.linalg.norm(right)
            self.camera.pos += right * self.move_speed
            self.camera.target += right * self.move_speed

    def rotate_camera(self, dx, dy):
        """Rotate camera around target"""
        # Calculate spherical coordinates
        to_camera = self.camera.pos - self.camera.target
        radius = np.linalg.norm(to_camera)
        
        # Current angles
        theta = math.atan2(to_camera[2], to_camera[0])  # Azimuth
        phi = math.acos(to_camera[1] / radius)  # Elevation
        
        # Update angles
        theta += dx
        phi += dy
        phi = max(0.1, min(math.pi - 0.1, phi))  # Clamp elevation
        
        # Convert back to cartesian
        new_pos = np.array([
            self.camera.target[0] + radius * math.sin(phi) * math.cos(theta),
            self.camera.target[1] + radius * math.cos(phi),
            self.camera.target[2] + radius * math.sin(phi) * math.sin(theta)
        ])
        
        self.camera.pos = new_pos

    def update_simulation(self):
        """Update fire simulation"""
        current_time = time.time()
        if self.auto_step and current_time - self.last_step_time > self.step_delay:
            self.fire_model.spread_fire()
            self.step_count += 1
            self.last_step_time = current_time
            
            if self.step_count % 10 == 0:
                print(f"Simulation step: {self.step_count}")

    def run(self):
        """Main game loop"""
        print("3D Forest Fire Simulation - Software Rendering")
        print("Controls:")
        print("  WASD - Move camera")
        print("  Left click + drag - Rotate camera")
        print("  Space - Toggle auto-step")
        print("  R - Restart simulation")
        print("  ESC - Quit")
        
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Handle input
            running = self.handle_input()
            
            # Update simulation
            self.update_simulation()
            
            # Render
            self.render_scene()
            
            # Control frame rate
            clock.tick(30)  # 30 FPS for good performance
        
        pygame.quit()
        print("Simulation ended.")

def main():
    try:
        sim = FireSimulation3DPygame(grid_size=15)
        sim.run()
    except Exception as e:
        print(f"Simulation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
