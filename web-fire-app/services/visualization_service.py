"""
Visualization Service
Handles rendering of fire simulation overlays on maps
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2
from typing import Tuple, Optional
import base64
import io

from core.config import Config
from core.fire_engine import FireSimulation

class VisualizationService:
    """Service for creating fire simulation visualizations"""
    
    def __init__(self):
        self.fire_colors = Config.FIRE_COLORS
        
    def create_fire_overlay(self, fire_simulation: FireSimulation, 
                          alpha: float = 0.7) -> np.ndarray:
        """Create fire overlay image from simulation state"""
        
        fire_state = fire_simulation.get_fire_state_array()
        height, width = fire_state.shape
        
        # Create RGBA overlay
        overlay = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Color mapping for fire states
        color_map = {
            0: (0, 0, 0, 0),           # Normal - transparent
            1: (255, 0, 0, 200),       # Burning - bright red
            2: (64, 64, 64, 150),      # Burned - dark gray
            3: (255, 140, 0, 180)      # Smoldering - orange
        }
        
        for state, color in color_map.items():
            mask = fire_state == state
            overlay[mask] = color
        
        # Apply alpha blending
        if alpha != 1.0:
            overlay[:, :, 3] = (overlay[:, :, 3] * alpha).astype(np.uint8)
        
        return overlay
    
    def create_composite_image(self, terrain_image: np.ndarray, 
                             fire_overlay: np.ndarray) -> np.ndarray:
        """Combine terrain and fire overlay into single image"""
        
        # Ensure both images have same dimensions
        h, w = terrain_image.shape[:2]
        if fire_overlay.shape[:2] != (h, w):
            fire_overlay_pil = Image.fromarray(fire_overlay)
            fire_overlay_pil = fire_overlay_pil.resize((w, h), Image.NEAREST)
            fire_overlay = np.array(fire_overlay_pil)
        
        # Convert terrain to RGBA if needed
        if terrain_image.shape[2] == 3:
            terrain_rgba = np.zeros((h, w, 4), dtype=np.uint8)
            terrain_rgba[:, :, :3] = terrain_image
            terrain_rgba[:, :, 3] = 255  # Full opacity
        else:
            terrain_rgba = terrain_image.copy()
        
        # Alpha blend fire overlay onto terrain
        fire_alpha = fire_overlay[:, :, 3:4] / 255.0
        terrain_alpha = (1.0 - fire_alpha) * (terrain_rgba[:, :, 3:4] / 255.0)
        
        # Blend RGB channels
        result = np.zeros_like(terrain_rgba)
        for i in range(3):  # RGB channels
            result[:, :, i] = (
                fire_overlay[:, :, i] * fire_alpha.squeeze() +
                terrain_rgba[:, :, i] * terrain_alpha.squeeze()
            ).astype(np.uint8)
        
        # Combine alpha channels
        result[:, :, 3] = np.maximum(
            fire_overlay[:, :, 3], 
            terrain_rgba[:, :, 3]
        )
        
        return result
    
    def add_fire_effects(self, image: np.ndarray, 
                        fire_simulation: FireSimulation) -> np.ndarray:
        """Add visual effects like smoke and glow to fire visualization"""
        
        fire_state = fire_simulation.get_fire_state_array()
        enhanced_image = image.copy()
        
        # Add glow effect around burning areas
        burning_mask = fire_state == 1
        if np.any(burning_mask):
            enhanced_image = self._add_glow_effect(enhanced_image, burning_mask)
        
        # Add smoke effect
        if fire_simulation.burning_cells > 0:
            enhanced_image = self._add_smoke_effect(enhanced_image, fire_state)
        
        return enhanced_image
    
    def _add_glow_effect(self, image: np.ndarray, burning_mask: np.ndarray) -> np.ndarray:
        """Add glow effect around burning areas"""
        
        # Convert mask to image for processing
        glow_mask = (burning_mask * 255).astype(np.uint8)
        
        # Create glow by blurring the mask
        glow = cv2.GaussianBlur(glow_mask, (15, 15), 0)
        glow = cv2.GaussianBlur(glow, (15, 15), 0)  # Double blur for softer effect
        
        # Apply orange glow color
        glow_colored = np.zeros((*glow.shape, 3), dtype=np.uint8)
        glow_colored[:, :, 0] = glow  # Red channel
        glow_colored[:, :, 1] = glow // 2  # Green channel (orange effect)
        glow_colored[:, :, 2] = 0  # No blue
        
        # Blend with original image
        glow_alpha = (glow / 255.0 * 0.3)[:, :, np.newaxis]  # 30% opacity
        enhanced = image.copy()
        
        if image.shape[2] == 4:  # RGBA
            enhanced[:, :, :3] = (
                enhanced[:, :, :3] * (1 - glow_alpha) + 
                glow_colored * glow_alpha
            ).astype(np.uint8)
        else:  # RGB
            enhanced = (
                enhanced * (1 - glow_alpha) + 
                glow_colored * glow_alpha
            ).astype(np.uint8)
        
        return enhanced
    
    def _add_smoke_effect(self, image: np.ndarray, fire_state: np.ndarray) -> np.ndarray:
        """Add smoke effect over burning and recently burned areas"""
        
        # Create smoke mask (burning + recently burned areas)
        smoke_mask = ((fire_state == 1) | (fire_state == 2)).astype(np.uint8) * 255
        
        # Create smoke pattern with noise
        h, w = smoke_mask.shape
        noise = np.random.randint(0, 100, (h, w), dtype=np.uint8)
        smoke_pattern = cv2.addWeighted(smoke_mask, 0.7, noise, 0.3, 0)
        
        # Blur smoke for realistic effect
        smoke_blurred = cv2.GaussianBlur(smoke_pattern, (21, 21), 0)
        
        # Create gray smoke overlay
        smoke_overlay = np.zeros((*smoke_blurred.shape, 3), dtype=np.uint8)
        smoke_overlay[:, :, :] = smoke_blurred[:, :, np.newaxis]  # Gray smoke
        
        # Apply smoke with low opacity
        smoke_alpha = (smoke_blurred / 255.0 * 0.2)[:, :, np.newaxis]  # 20% opacity
        
        enhanced = image.copy()
        if image.shape[2] == 4:  # RGBA
            enhanced[:, :, :3] = (
                enhanced[:, :, :3] * (1 - smoke_alpha) + 
                smoke_overlay * smoke_alpha
            ).astype(np.uint8)
        else:  # RGB
            enhanced = (
                enhanced * (1 - smoke_alpha) + 
                smoke_overlay * smoke_alpha
            ).astype(np.uint8)
        
        return enhanced
    
    def create_legend(self, size: Tuple[int, int] = (200, 300)) -> np.ndarray:
        """Create legend image for fire simulation colors"""
        
        width, height = size
        legend = np.ones((height, width, 3), dtype=np.uint8) * 255  # White background
        
        # Legend items
        items = [
            ("Normal Terrain", (0, 128, 0)),
            ("Burning", (255, 0, 0)),
            ("Burned", (64, 64, 64)),
            ("Water", (0, 100, 200)),
            ("Urban", (128, 128, 128)),
            ("Agriculture", (255, 215, 0))
        ]
        
        # Draw legend items
        y_start = 20
        item_height = 30
        
        for i, (label, color) in enumerate(items):
            y = y_start + i * item_height
            
            # Draw color box
            legend[y:y+20, 10:30] = color
            
            # Add text label (simplified - in real implementation use PIL ImageDraw)
            # For now, we'll just create colored boxes
        
        return legend
    
    def image_to_base64(self, image: np.ndarray, format: str = 'PNG') -> str:
        """Convert numpy array image to base64 string"""
        
        # Convert to PIL Image
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        pil_image = Image.fromarray(image)
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/{format.lower()};base64,{img_str}"
    
    def create_time_series_gif(self, simulation_states: list, 
                             terrain_image: np.ndarray,
                             output_path: str,
                             duration: int = 500) -> bool:
        """Create animated GIF from simulation time series"""
        
        try:
            frames = []
            
            for fire_state in simulation_states:
                # Create fire overlay
                overlay = self._create_state_overlay(fire_state)
                
                # Composite with terrain
                composite = self.create_composite_image(terrain_image, overlay)
                
                # Convert to PIL Image
                frame = Image.fromarray(composite[:, :, :3])  # RGB only for GIF
                frames.append(frame)
            
            # Save as animated GIF
            if frames:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=duration,
                    loop=0
                )
                return True
            
        except Exception as e:
            print(f"Error creating GIF: {e}")
        
        return False
    
    def _create_state_overlay(self, fire_state: np.ndarray) -> np.ndarray:
        """Create overlay from fire state array"""
        
        height, width = fire_state.shape
        overlay = np.zeros((height, width, 4), dtype=np.uint8)
        
        # Apply colors based on state
        overlay[fire_state == 1] = [255, 0, 0, 200]    # Burning
        overlay[fire_state == 2] = [64, 64, 64, 150]   # Burned
        overlay[fire_state == 3] = [255, 140, 0, 180]  # Smoldering
        
        return overlay
