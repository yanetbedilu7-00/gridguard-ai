"""
GRIDGUARD AI - Configuration Module
"""

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'gridguard-secret-key-2026'
    
    # CORS Settings
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000', 'https://yanetbedilu7-00.github.io']
    
    # Data Storage
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
    HISTORY_FILE = os.path.join(DATA_DIR, 'grid_history.json')
    
    # Simulation Settings
    UPDATE_INTERVAL = 1  # seconds
    
    # Risk Thresholds
    RISK_NORMAL = 30
    RISK_WARNING = 50
    RISK_CRITICAL = 70

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}