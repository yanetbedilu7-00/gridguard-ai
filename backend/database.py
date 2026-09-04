"""
GRIDGUARD AI - Database Operations
"""

import json
import os
from datetime import datetime
from config import Config

class GridDatabase:
    def __init__(self):
        self.data_file = Config.HISTORY_FILE
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Create data file if it doesn't exist"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump([], f)
    
    def save_reading(self, data):
        """Save a grid reading to history"""
        try:
            with open(self.data_file, 'r') as f:
                history = json.load(f)
            
            # Add timestamp
            data['timestamp'] = datetime.now().isoformat()
            
            # Keep only last 1000 records
            history.append(data)
            if len(history) > 1000:
                history = history[-1000:]
            
            with open(self.data_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def get_history(self, limit=100):
        """Get historical data"""
        try:
            with open(self.data_file, 'r') as f:
                history = json.load(f)
            return history[-limit:] if history else []
        except:
            return []
    
    def get_stats(self):
        """Get statistics from history"""
        history = self.get_history(100)
        if not history:
            return {
                'total_readings': 0,
                'avg_voltage': 0,
                'avg_current': 0,
                'avg_temperature': 0,
                'max_risk': 0,
                'alerts': 0
            }
        
        voltages = [h.get('voltage', 0) for h in history]
        currents = [h.get('current', 0) for h in history]
        temperatures = [h.get('temperature', 0) for h in history]
        risks = [h.get('risk', 0) for h in history]
        
        return {
            'total_readings': len(history),
            'avg_voltage': sum(voltages) / len(voltages),
            'avg_current': sum(currents) / len(currents),
            'avg_temperature': sum(temperatures) / len(temperatures),
            'max_risk': max(risks) if risks else 0,
            'alerts': sum(1 for r in risks if r > Config.RISK_WARNING)
        }