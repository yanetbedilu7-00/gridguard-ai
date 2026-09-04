"""
GRIDGUARD AI - REST API Routes
"""

from flask import Blueprint, request, jsonify
from database import GridDatabase
from models.grid_data import GridReading, RiskAnalysis

api_bp = Blueprint('api', __name__)
db = GridDatabase()

@api_bp.route('/status', methods=['GET'])
def get_status():
    """Get current system status"""
    return jsonify({
        'status': 'online',
        'version': '2.0.0',
        'timestamp': __import__('datetime').datetime.now().isoformat()
    })

@api_bp.route('/data/current', methods=['GET'])
def get_current_data():
    """Get latest grid data"""
    history = db.get_history(1)
    if history:
        return jsonify(history[-1])
    return jsonify({'error': 'No data available'}), 404

@api_bp.route('/data/history', methods=['GET'])
def get_history():
    """Get historical data"""
    limit = request.args.get('limit', 100, type=int)
    history = db.get_history(limit)
    return jsonify(history)

@api_bp.route('/data/stats', methods=['GET'])
def get_stats():
    """Get statistics"""
    stats = db.get_stats()
    return jsonify(stats)

@api_bp.route('/data/ingest', methods=['POST'])
def ingest_data():
    """Ingest new grid data"""
    try:
        data = request.json
        
        # Validate data
        required = ['voltage', 'current', 'temperature']
        if not all(k in data for k in required):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Analyze risk
        analysis = RiskAnalysis(
            data['voltage'],
            data['current'],
            data['temperature']
        )
        
        # Create reading
        reading = GridReading(
            data['voltage'],
            data['current'],
            data['temperature'],
            analysis.risk_score,
            data.get('scenario', 'normal')
        )
        
        # Save to database
        db.save_reading(reading.to_dict())
        
        return jsonify({
            'status': 'success',
            'data': reading.to_dict(),
            'analysis': analysis.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/simulate', methods=['POST'])
def simulate_intervention():
    """Simulate an intervention"""
    try:
        data = request.json
        current_risk = data.get('risk', 0)
        
        # Calculate simulated risk reduction
        reduction = 0
        if current_risk > 70:
            reduction = 57
        elif current_risk > 40:
            reduction = 35
        else:
            reduction = 15
        
        simulated_risk = max(0, current_risk - reduction)
        
        return jsonify({
            'current_risk': current_risk,
            'simulated_risk': round(simulated_risk, 1),
            'reduction': reduction,
            'status': 'SAFE' if simulated_risk < 30 else 'MONITORING',
            'intervention': 'Load shedding + critical protection' if current_risk > 40 else 'Monitoring only'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500