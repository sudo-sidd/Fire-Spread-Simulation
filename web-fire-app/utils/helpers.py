"""
Utility functions for the Fire Spread Simulation Web Application
"""

import numpy as np
from typing import Tuple, List, Dict, Any
import json
import base64
import io
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def image_to_base64(image_array: np.ndarray, format: str = 'PNG') -> str:
    """Convert numpy array to base64 encoded image string"""
    try:
        # Ensure proper data type
        if image_array.dtype != np.uint8:
            image_array = (image_array * 255).astype(np.uint8)
        
        # Convert to PIL Image
        if len(image_array.shape) == 2:  # Grayscale
            pil_image = Image.fromarray(image_array, mode='L')
        elif image_array.shape[2] == 3:  # RGB
            pil_image = Image.fromarray(image_array, mode='RGB')
        elif image_array.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(image_array, mode='RGBA')
        else:
            raise ValueError(f"Unsupported image shape: {image_array.shape}")
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format=format)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/{format.lower()};base64,{img_str}"
        
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        raise

def base64_to_image(base64_string: str) -> np.ndarray:
    """Convert base64 encoded image string to numpy array"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        # Decode base64
        img_data = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        img = Image.open(io.BytesIO(img_data))
        
        # Convert to numpy array
        return np.array(img)
        
    except Exception as e:
        logger.error(f"Error converting base64 to image: {e}")
        raise

def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate latitude and longitude coordinates"""
    return (-90 <= lat <= 90) and (-180 <= lon <= 180)

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula (in km)"""
    from math import radians, sin, cos, sqrt, atan2
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Earth's radius in kilometers
    earth_radius = 6371.0
    
    return earth_radius * c

def resize_image(image_array: np.ndarray, target_size: Tuple[int, int], 
                method: str = 'nearest') -> np.ndarray:
    """Resize image array to target size"""
    try:
        pil_image = Image.fromarray(image_array)
        
        # Select resampling method
        resample_methods = {
            'nearest': Image.NEAREST,
            'bilinear': Image.BILINEAR,
            'bicubic': Image.BICUBIC,
            'lanczos': Image.LANCZOS
        }
        
        resample = resample_methods.get(method, Image.NEAREST)
        resized_image = pil_image.resize(target_size, resample)
        
        return np.array(resized_image)
        
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        raise

def create_color_palette(terrain_types: Dict[str, Dict]) -> Dict[Tuple[int, int, int], str]:
    """Create color palette mapping from terrain configuration"""
    color_palette = {}
    
    for terrain_type, properties in terrain_types.items():
        color = tuple(properties['color'])
        color_palette[color] = terrain_type
    
    return color_palette

def analyze_image_histogram(image_array: np.ndarray) -> Dict[str, Any]:
    """Analyze image color histogram"""
    try:
        # Flatten image to get all pixels
        pixels = image_array.reshape(-1, image_array.shape[-1])
        
        # Calculate histogram for each channel
        histograms = {}
        if image_array.shape[-1] == 3:  # RGB
            channels = ['red', 'green', 'blue']
        elif image_array.shape[-1] == 4:  # RGBA
            channels = ['red', 'green', 'blue', 'alpha']
        else:
            channels = ['intensity']
        
        for i, channel in enumerate(channels):
            hist, bins = np.histogram(pixels[:, i], bins=256, range=(0, 256))
            histograms[channel] = {
                'histogram': hist.tolist(),
                'bins': bins.tolist(),
                'mean': float(np.mean(pixels[:, i])),
                'std': float(np.std(pixels[:, i]))
            }
        
        return {
            'histograms': histograms,
            'image_stats': {
                'width': image_array.shape[1],
                'height': image_array.shape[0],
                'channels': image_array.shape[-1] if len(image_array.shape) > 2 else 1,
                'total_pixels': image_array.shape[0] * image_array.shape[1]
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing image histogram: {e}")
        raise

def generate_simulation_summary(simulation_data: Dict) -> Dict[str, Any]:
    """Generate summary statistics for simulation data"""
    try:
        summary = {
            'duration': {
                'total_steps': simulation_data.get('current_step', 0),
                'estimated_time_hours': simulation_data.get('current_step', 0) * 0.25  # Assuming 15min per step
            },
            'area_impact': {
                'total_burned_km2': simulation_data.get('statistics', {}).get('total_burned_area_km2', 0),
                'burning_cells': simulation_data.get('statistics', {}).get('burning_cells', 0),
                'burned_cells': simulation_data.get('statistics', {}).get('burned_cells', 0)
            },
            'fire_behavior': {
                'peak_burning_cells': 0,
                'spread_rate': 0,
                'total_ignition_points': 0
            }
        }
        
        # Calculate peak burning cells from history
        step_history = simulation_data.get('step_history', [])
        if step_history:
            burning_counts = [step.get('burning_cells', 0) for step in step_history]
            summary['fire_behavior']['peak_burning_cells'] = max(burning_counts) if burning_counts else 0
            
            # Calculate spread rate (cells burned per step)
            if len(step_history) > 1:
                total_spread = sum(step.get('new_ignitions', 0) for step in step_history)
                summary['fire_behavior']['spread_rate'] = total_spread / len(step_history)
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating simulation summary: {e}")
        return {}

def create_terrain_mask(terrain_array: np.ndarray, terrain_type: str, 
                       color_palette: Dict[Tuple[int, int, int], str]) -> np.ndarray:
    """Create a boolean mask for specific terrain type"""
    try:
        mask = np.zeros(terrain_array.shape[:2], dtype=bool)
        
        # Find target color for terrain type
        target_color = None
        for color, t_type in color_palette.items():
            if t_type == terrain_type:
                target_color = color
                break
        
        if target_color is None:
            logger.warning(f"Terrain type '{terrain_type}' not found in color palette")
            return mask
        
        # Create mask for pixels matching target color (with tolerance)
        tolerance = 10
        for i, channel_value in enumerate(target_color):
            if i < terrain_array.shape[2]:
                channel_mask = np.abs(terrain_array[:, :, i] - channel_value) <= tolerance
                if i == 0:
                    mask = channel_mask
                else:
                    mask = mask & channel_mask
        
        return mask
        
    except Exception as e:
        logger.error(f"Error creating terrain mask: {e}")
        return np.zeros(terrain_array.shape[:2], dtype=bool)

def apply_gaussian_blur(image_array: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """Apply Gaussian blur to image array"""
    try:
        from scipy import ndimage
        
        # Apply Gaussian filter to each channel
        if len(image_array.shape) == 3:
            blurred = np.zeros_like(image_array)
            for i in range(image_array.shape[2]):
                blurred[:, :, i] = ndimage.gaussian_filter(image_array[:, :, i], sigma=sigma)
            return blurred
        else:
            return ndimage.gaussian_filter(image_array, sigma=sigma)
            
    except ImportError:
        logger.warning("scipy not available, using simple averaging for blur")
        # Simple averaging blur fallback
        kernel_size = max(1, int(sigma * 2))
        kernel = np.ones((kernel_size, kernel_size)) / (kernel_size * kernel_size)
        
        if len(image_array.shape) == 3:
            blurred = np.zeros_like(image_array)
            for i in range(image_array.shape[2]):
                blurred[:, :, i] = np.convolve(image_array[:, :, i].flatten(), 
                                             kernel.flatten(), mode='same').reshape(image_array.shape[:2])
            return blurred
        else:
            return np.convolve(image_array.flatten(), 
                             kernel.flatten(), mode='same').reshape(image_array.shape)
    
    except Exception as e:
        logger.error(f"Error applying blur: {e}")
        return image_array

def save_json_data(data: Dict[str, Any], filepath: str) -> bool:
    """Save data as JSON file"""
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON data: {e}")
        return False

def load_json_data(filepath: str) -> Dict[str, Any]:
    """Load data from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON data: {e}")
        return {}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))
