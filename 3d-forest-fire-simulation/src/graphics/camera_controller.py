from ursina import *

class CameraController(Entity):
    def __init__(self):
        super().__init__()
        self.camera_speed = 5
        self.rotation_speed = 100

    def update(self):
        # Camera movement
        if held_keys['w']:
            self.position += self.forward * self.camera_speed * time.dt
        if held_keys['s']:
            self.position -= self.forward * self.camera_speed * time.dt
        if held_keys['a']:
            self.position -= self.right * self.camera_speed * time.dt
        if held_keys['d']:
            self.position += self.right * self.camera_speed * time.dt

        # Camera rotation
        if held_keys['q']:
            self.rotation_y -= self.rotation_speed * time.dt
        if held_keys['e']:
            self.rotation_y += self.rotation_speed * time.dt

        # Camera height adjustment
        if held_keys['space']:
            self.position_y += self.camera_speed * time.dt
        if held_keys['left control']:
            self.position_y -= self.camera_speed * time.dt