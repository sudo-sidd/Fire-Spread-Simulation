#!/usr/bin/env python3
"""
Fire Spread Simulation API Demo
Demonstrates how to use the simulation API programmatically
"""

import requests
import json
import time
import base64
from PIL import Image
import io

# Configuration
API_BASE_URL = "http://localhost:5000/api"
DEMO_LOCATION = {"lat": 39.8283, "lon": -98.5795}  # Center of USA

def test_api_connection():
    """Test if the API is accessible"""
    try:
        response = requests.get(f"{API_BASE_URL.replace('/api', '')}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def extract_terrain(lat, lon):
    """Extract terrain data for given coordinates"""
    print(f"🗺️  Extracting terrain for ({lat}, {lon})...")
    
    payload = {
        "lat": lat,
        "lon": lon,
        "zoom": 15,
        "grid_size": [100, 100]  # Smaller grid for demo
    }
    
    response = requests.post(f"{API_BASE_URL}/map/select-area", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print("✅ Terrain extracted successfully")
            return data
        else:
            print(f"❌ Terrain extraction failed: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ API request failed: {response.status_code}")
    
    return None

def create_simulation(terrain_data):
    """Create a new fire simulation"""
    print("🔥 Creating simulation...")
    
    payload = {
        "width": 100,
        "height": 100,
        "terrain_data": {
            "bitmap": terrain_data["terrain_image"],
            "color_map": terrain_data["color_map"]
        }
    }
    
    response = requests.post(f"{API_BASE_URL}/simulation/create", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print(f"✅ Simulation created: {data['simulation_id']}")
            return data["simulation_id"]
        else:
            print(f"❌ Simulation creation failed: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ API request failed: {response.status_code}")
    
    return None

def ignite_fire(sim_id, x, y):
    """Start a fire at given coordinates"""
    print(f"🔥 Igniting fire at ({x}, {y})...")
    
    payload = {
        "simulation_id": sim_id,
        "x": x,
        "y": y
    }
    
    response = requests.post(f"{API_BASE_URL}/simulation/ignite", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print("✅ Fire ignited successfully")
            return data
        else:
            print(f"❌ Ignition failed: {data.get('message', 'Unknown error')}")
    else:
        print(f"❌ API request failed: {response.status_code}")
    
    return None

def run_simulation_steps(sim_id, num_steps=10):
    """Run simulation for specified number of steps"""
    print(f"⏭️  Running {num_steps} simulation steps...")
    
    results = []
    
    for step in range(num_steps):
        payload = {
            "simulation_id": sim_id,
            "steps": 1
        }
        
        response = requests.post(f"{API_BASE_URL}/simulation/step", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                stats = data["statistics"]
                print(f"   Step {step + 1}: Burning={stats['burning_cells']}, "
                      f"Burned={stats['burned_cells']}, "
                      f"Area={stats.get('total_burned_area_km2', 0):.4f} km²")
                
                results.append(data)
                
                # Stop if no more active fires
                if not stats.get("is_active", True):
                    print("🏁 Simulation completed - no more active fires")
                    break
            else:
                print(f"❌ Step failed: {data.get('error', 'Unknown error')}")
                break
        else:
            print(f"❌ API request failed: {response.status_code}")
            break
        
        time.sleep(0.5)  # Small delay between steps
    
    return results

def set_weather_conditions(sim_id):
    """Set custom weather conditions"""
    print("🌦️  Setting weather conditions...")
    
    payload = {
        "simulation_id": sim_id,
        "wind_speed": 15.0,      # km/h
        "wind_direction": 45.0,   # degrees
        "humidity": 30.0,         # %
        "temperature": 35.0,      # °C
        "precipitation": 0.0      # mm/h
    }
    
    response = requests.post(f"{API_BASE_URL}/simulation/weather", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            print("✅ Weather conditions updated")
            return True
        else:
            print(f"❌ Weather update failed: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ API request failed: {response.status_code}")
    
    return False

def get_simulation_status(sim_id):
    """Get current simulation status"""
    response = requests.get(f"{API_BASE_URL}/simulation/status/{sim_id}")
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            return data["statistics"]
    
    return None

def export_simulation_data(sim_id):
    """Export simulation data"""
    print("💾 Exporting simulation data...")
    
    response = requests.get(f"{API_BASE_URL}/simulation/export/{sim_id}")
    
    if response.status_code == 200:
        data = response.json()
        if data["success"]:
            # Save to file
            filename = f"simulation_export_{sim_id}.json"
            with open(filename, 'w') as f:
                json.dump(data["export_data"], f, indent=2)
            
            print(f"✅ Data exported to {filename}")
            return filename
        else:
            print(f"❌ Export failed: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ API request failed: {response.status_code}")
    
    return None

def save_visualization(image_base64, filename):
    """Save visualization image to file"""
    try:
        # Remove data URL prefix
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # Decode and save
        img_data = base64.b64decode(image_base64)
        img = Image.open(io.BytesIO(img_data))
        img.save(filename)
        
        print(f"💾 Visualization saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save visualization: {e}")
        return False

def main():
    """Main demo function"""
    print("🔥 Fire Spread Simulation API Demo")
    print("=" * 40)
    
    # Test API connection
    print("🔗 Testing API connection...")
    if not test_api_connection():
        print("❌ Cannot connect to API. Make sure the server is running.")
        print("   Start with: python app.py")
        return
    
    print("✅ API connection successful")
    
    # Extract terrain
    terrain_data = extract_terrain(DEMO_LOCATION["lat"], DEMO_LOCATION["lon"])
    if not terrain_data:
        print("❌ Demo failed - could not extract terrain")
        return
    
    # Create simulation
    sim_id = create_simulation(terrain_data)
    if not sim_id:
        print("❌ Demo failed - could not create simulation")
        return
    
    # Set weather conditions
    set_weather_conditions(sim_id)
    
    # Ignite fires at multiple locations
    fire_locations = [(25, 25), (75, 75), (50, 25)]
    
    for x, y in fire_locations:
        result = ignite_fire(sim_id, x, y)
        if result and "visualization" in result:
            save_visualization(result["visualization"], f"ignition_{x}_{y}.png")
    
    # Run simulation
    results = run_simulation_steps(sim_id, 15)
    
    # Save final visualization
    if results and "visualization" in results[-1]:
        save_visualization(results[-1]["visualization"], "final_result.png")
    
    # Get final status
    final_status = get_simulation_status(sim_id)
    if final_status:
        print("\n📊 Final Statistics:")
        print(f"   Total Steps: {final_status['step']}")
        print(f"   Burned Cells: {final_status['burned_cells']}")
        print(f"   Burned Area: {final_status.get('total_burned_area_km2', 0):.4f} km²")
    
    # Export data
    export_file = export_simulation_data(sim_id)
    
    print("\n🎉 Demo completed successfully!")
    print("📁 Generated files:")
    print("   - ignition_*.png (fire ignition visualizations)")
    print("   - final_result.png (final simulation state)")
    if export_file:
        print(f"   - {export_file} (simulation data)")

if __name__ == "__main__":
    main()
