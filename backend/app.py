"""
GRIDGUARD AI - Vercel Compatible Backend
Fixed to serve index.html at root URL
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import random
import json
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__, static_folder='../')

# Enable CORS for all origins
CORS(app, origins=['*'])

# ============================================
# SERVE FRONTEND
# ============================================

@app.route('/')
def serve_index():
    """Serve the main index.html"""
    return send_from_directory('../', 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve assets folder"""
    return send_from_directory('../assets', filename)

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
# DATA GENERATION
# ============================================

def generate_grid_data(scenario='normal'):
    """Generate realistic grid data for a single request"""
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
    
    power = (voltage * current) / 1000
    analysis = analyze_risk(voltage, current, temperature, scenario)
    
    return {
        'voltage': round(voltage, 1),
        'current': round(current, 1),
        'temperature': round(temperature, 1),
        'power': round(power, 2),
        'risk': analysis['risk'],
        'risk_level': analysis['level'],
        'conditions': analysis['conditions'],
        'scenario': scenario
    }

# ============================================
# API ENDPOINTS
# ============================================

@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'online',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/data/current')
def get_current_data():
    """Get current grid data"""
    scenario = request.args.get('scenario', 'normal')
    data = generate_grid_data(scenario)
    return jsonify(data)

@app.route('/api/data/history')
def get_history():
    """Get historical data (simulated)"""
    history = []
    scenarios = ['normal', 'normal', 'normal', 'overheat', 'normal', 'overload', 'normal']
    for _ in range(20):
        s = random.choice(scenarios)
        data = generate_grid_data(s)
        data['timestamp'] = datetime.now().isoformat()
        history.append(data)
    
    return jsonify(history[-10:])

@app.route('/api/data/stats')
def get_stats():
    """Get statistics"""
    history = []
    for _ in range(50):
        scenario = random.choice(['normal', 'normal', 'normal', 'overheat', 'overload', 'voltage_drop'])
        data = generate_grid_data(scenario)
        history.append(data)
    
    voltages = [h['voltage'] for h in history]
    currents = [h['current'] for h in history]
    temperatures = [h['temperature'] for h in history]
    risks = [h['risk'] for h in history]
    
    return jsonify({
        'total_readings': len(history),
        'avg_voltage': round(sum(voltages) / len(voltages), 1),
        'avg_current': round(sum(currents) / len(currents), 1),
        'avg_temperature': round(sum(temperatures) / len(temperatures), 1),
        'max_risk': round(max(risks), 1),
        'alerts': sum(1 for r in risks if r > 50)
    })

@app.route('/api/simulate', methods=['POST'])
def simulate_intervention():
    """Simulate an intervention"""
    try:
        data = request.json or {}
        current_risk = data.get('risk', 0)
        scenario = data.get('scenario', 'normal')
        
        current_data = generate_grid_data(scenario)
        current_risk = current_data['risk']
        
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
            'intervention': 'Load shedding + critical protection' if current_risk > 40 else 'Monitoring only',
            'data': current_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# ERROR HANDLER
# ============================================

@app.errorhandler(404)
def handle_404(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def handle_500(error):
    return jsonify({
        'error': 'Internal server error',
        'message': str(error)
    }), 500

# ============================================
# FOR LOCAL TESTING
# ============================================

if __name__ == '__main__':
    app.run(debug=True, port=5000)