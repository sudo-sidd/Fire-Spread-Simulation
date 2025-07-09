#!/usr/bin/env python3
"""
Fire Spread Simulation Web Application - Setup Script
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or later is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing Python dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ["temp", "data", "static/images"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"   Created: {directory}")
    
    print("✅ Directories created")

def check_browser():
    """Check if a suitable browser is available"""
    print("🌐 Checking for browser...")
    
    browsers = ["google-chrome", "chromium-browser", "chromium"]
    
    for browser in browsers:
        try:
            subprocess.check_output(["which", browser], stderr=subprocess.DEVNULL)
            print(f"✅ Found browser: {browser}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("⚠️  No suitable browser found")
    print("   Install Chrome or Chromium for terrain extraction features")
    
    # Provide installation instructions
    system = platform.system().lower()
    if system == "linux":
        print("   Ubuntu/Debian: sudo apt-get install chromium-browser")
        print("   Fedora: sudo dnf install chromium")
    elif system == "darwin":
        print("   macOS: brew install --cask google-chrome")
    elif system == "windows":
        print("   Windows: Download from https://www.google.com/chrome/")
    
    return False

def test_import():
    """Test if key modules can be imported"""
    print("🧪 Testing imports...")
    
    required_modules = [
        "flask",
        "numpy",
        "PIL",
        "selenium",
        "folium"
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"❌ Failed to import: {', '.join(failed_imports)}")
        print("   Try running: pip install -r requirements.txt")
        return False
    
    print("✅ All imports successful")
    return True

def main():
    """Main setup function"""
    print("🔥 Fire Spread Simulation - Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Test imports
    if not test_import():
        sys.exit(1)
    
    # Check browser
    check_browser()
    
    print("\n🎉 Setup complete!")
    print("📋 Next steps:")
    print("   1. Run: python app.py")
    print("   2. Open: http://localhost:5000")
    print("   3. Or use: ./run.sh")
    
    print("\n📚 Documentation:")
    print("   - README.md for detailed instructions")
    print("   - Help button in the web interface")

if __name__ == "__main__":
    main()
