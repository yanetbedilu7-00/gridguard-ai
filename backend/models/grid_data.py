"""
GRIDGUARD AI - Data Models
"""

class GridReading:
    def __init__(self, voltage, current, temperature, risk, scenario='normal'):
        self.voltage = voltage
        self.current = current
        self.temperature = temperature
        self.risk = risk
        self.scenario = scenario
        self.power = (voltage * current) / 1000
    
    def to_dict(self):
        return {
            'voltage': round(self.voltage, 1),
            'current': round(self.current, 1),
            'temperature': round(self.temperature, 1),
            'power': round(self.power, 2),
            'risk': round(self.risk, 1),
            'scenario': self.scenario
        }

class RiskAnalysis:
    def __init__(self, voltage, current, temperature):
        self.voltage = voltage
        self.current = current
        self.temperature = temperature
        self.risk_score = 0
        self.conditions = []
        self.level = 'NORMAL'
        self.calculate()
    
    def calculate(self):
        risk = 0
        
        # Voltage analysis
        if self.voltage < 195:
            risk += 35
            self.conditions.append(f'Voltage critically low ({self.voltage:.1f} V)')
        elif self.voltage < 205:
            risk += 25
            self.conditions.append(f'Voltage below safe range ({self.voltage:.1f} V)')
        elif self.voltage < 210:
            risk += 10
            self.conditions.append(f'Voltage dropping ({self.voltage:.1f} V)')
        
        # Current analysis
        if self.current > 8.5:
            risk += 35
            self.conditions.append(f'Critical current detected ({self.current:.1f} A)')
        elif self.current > 7.0:
            risk += 25
            self.conditions.append(f'High current detected ({self.current:.1f} A)')
        elif self.current > 6.0:
            risk += 10
            self.conditions.append(f'Current rising ({self.current:.1f} A)')
        
        # Temperature analysis
        if self.temperature > 44:
            risk += 35
            self.conditions.append(f'Critical temperature ({self.temperature:.1f} °C)')
        elif self.temperature > 41:
            risk += 25
            self.conditions.append(f'Temperature above warning level ({self.temperature:.1f} °C)')
        elif self.temperature > 38:
            risk += 10
            self.conditions.append(f'Temperature elevated ({self.temperature:.1f} °C)')
        
        self.risk_score = min(100, max(0, risk))
        
        if self.risk_score > 70:
            self.level = 'CRITICAL'
        elif self.risk_score > 40:
            self.level = 'WARNING'
        else:
            self.level = 'NORMAL'
    
    def to_dict(self):
        return {
            'risk': round(self.risk_score, 1),
            'level': self.level,
            'conditions': self.conditions
        }