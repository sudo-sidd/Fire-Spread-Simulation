"""
Fire Spread Simulation Web Application
Main Flask application entry point
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import logging
from datetime import datetime

from api.map_api import map_bp
from api.simulation_api import simulation_bp
from api.enhanced_simulation_api import enhanced_simulation_bp
from api.terrain_api import terrain_bp
from core.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(map_bp, url_prefix='/api/map')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(enhanced_simulation_bp, url_prefix='/api/enhanced-simulation')
    app.register_blueprint(terrain_bp, url_prefix='/api/terrain')
    
    @app.route('/')
    def index():
        """Main application page"""
        return render_template('index.html')
    
    @app.route('/test')
    def test_page():
        """Test page to verify changes"""
        return render_template('test.html')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
