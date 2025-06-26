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

def download_satellite_image(lat, lon, zoom=13, size=(512, 512), save_path='satellite_image.png'):
    # Use public Sentinel-2 WMS layer (from Sentinel Hub)
    tile_url = (
        f"https://services.sentinel-hub.com/ogc/wms/"
        f"demo?REQUEST=GetMap&SERVICE=WMS&VERSION=1.3.0&"
        f"BBOX={lat-0.02},{lon-0.02},{lat+0.02},{lon+0.02}&"
        f"CRS=EPSG:4326&WIDTH={size[0]}&HEIGHT={size[1]}&"
        f"LAYERS=TRUE_COLOR&FORMAT=image/png&TRANSPARENT=FALSE&"
        f"TIME=2023-07-01/2023-07-10"  # Date range for recent imagery
    )

    print(f"Fetching satellite image for lat={lat}, lon={lon}")
    response = requests.get(tile_url)

    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Image saved to: {save_path}")
    else:
        print("Failed to download image. Status code:", response.status_code)

def visualize_on_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=13)
    folium.TileLayer(
        tiles="https://services.sentinel-hub.com/ogc/wms/demo"
              "?REQUEST=GetMap&SERVICE=WMS&VERSION=1.3.0&"
              "LAYERS=TRUE_COLOR&FORMAT=image/png&"
              "TIME=2023-07-01/2023-07-10",
        attr='Sentinel-Hub',
        name='Sentinel-2',
        overlay=True,
        control=True,
    ).add_to(m)
    folium.Marker([lat, lon], tooltip="Center").add_to(m)
    return m

def km_to_deg(km):
    return km / 111.0

def get_worldcover_matrix(lat, lon, radius_km=1):
    # Convert to bounding box
    delta = km_to_deg(radius_km)
    min_lon = lon - delta
    max_lon = lon + delta
    min_lat = lat - delta
    max_lat = lat + delta
    bbox = [min_lon, min_lat, max_lon, max_lat]
    region = box(*bbox)

    # Load STAC client
    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
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

    # Plot
    plt.imshow(matrix, cmap="tab20")
    plt.title("ESA WorldCover Land Classification")
    plt.colorbar()
    plt.savefig("land_cover_matrix.png")

    print("[✔] Matrix shape:", matrix.shape)
    return matrix

if __name__ == "__main__":
    ...
