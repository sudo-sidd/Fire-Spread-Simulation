import folium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from PIL import Image
import time
import os
import requests
import planetary_computer
import geopandas as gpd
from pystac_client import Client
from shapely.geometry import box, Point
import stackstac
import rioxarray
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from typing import Tuple, Optional
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TerrainExtractor:
    """
    A class for extracting terrain and satellite data for a given geographic location.
    
    This class provides functionality to:
    - Download satellite images from Sentinel-2
    - Extract land cover data from ESA WorldCover
    - Visualize data on interactive maps
    - Generate terrain matrices for analysis
    """
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the TerrainExtractor.
        
        Args:
            output_dir (str): Directory to save output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configuration constants
        self.SENTINEL_WMS_URL = "https://services.sentinel-hub.com/ogc/wms/demo"
        self.PLANETARY_COMPUTER_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
        self.KM_TO_DEGREE_CONVERSION = 111.0
        
        # Default parameters
        self.default_date_range = "2023-07-01/2023-07-10"
        self.default_image_size = (512, 512)
        self.default_zoom = 13
        
        # Store current location data
        self.current_lat: Optional[float] = None
        self.current_lon: Optional[float] = None
        self.current_bbox: Optional[list] = None
        self.land_cover_matrix: Optional[np.ndarray] = None
        
    def set_location(self, lat: float, lon: float) -> None:
        """
        Set the current location for data extraction.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
        """
        self.current_lat = lat
        self.current_lon = lon
        logger.info(f"Location set to: {lat}, {lon}")
        
    def km_to_degrees(self, km: float) -> float:
        """
        Convert kilometers to degrees (approximate).
        
        Args:
            km (float): Distance in kilometers
            
        Returns:
            float: Distance in degrees
        """
        return km / self.KM_TO_DEGREE_CONVERSION
    
    def calculate_bbox(self, radius_km: float = 1.0) -> list:
        """
        Calculate bounding box for the current location.
        
        Args:
            radius_km (float): Radius in kilometers around the center point
            
        Returns:
            list: Bounding box [min_lon, min_lat, max_lon, max_lat]
            
        Raises:
            ValueError: If location is not set
        """
        if self.current_lat is None or self.current_lon is None:
            raise ValueError("Location must be set before calculating bounding box")
            
        delta = self.km_to_degrees(radius_km)
        bbox = [
            self.current_lon - delta,  # min_lon
            self.current_lat - delta,  # min_lat
            self.current_lon + delta,  # max_lon
            self.current_lat + delta   # max_lat
        ]
        self.current_bbox = bbox
        return bbox
    
    def extract_original_image(self, 
                             radius_km: float = 1.0,
                             size: Tuple[int, int] = None, 
                             save_filename: str = 'original_image.png',
                             date_range: str = None) -> np.ndarray:
        """
        Extract original satellite image from Sentinel-2 for the specified radius around the location.
        
        Args:
            radius_km (float): Radius in kilometers around the center point
            size (Tuple[int, int]): Image size (width, height)
            save_filename (str): Filename to save the image
            date_range (str): Date range for imagery
            
        Returns:
            np.ndarray: Original satellite image as numpy array (RGB)
            
        Raises:
            ValueError: If location is not set
        """
        if self.current_lat is None or self.current_lon is None:
            raise ValueError("Location must be set before extracting original image")
            
        size = size or self.default_image_size
        date_range = date_range or self.default_date_range
        save_path = self.output_dir / save_filename
        
        # Calculate bounding box based on radius
        delta = self.km_to_degrees(radius_km)
        bbox_str = f"{self.current_lat-delta},{self.current_lon-delta},{self.current_lat+delta},{self.current_lon+delta}"
        
        tile_url = (
            f"{self.SENTINEL_WMS_URL}?"
            f"REQUEST=GetMap&SERVICE=WMS&VERSION=1.3.0&"
            f"BBOX={bbox_str}&"
            f"CRS=EPSG:4326&WIDTH={size[0]}&HEIGHT={size[1]}&"
            f"LAYERS=TRUE_COLOR&FORMAT=image/png&TRANSPARENT=FALSE&"
            f"TIME={date_range}"
        )
        
        try:
            logger.info(f"Extracting original image for lat={self.current_lat}, lon={self.current_lon}, radius={radius_km}km")
            response = requests.get(tile_url, timeout=30)
            response.raise_for_status()
            
            # Save image
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            # Load image as numpy array
            from PIL import Image
            image = Image.open(save_path)
            image_array = np.array(image)
            
            logger.info(f"Original image extracted. Shape: {image_array.shape}, saved to: {save_path}")
            return image_array
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to extract original image: {e}")
            raise
        except IOError as e:
            logger.error(f"Failed to process image: {e}")
            raise

    def download_satellite_image(self, 
                                zoom: int = None, 
                                size: Tuple[int, int] = None, 
                                save_filename: str = 'satellite_image.png',
                                date_range: str = None) -> bool:
        """
        Download satellite image from Sentinel-2 for the current location.
        [DEPRECATED: Use extract_original_image for better functionality]
        
        Args:
            zoom (int): Zoom level (not used in current implementation but kept for API consistency)
            size (Tuple[int, int]): Image size (width, height)
            save_filename (str): Filename to save the image
            date_range (str): Date range for imagery
            
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            ValueError: If location is not set
        """
        try:
            self.extract_original_image(
                radius_km=1.0, 
                size=size, 
                save_filename=save_filename, 
                date_range=date_range
            )
            return True
        except Exception:
            return False
    
    def create_interactive_map(self, 
                              zoom_start: int = None,
                              save_filename: str = 'map_output.html') -> folium.Map:
        """
        Create an interactive map with satellite overlay for the current location.
        
        Args:
            zoom_start (int): Initial zoom level
            save_filename (str): Filename to save the map
            
        Returns:
            folium.Map: The created map object
            
        Raises:
            ValueError: If location is not set
        """
        if self.current_lat is None or self.current_lon is None:
            raise ValueError("Location must be set before creating map")
            
        zoom_start = zoom_start or self.default_zoom
        save_path = self.output_dir / save_filename
        
        try:
            m = folium.Map(location=[self.current_lat, self.current_lon], zoom_start=zoom_start)
            
            # Add satellite layer
            folium.TileLayer(
                tiles=f"{self.SENTINEL_WMS_URL}"
                      f"?REQUEST=GetMap&SERVICE=WMS&VERSION=1.3.0&"
                      f"LAYERS=TRUE_COLOR&FORMAT=image/png&"
                      f"TIME={self.default_date_range}",
                attr='Sentinel-Hub',
                name='Sentinel-2',
                overlay=True,
                control=True,
            ).add_to(m)
            
            # Add marker for center point
            folium.Marker(
                [self.current_lat, self.current_lon], 
                tooltip=f"Center: {self.current_lat:.4f}, {self.current_lon:.4f}"
            ).add_to(m)
            
            # Save map
            m.save(str(save_path))
            logger.info(f"Interactive map saved to: {save_path}")
            
            return m
            
        except Exception as e:
            logger.error(f"Failed to create interactive map: {e}")
            raise
    
    def extract_features_from_image(self, 
                                   radius_km: float = 1.0,
                                   save_matrix_plot: bool = True,
                                   save_colored_image: bool = True,
                                   matrix_filename: str = 'feature_matrix.png',
                                   colored_filename: str = 'colored_features.png') -> dict:
        """
        Extract features from the image and map values for each category.
        Returns matrix values and colored image for each land cover category.
        
        Categories mapped:
        - 10: Tree cover / Forest (Green)
        - 20: Shrubland (Light Green)
        - 30: Grassland (Yellow Green)
        - 40: Cropland (Yellow)
        - 50: Built-up / Urban (Red)
        - 60: Bare/sparse vegetation (Brown)
        - 70: Snow and ice (White)
        - 80: Permanent water bodies (Blue)
        - 90: Herbaceous wetland (Cyan)
        - 95: Mangroves (Dark Green)
        - 100: Moss and lichen (Light Brown)
        
        Args:
            radius_km (float): Radius in kilometers around the center point
            save_matrix_plot (bool): Whether to save a plot of the matrix
            save_colored_image (bool): Whether to save colored feature image
            matrix_filename (str): Filename for the matrix plot
            colored_filename (str): Filename for the colored image
            
        Returns:
            dict: Contains 'matrix', 'colored_image', 'category_stats', 'category_mapping'
            
        Raises:
            ValueError: If location is not set
        """
        if self.current_lat is None or self.current_lon is None:
            raise ValueError("Location must be set before extracting features")
            
        try:
            # Get land cover matrix
            matrix = self.extract_land_cover_matrix(radius_km, save_plot=False)
            
            # Define category mapping with colors and names
            category_mapping = {
                10: {'name': 'Tree cover/Forest', 'color': [34, 139, 34], 'rgb': (34, 139, 34)},     # Forest Green
                20: {'name': 'Shrubland', 'color': [154, 205, 50], 'rgb': (154, 205, 50)},          # Yellow Green
                30: {'name': 'Grassland', 'color': [173, 255, 47], 'rgb': (173, 255, 47)},          # Green Yellow
                40: {'name': 'Cropland', 'color': [255, 215, 0], 'rgb': (255, 215, 0)},             # Gold
                50: {'name': 'Built-up/Urban', 'color': [220, 20, 60], 'rgb': (220, 20, 60)},       # Crimson
                60: {'name': 'Bare/sparse vegetation', 'color': [210, 180, 140], 'rgb': (210, 180, 140)}, # Tan
                70: {'name': 'Snow and ice', 'color': [255, 250, 250], 'rgb': (255, 250, 250)},     # Snow
                80: {'name': 'Water bodies', 'color': [0, 191, 255], 'rgb': (0, 191, 255)},         # Deep Sky Blue
                90: {'name': 'Herbaceous wetland', 'color': [64, 224, 208], 'rgb': (64, 224, 208)}, # Turquoise
                95: {'name': 'Mangroves', 'color': [0, 100, 0], 'rgb': (0, 100, 0)},                # Dark Green
                100: {'name': 'Moss and lichen', 'color': [188, 143, 143], 'rgb': (188, 143, 143)}, # Rosy Brown
                0: {'name': 'No data', 'color': [0, 0, 0], 'rgb': (0, 0, 0)}                        # Black
            }
            
            # Create colored image
            colored_image = self._create_colored_feature_image(matrix, category_mapping)
            
            # Calculate category statistics
            category_stats = self._calculate_category_stats(matrix, category_mapping)
            
            # Save visualizations
            if save_matrix_plot:
                self._save_feature_matrix_plot(matrix, category_mapping, matrix_filename)
            
            if save_colored_image:
                self._save_colored_feature_image(colored_image, colored_filename)
            
            logger.info(f"✔ Features extracted. Matrix shape: {matrix.shape}")
            logger.info(f"✔ Found {len(category_stats)} different land cover categories")
            
            return {
                'matrix': matrix,
                'colored_image': colored_image,
                'category_stats': category_stats,
                'category_mapping': category_mapping
            }
            
        except Exception as e:
            logger.error(f"Failed to extract features from image: {e}")
            raise
    
    def _create_colored_feature_image(self, matrix: np.ndarray, category_mapping: dict) -> np.ndarray:
        """
        Create a colored image based on land cover categories.
        
        Args:
            matrix (np.ndarray): Land cover matrix
            category_mapping (dict): Mapping of categories to colors
            
        Returns:
            np.ndarray: RGB colored image
        """
        colored_image = np.zeros((*matrix.shape, 3), dtype=np.uint8)
        
        for category_id, info in category_mapping.items():
            mask = (matrix == category_id)
            colored_image[mask] = info['color']
        
        return colored_image
    
    def _calculate_category_stats(self, matrix: np.ndarray, category_mapping: dict) -> dict:
        """
        Calculate statistics for each land cover category.
        
        Args:
            matrix (np.ndarray): Land cover matrix
            category_mapping (dict): Mapping of categories
            
        Returns:
            dict: Statistics for each category
        """
        unique_values, counts = np.unique(matrix, return_counts=True)
        total_pixels = matrix.size
        
        stats = {}
        for value, count in zip(unique_values, counts):
            if value in category_mapping:
                stats[value] = {
                    'name': category_mapping[value]['name'],
                    'pixel_count': int(count),
                    'percentage': float(count / total_pixels * 100),
                    'color': category_mapping[value]['rgb']
                }
        
        return stats
    
    def _save_feature_matrix_plot(self, matrix: np.ndarray, category_mapping: dict, filename: str) -> None:
        """
        Save a detailed plot of the feature matrix with legend.
        
        Args:
            matrix (np.ndarray): Land cover matrix
            category_mapping (dict): Category mapping
            filename (str): Output filename
        """
        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # Plot 1: Original matrix with color mapping
            im1 = ax1.imshow(matrix, cmap="tab20")
            ax1.set_title("Land Cover Classification Matrix")
            ax1.set_xlabel("Longitude (pixels)")
            ax1.set_ylabel("Latitude (pixels)")
            
            # Add colorbar for matrix
            cbar1 = plt.colorbar(im1, ax=ax1, label="Land Cover Class ID")
            
            # Plot 2: Colored feature image
            colored_image = self._create_colored_feature_image(matrix, category_mapping)
            ax2.imshow(colored_image)
            ax2.set_title("Color-Coded Land Cover Features")
            ax2.set_xlabel("Longitude (pixels)")
            ax2.set_ylabel("Latitude (pixels)")
            
            # Create legend for categories present in the image
            unique_values = np.unique(matrix)
            legend_elements = []
            for value in unique_values:
                if value in category_mapping:
                    color = np.array(category_mapping[value]['color']) / 255.0
                    name = category_mapping[value]['name']
                    legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=color, label=f"{value}: {name}"))
            
            if legend_elements:
                ax2.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left')
            
            plt.tight_layout()
            
            save_path = self.output_dir / filename
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Feature matrix plot saved to: {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save feature matrix plot: {e}")
    
    def _save_colored_feature_image(self, colored_image: np.ndarray, filename: str) -> None:
        """
        Save the colored feature image.
        
        Args:
            colored_image (np.ndarray): Colored image array
            filename (str): Output filename
        """
        try:
            save_path = self.output_dir / filename
            from PIL import Image
            image = Image.fromarray(colored_image)
            image.save(save_path)
            
            logger.info(f"Colored feature image saved to: {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save colored feature image: {e}")

    def extract_land_cover_matrix(self, 
                                 radius_km: float = 1.0,
                                 save_plot: bool = True,
                                 plot_filename: str = 'land_cover_matrix.png') -> np.ndarray:
        """
        Extract land cover matrix from ESA WorldCover data.
        
        Args:
            radius_km (float): Radius in kilometers around the center point
            save_plot (bool): Whether to save a plot of the matrix
            plot_filename (str): Filename for the plot
            
        Returns:
            np.ndarray: Land cover matrix
            
        Raises:
            ValueError: If location is not set
            Exception: If no land cover data is found
        """
        if self.current_lat is None or self.current_lon is None:
            raise ValueError("Location must be set before extracting land cover matrix")
            
        try:
            # Calculate bounding box
            bbox = self.calculate_bbox(radius_km)
            
            # Load STAC client
            catalog = Client.open(self.PLANETARY_COMPUTER_URL)
            search = catalog.search(
                collections=["esa-worldcover"],
                bbox=bbox,
                limit=1
            )
            
            items = list(search.get_items())
            if not items:
                raise Exception("❌ No land cover data found for this location.")
            
            # Sign the asset URL
            signed_item = planetary_computer.sign(items[0])
            asset = signed_item.assets["map"]
            
            # Load with rioxarray and clip
            data = rioxarray.open_rasterio(asset.href, masked=True)
            data = data.rio.write_crs("EPSG:4326")
            clipped = data.rio.clip_box(*bbox)
            
            # Convert to NumPy
            matrix = clipped.squeeze().values.astype(np.uint8)
            self.land_cover_matrix = matrix
            
            # Create and save plot if requested
            if save_plot:
                self._save_land_cover_plot(matrix, plot_filename)
            
            logger.info(f"✔ Land cover matrix extracted. Shape: {matrix.shape}")
            return matrix
            
        except Exception as e:
            logger.error(f"Failed to extract land cover matrix: {e}")
            raise
    
    def _save_land_cover_plot(self, matrix: np.ndarray, filename: str) -> None:
        """
        Save a plot of the land cover matrix.
        
        Args:
            matrix (np.ndarray): Land cover matrix
            filename (str): Output filename
        """
        try:
            plt.figure(figsize=(10, 8))
            plt.imshow(matrix, cmap="tab20")
            plt.title("ESA WorldCover Land Classification")
            plt.colorbar(label="Land Cover Class")
            plt.xlabel("Longitude (pixels)")
            plt.ylabel("Latitude (pixels)")
            
            save_path = self.output_dir / filename
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            plt.close()  # Close to free memory
            
            logger.info(f"Land cover plot saved to: {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save land cover plot: {e}")
    
    def process_location(self, 
                        lat: float, 
                        lon: float, 
                        radius_km: float = 1.0,
                        extract_original_image: bool = True,
                        extract_features: bool = True,
                        create_map: bool = True) -> dict:
        """
        Process a location by extracting all available data.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            radius_km (float): Radius for data extraction
            extract_original_image (bool): Whether to extract original satellite image
            extract_features (bool): Whether to extract and categorize land cover features
            create_map (bool): Whether to create interactive map
            
        Returns:
            dict: Summary of processed data including original image and features
        """
        self.set_location(lat, lon)
        results = {
            'latitude': lat,
            'longitude': lon,
            'radius_km': radius_km,
            'original_image': None,
            'features': None,
            'interactive_map': False,
            'bbox': None
        }
        
        try:
            # Calculate bounding box
            bbox = self.calculate_bbox(radius_km)
            results['bbox'] = bbox
            
            # Extract original satellite image
            if extract_original_image:
                try:
                    original_image = self.extract_original_image(
                        radius_km=radius_km,
                        save_filename=f'original_image_{radius_km}km.png'
                    )
                    results['original_image'] = original_image
                    logger.info("✓ Original image extraction successful")
                except Exception as e:
                    logger.warning(f"Original image extraction failed: {e}")
                    results['original_image'] = None
            
            # Extract features and create categorized visualization
            if extract_features:
                try:
                    features = self.extract_features_from_image(
                        radius_km=radius_km,
                        matrix_filename=f'feature_matrix_{radius_km}km.png',
                        colored_filename=f'colored_features_{radius_km}km.png'
                    )
                    results['features'] = features
                    logger.info("✓ Feature extraction successful")
                except Exception as e:
                    logger.warning(f"Feature extraction failed: {e}")
                    results['features'] = None
            
            # Create interactive map
            if create_map:
                try:
                    map_obj = self.create_interactive_map(save_filename=f'map_{radius_km}km.html')
                    results['interactive_map'] = True
                    logger.info("✓ Interactive map creation successful")
                except Exception as e:
                    logger.warning(f"Interactive map creation failed: {e}")
                    results['interactive_map'] = False
            
            logger.info("Location processing completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error processing location: {e}")
            # Return partial results even if some operations failed
            return results


def main():
    """
    Example usage of the TerrainExtractor class.
    Demonstrates extraction of original images and feature categorization.
    """
    # Initialize extractor
    extractor = TerrainExtractor(output_dir="terrain_output")
    
    # Example coordinates (you can change these)
    lat, lon = 11.045433, 77.096564
    
    try:
        # Process the location with new functionality
        results = extractor.process_location(
            lat=lat,
            lon=lon,
            radius_km=2.0,
            extract_original_image=True,
            extract_features=True,
            create_map=True
        )
        
        print("Processing Results:")
        print(f"Location: {results['latitude']}, {results['longitude']}")
        print(f"Radius: {results['radius_km']} km")
        print(f"Bounding Box: {results['bbox']}")
        print(f"Interactive Map Created: {results['interactive_map']}")
        
        if results['original_image'] is not None:
            print(f"Original Image Shape: {results['original_image'].shape}")
            print(f"Original Image Type: {results['original_image'].dtype}")
        
        if results['features'] is not None:
            features = results['features']
            print(f"Feature Matrix Shape: {features['matrix'].shape}")
            print(f"Colored Image Shape: {features['colored_image'].shape}")
            print("\nLand Cover Categories Found:")
            
            for category_id, stats in features['category_stats'].items():
                print(f"  {category_id}: {stats['name']}")
                print(f"    - Pixels: {stats['pixel_count']} ({stats['percentage']:.2f}%)")
                print(f"    - Color (RGB): {stats['color']}")
        
        print(f"\nFiles saved in: {extractor.output_dir}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
