"""
GRIDGUARD AI - Flask Application
ULTIMATE FIX - No JSON Errors
"""

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import json
import time
import threading
import random
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, static_folder='../')
app.config['SECRET_KEY'] = 'gridguard-secret-key-2026'

# Enable CORS
CORS(app, origins=['*'])

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# Data file path
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
DATA_FILE = os.path.join(DATA_DIR, 'grid_history.json')

# ============================================
# ULTIMATE DATA FILE FIX
# ============================================

def init_data_file():
    """Create fresh data file"""
    # Create directory
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Write fresh empty array
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)
    
    print("Data file initialized successfully")

def safe_read_data():
    """Safely read data from file"""
    try:
        # Ensure file exists
        if not os.path.exists(DATA_FILE):
            init_data_file()
            return []
        
        # Read file
        with open(DATA_FILE, 'r') as f:
            content = f.read().strip()
            
            # If empty, reinitialize
            if not content:
                init_data_file()
                return []
            
            # Parse JSON
            data = json.loads(content)
            return data if isinstance(data, list) else []
            
    except json.JSONDecodeError:
        # File corrupted - reinitialize
        print("Data file corrupted, reinitializing...")
        init_data_file()
        return []
    except Exception as e:
        print(f"Error reading data: {e}")
        init_data_file()
        return []

def safe_write_data(data):
    """Safely write data to file"""
    try:
        # Ensure it's a list
        if not isinstance(data, list):
            data = []
        
        # Write to file
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error writing data: {e}")
        return False

# Initialize on startup
init_data_file()

# Global state
current_state = {
    'voltage': 220.0,
    'current': 5.0,
    'temperature': 35.0,
    'risk': 0,
    'scenario': 'normal',
    'conditions': []
}

# ============================================
# DATABASE FUNCTIONS
# ============================================

def save_reading(data):
    """Save a grid reading to history"""
    try:
        # Read existing data
        history = safe_read_data()
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        
        # Append new data
        history.append(data)
        
        # Keep only last 500 records
        if len(history) > 500:
            history = history[-500:]
        
        # Write back
        return safe_write_data(history)
    except Exception as e:
        print(f"Error saving data: {e}")
        return False

def get_history(limit=100):
    """Get historical data"""
    try:
        history = safe_read_data()
        return history[-limit:] if history else []
    except Exception as e:
        print(f"Error reading history: {e}")
        return []

def get_stats():
    """Get statistics from history"""
    history = get_history(100)
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
        'avg_voltage': round(sum(voltages) / len(voltages), 1),
        'avg_current': round(sum(currents) / len(currents), 1),
        'avg_temperature': round(sum(temperatures) / len(temperatures), 1),
        'max_risk': round(max(risks) if risks else 0, 1),
        'alerts': sum(1 for r in risks if r > 50)
    }

# ============================================
# RISK ANALYSIS
# ============================================

def analyze_risk(voltage, current, temperature, scenario='normal'):
    """Calculate risk score"""
    risk = 0
    conditions = []
    
    if voltage < 195:
        risk += 35
        conditions.append(f'Voltage critically low ({voltage:.1f} V)')
    elif voltage < 205:
        risk += 25
        conditions.append(f'Voltage below safe range ({voltage:.1f} V)')
    elif voltage < 210:
        risk += 10
        conditions.append(f'Voltage dropping ({voltage:.1f} V)')
    
    if current > 8.5:
        risk += 35
        conditions.append(f'Critical current detected ({current:.1f} A)')
    elif current > 7.0:
        risk += 25
        conditions.append(f'High current detected ({current:.1f} A)')
    elif current > 6.0:
        risk += 10
        conditions.append(f'Current rising ({current:.1f} A)')
    
    if temperature > 44:
        risk += 35
        conditions.append(f'Critical temperature ({temperature:.1f} °C)')
    elif temperature > 41:
        risk += 25
        conditions.append(f'Temperature above warning level ({temperature:.1f} °C)')
    elif temperature > 38:
        risk += 10
        conditions.append(f'Temperature elevated ({temperature:.1f} °C)')
    
    if scenario == 'overheat':
        risk += 20
    elif scenario == 'overload':
        risk += 15
    elif scenario == 'voltage_drop':
        risk += 10
    
    risk = min(100, max(0, risk))
    
    if risk > 70:
        level = 'CRITICAL'
    elif risk > 40:
        level = 'WARNING'
    else:
        level = 'NORMAL'
    
    return {
        'risk': round(risk, 1),
        'level': level,
        'conditions': conditions
    }

# ============================================
# ROUTES
# ============================================

@app.route('/')
def serve_index():
    return send_from_directory('../', 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('../assets', filename)

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'status': 'online',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/data/current', methods=['GET'])
def get_current_data():
    history = get_history(1)
    if history:
        return jsonify(history[-1])
    return jsonify({'error': 'No data available'}), 404

@app.route('/api/data/history', methods=['GET'])
def get_history_data():
    limit = request.args.get('limit', 100, type=int)
    history = get_history(limit)
    return jsonify(history)

@app.route('/api/data/stats', methods=['GET'])
def get_stats_data():
    stats = get_stats()
    return jsonify(stats)

@app.route('/api/data/ingest', methods=['POST'])
def ingest_data():
    try:
        data = request.json
        required = ['voltage', 'current', 'temperature']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        analysis = analyze_risk(
            data['voltage'],
            data['current'],
            data['temperature'],
            data.get('scenario', 'normal')
        )
        
        reading = {
            'voltage': round(data['voltage'], 1),
            'current': round(data['current'], 1),
            'temperature': round(data['temperature'], 1),
            'power': round((data['voltage'] * data['current']) / 1000, 2),
            'risk': analysis['risk'],
            'risk_level': analysis['level'],
            'conditions': analysis['conditions'],
            'scenario': data.get('scenario', 'normal')
        }
        
        save_reading(reading)
        
        return jsonify({
            'status': 'success',
            'data': reading,
            'analysis': analysis
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulate', methods=['POST'])
def simulate_intervention():
    try:
        data = request.json
        current_risk = data.get('risk', 0)
        
        if current_risk > 70:
            reduction = 57
        elif current_risk > 40:
            reduction = 35
        else:
            reduction = 15
        
        simulated_risk = max(0, current_risk - reduction)
        
        return jsonify({
            'current_risk': round(current_risk, 1),
            'simulated_risk': round(simulated_risk, 1),
            'reduction': reduction,
            'status': 'SAFE' if simulated_risk < 30 else 'MONITORING',
            'intervention': 'Load shedding + critical protection' if current_risk > 40 else 'Monitoring only'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# BACKGROUND DATA GENERATION
# ============================================

def generate_grid_data():
    """Generate realistic grid data"""
    global current_state
    
    while True:
        scenario = current_state['scenario']
        
        if scenario == 'normal':
            voltage = 216 + 5 * random.random() + 2 * (random.random() - 0.5)
            current = 5.5 + 1.5 * random.random() + 0.5 * (random.random() - 0.5)
            temperature = 35 + 3 * random.random() + 2 * (random.random() - 0.5)
        elif scenario == 'overheat':
            voltage = 208 + 6 * random.random()
            current = 6.5 + 1.5 * random.random()
            temperature = 42 + 5 * random.random()
        elif scenario == 'overload':
            voltage = 198 + 12 * random.random()
            current = 8 + 3 * random.random()
            temperature = 38 + 5 * random.random()
        elif scenario == 'voltage_drop':
            voltage = 190 + 15 * random.random()
            current = 5.5 + 2 * random.random()
            temperature = 35 + 4 * random.random()
        else:
            voltage = 220
            current = 5
            temperature = 35
        
        analysis = analyze_risk(voltage, current, temperature, scenario)
        
        current_state['voltage'] = voltage
        current_state['current'] = current
        current_state['temperature'] = temperature
        current_state['risk'] = analysis['risk']
        current_state['conditions'] = analysis['conditions']
        
        reading = {
            'voltage': round(voltage, 1),
            'current': round(current, 1),
            'temperature': round(temperature, 1),
            'power': round((voltage * current) / 1000, 2),
            'risk': analysis['risk'],
            'risk_level': analysis['level'],
            'conditions': analysis['conditions'],
            'scenario': scenario
        }
        save_reading(reading)
        
        socketio.emit('grid_update', {
            'voltage': round(voltage, 1),
            'current': round(current, 1),
            'temperature': round(temperature, 1),
            'power': round((voltage * current) / 1000, 2),
            'risk': round(analysis['risk'], 1),
            'risk_level': analysis['level'],
            'conditions': analysis['conditions'],
            'scenario': scenario
        })
        
        time.sleep(1)

# ============================================
# SOCKETIO EVENTS
# ============================================

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {
        'status': 'connected',
        'message': 'Connected to GRIDGUARD AI backend'
    })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('set_scenario')
def handle_set_scenario(data):
    global current_state
    scenario = data.get('scenario', 'normal')
    current_state['scenario'] = scenario
    print(f'Scenario changed to: {scenario}')
    emit('scenario_changed', {'scenario': scenario})

@socketio.on('run_agent')
def handle_run_agent():
    risk = current_state['risk']
    
    if risk < 30:
        response = {
            'status': 'MONITORING',
            'message': 'System stable. No action required.',
            'load_shed': 0
        }
    elif risk < 50:
        response = {
            'status': 'WARNING',
            'message': 'Risk detected. Preparing mitigation strategy.',
            'load_shed': 0.2
        }
    elif risk < 70:
        response = {
            'status': 'ALERT',
            'message': 'High risk detected. Shedding non-critical loads.',
            'load_shed': 0.5
        }
    else:
        response = {
            'status': 'EMERGENCY',
            'message': 'Critical. Autonomous intervention triggered. All flexible loads shed.',
            'load_shed': 1.0
        }
    
    emit('agent_response', response)

@socketio.on('run_simulation')
def handle_simulation():
    risk = current_state['risk']
    simulated_risk = max(0, risk - 57)
    
    response = {
        'current_risk': round(risk, 1),
        'simulated_risk': round(simulated_risk, 1),
        'reduction': round(risk - simulated_risk, 1),
        'status': 'SAFE' if simulated_risk < 30 else 'MONITORING'
    }
    
    emit('simulation_result', response)

# ============================================
# START SERVER
# ============================================

if __name__ == '__main__':
    # Start background thread
    thread = threading.Thread(target=generate_grid_data)
    thread.daemon = True
    thread.start()
    
    print("=" * 50)
    print("GRIDGUARD AI BACKEND SERVER")
    print("=" * 50)
    print("Server running on: http://localhost:5000")
    print("API endpoints:")
    print("  GET  /api/status")
    print("  GET  /api/data/current")
    print("  GET  /api/data/history")
    print("  GET  /api/data/stats")
    print("  POST /api/data/ingest")
    print("  POST /api/simulate")
    print("WebSocket: ws://localhost:5000/socket.io")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    socketio.run(app, debug=True, port=5000, allow_unsafe_werkzeug=True)