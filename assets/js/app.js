/* ============================================
   GRIDGUARD AI - COMPLETE APPLICATION
   Fixed WebSocket Connection
   ============================================ */

// Backend URL
const BACKEND_URL = 'http://localhost:5000';

// ============================================
// STATE
// ============================================

const state = {
    currentScenario: 'normal',
    riskScore: 0,
    voltage: 216.9,
    current: 5.9,
    temperature: 36.2,
    power: 1.28,
    connected: false,
    socket: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 10
};

// ============================================
// DOM REFERENCES
// ============================================

const DOM = {
    currentScenario: document.getElementById('currentScenario'),
    tagNormal: document.getElementById('tagNormal'),
    tagOverheat: document.getElementById('tagOverheat'),
    tagOverload: document.getElementById('tagOverload'),
    tagVoltageDrop: document.getElementById('tagVoltageDrop'),
    voltage: document.getElementById('voltage'),
    current: document.getElementById('current'),
    temperature: document.getElementById('temperature'),
    power: document.getElementById('power'),
    riskValue: document.getElementById('riskValue'),
    riskScore: document.getElementById('riskScore'),
    riskIndicator: document.getElementById('riskIndicator'),
    riskStatus: document.getElementById('riskStatus'),
    riskLevel: document.getElementById('riskLevel'),
    confidence: document.getElementById('confidence'),
    confidenceFill: document.getElementById('confidenceFill'),
    detectedConditions: document.getElementById('detectedConditions'),
    failurePrediction: document.getElementById('failurePrediction'),
    agentStatus: document.getElementById('agentStatus'),
    agentMessage: document.getElementById('agentMessage'),
    simulationOutput: document.getElementById('simulationOutput'),
    emergencyStatus: document.getElementById('emergencyStatus'),
    commsStatus: document.getElementById('commsStatus'),
    medicalStatus: document.getElementById('medicalStatus'),
    systemStatus: document.getElementById('systemStatus'),
    statusIndicator: document.getElementById('statusIndicator'),
    timeline: document.getElementById('timeline')
};

// ============================================
// CONNECT TO BACKEND
// ============================================

function connectBackend() {
    fetch(`${BACKEND_URL}/api/status`)
        .then(response => response.json())
        .then(data => {
            state.connected = true;
            addTimeline('Backend connected - Real data mode active', 'info');
            console.log('Connected to backend:', data);
            connectWebSocket();
        })
        .catch(() => {
            state.connected = false;
            addTimeline('Backend not available - Running in simulation mode', 'warning');
            console.log('Running in simulation mode');
            startLocalSimulation();
        });
}

// ============================================
// WEBSOCKET CONNECTION - FIXED
// ============================================

function connectWebSocket() {
    try {
        // Use Socket.IO
        state.socket = io(BACKEND_URL, {
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionAttempts: state.maxReconnectAttempts,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            timeout: 20000
        });
        
        state.socket.on('connect', function() {
            state.reconnectAttempts = 0;
            addTimeline('WebSocket connected - Real-time updates active', 'info');
            console.log('Socket.IO connected');
            state.connected = true;
        });
        
        state.socket.on('disconnect', function(reason) {
            state.connected = false;
            console.log('Socket.IO disconnected:', reason);
            if (reason === 'io server disconnect') {
                // The disconnection was initiated by the server, reconnect manually
                state.socket.connect();
            }
            addTimeline('WebSocket disconnected - Reconnecting...', 'warning');
        });
        
        state.socket.on('connect_error', function(error) {
            console.log('Connection error:', error);
            state.reconnectAttempts++;
            if (state.reconnectAttempts >= state.maxReconnectAttempts) {
                addTimeline('WebSocket connection failed - Using simulation', 'warning');
                startLocalSimulation();
            }
        });
        
        state.socket.on('grid_update', function(data) {
            updateDashboardWithData(data);
        });
        
        state.socket.on('agent_response', function(data) {
            handleAgentResponse(data);
        });
        
        state.socket.on('simulation_result', function(data) {
            handleSimulationResult(data);
        });
        
        state.socket.on('scenario_changed', function(data) {
            handleScenarioChanged(data);
        });
        
        state.socket.on('connection_response', function(data) {
            console.log('Connection response:', data);
        });
        
    } catch(e) {
        console.log('WebSocket connection error:', e);
        addTimeline('WebSocket connection failed - Using simulation', 'warning');
        startLocalSimulation();
    }
}

// ============================================
// HANDLE SOCKET EVENTS
// ============================================

function handleAgentResponse(data) {
    DOM.agentStatus.textContent = data.status;
    DOM.agentStatus.style.color = 
        data.status === 'EMERGENCY' ? '#b33a2a' :
        data.status === 'ALERT' ? '#b87a2a' :
        data.status === 'WARNING' ? '#b87a2a' : '#2d7a4a';
    DOM.agentMessage.textContent = data.message;
    
    const eventType = data.status === 'EMERGENCY' ? 'critical' : 
                     data.status === 'ALERT' ? 'warning' : 'agent';
    addTimeline('Agent: ' + data.status + ' - ' + data.message, eventType);
}

function handleSimulationResult(data) {
    let output = 'Risk: ' + data.current_risk + '% → ' + data.simulated_risk + '%<br>';
    output += 'Reduction: ' + data.reduction + '%<br>';
    output += 'Status: ' + data.status;
    DOM.simulationOutput.innerHTML = output;
    DOM.simulationOutput.style.color = data.status === 'SAFE' ? '#2d7a4a' : '#b87a2a';
    addTimeline('Simulation: ' + data.current_risk + '% → ' + data.simulated_risk + '%', 'simulation');
}

function handleScenarioChanged(data) {
    state.currentScenario = data.scenario;
    const names = {
        'normal': 'Normal',
        'overheat': 'Overheating',
        'overload': 'Overload',
        'voltage_drop': 'Voltage Drop'
    };
    DOM.currentScenario.textContent = names[data.scenario] || 'Normal';
    
    document.querySelectorAll('.scenario-tag').forEach(t => t.classList.remove('active'));
    const tagMap = {
        'normal': DOM.tagNormal,
        'overheat': DOM.tagOverheat,
        'overload': DOM.tagOverload,
        'voltage_drop': DOM.tagVoltageDrop
    };
    if (tagMap[data.scenario]) {
        tagMap[data.scenario].classList.add('active');
    }
}

// ============================================
// SEND MESSAGES TO BACKEND
// ============================================

function sendToBackend(message) {
    if (state.socket && state.connected) {
        try {
            state.socket.emit(message.type, message);
            console.log('Sent to backend:', message);
        } catch(e) {
            console.log('Error sending message:', e);
        }
    } else {
        console.log('Not connected to backend, using local');
        // Fallback to local
        if (message.type === 'set_scenario') {
            state.currentScenario = message.scenario;
        } else if (message.type === 'run_agent') {
            runLocalAgent();
        } else if (message.type === 'run_simulation') {
            runLocalSimulation();
        }
    }
}

// ============================================
// UPDATE DASHBOARD WITH BACKEND DATA
// ============================================

function updateDashboardWithData(data) {
    DOM.voltage.textContent = data.voltage;
    DOM.current.textContent = data.current;
    DOM.temperature.textContent = data.temperature;
    DOM.power.textContent = data.power || ((data.voltage * data.current) / 1000).toFixed(2);
    
    DOM.riskValue.textContent = data.risk;
    DOM.riskScore.textContent = data.risk;
    
    DOM.riskIndicator.className = 'risk-indicator';
    const risk = data.risk;
    
    if (risk > 70) {
        DOM.riskIndicator.classList.add('critical');
        DOM.riskStatus.textContent = 'Critical';
        DOM.riskStatus.className = 'risk-status-text critical';
        DOM.riskLevel.textContent = 'Critical';
        DOM.riskLevel.className = 'risk-level critical';
        DOM.detectedConditions.innerHTML = data.conditions ? data.conditions.join('<br>') : 'Critical conditions detected';
        DOM.failurePrediction.textContent = 'Failure Prediction: Critical - Rapid deterioration detected';
        DOM.failurePrediction.style.color = '#b33a2a';
        DOM.statusIndicator.className = 'status-indicator alert';
        DOM.systemStatus.textContent = 'System Alert';
    } else if (risk > 40) {
        DOM.riskIndicator.classList.add('warning');
        DOM.riskStatus.textContent = 'Warning';
        DOM.riskStatus.className = 'risk-status-text warning';
        DOM.riskLevel.textContent = 'Warning';
        DOM.riskLevel.className = 'risk-level warning';
        DOM.detectedConditions.innerHTML = data.conditions ? data.conditions.join('<br>') : 'Warning conditions detected';
        DOM.failurePrediction.textContent = 'Failure Prediction: Warning - Risk indicators present';
        DOM.failurePrediction.style.color = '#b87a2a';
        DOM.statusIndicator.className = 'status-indicator alert';
        DOM.systemStatus.textContent = 'System Alert';
    } else {
        DOM.riskStatus.textContent = 'Normal';
        DOM.riskStatus.className = 'risk-status-text normal';
        DOM.riskLevel.textContent = 'Normal';
        DOM.riskLevel.className = 'risk-level normal';
        DOM.detectedConditions.textContent = 'All parameters within normal range';
        DOM.failurePrediction.textContent = 'Failure Prediction: Normal - System stable';
        DOM.failurePrediction.style.color = '#6b6560';
        DOM.statusIndicator.className = 'status-indicator';
        DOM.systemStatus.textContent = 'System Online';
    }
    
    const confidence = data.confidence || (88 + Math.floor(Math.random() * 10));
    DOM.confidence.textContent = confidence;
    DOM.confidenceFill.style.width = confidence + '%';
}

// ============================================
// SCENARIO FUNCTIONS
// ============================================

function triggerOverheat() {
    state.currentScenario = 'overheat';
    sendToBackend({ type: 'set_scenario', scenario: 'overheat' });
    updateScenarioUI('Overheating', '#b33a2a', DOM.tagOverheat);
    addTimeline('Scenario loaded: Overheating', 'critical');
    if (!state.connected) {
        runLocalSimulation();
        setTimeout(runLocalAgent, 800);
    }
}

function triggerOverload() {
    state.currentScenario = 'overload';
    sendToBackend({ type: 'set_scenario', scenario: 'overload' });
    updateScenarioUI('Overload', '#b87a2a', DOM.tagOverload);
    addTimeline('Scenario loaded: Overload', 'warning');
    if (!state.connected) {
        runLocalSimulation();
        setTimeout(runLocalAgent, 800);
    }
}

function triggerVoltageDrop() {
    state.currentScenario = 'voltage_drop';
    sendToBackend({ type: 'set_scenario', scenario: 'voltage_drop' });
    updateScenarioUI('Voltage Drop', '#5a4a8b', DOM.tagVoltageDrop);
    addTimeline('Scenario loaded: Voltage Drop', 'warning');
    if (!state.connected) {
        runLocalSimulation();
        setTimeout(runLocalAgent, 800);
    }
}

function resetSystem() {
    state.currentScenario = 'normal';
    sendToBackend({ type: 'set_scenario', scenario: 'normal' });
    updateScenarioUI('Normal', '#2d7a4a', DOM.tagNormal);
    state.riskScore = 0;
    addTimeline('System reset - Normal operation restored', 'info');
    
    DOM.agentStatus.textContent = 'Monitoring';
    DOM.agentStatus.style.color = '#2d7a4a';
    DOM.agentMessage.textContent = 'Agent waiting for instruction.';
    
    DOM.simulationOutput.textContent = 'Ready';
    DOM.simulationOutput.style.color = '#2d2a24';
    
    ['emergencyStatus', 'commsStatus', 'medicalStatus'].forEach(id => {
        const el = document.getElementById(id);
        el.textContent = 'Critical &bull; Online';
        el.className = 'protection-status safe';
    });
    
    if (!state.connected) {
        startLocalSimulation();
    }
}

function updateScenarioUI(name, color, tagElement) {
    DOM.currentScenario.textContent = name;
    DOM.currentScenario.style.color = color;
    document.querySelectorAll('.scenario-tag').forEach(t => t.classList.remove('active'));
    tagElement.classList.add('active');
}

// ============================================
// AGENT FUNCTION
// ============================================

function runAgent() {
    if (state.connected) {
        sendToBackend({ type: 'run_agent' });
        addTimeline('Agent requested from backend', 'agent');
    } else {
        runLocalAgent();
    }
}

function runLocalAgent() {
    const risk = parseInt(DOM.riskValue.textContent) || 0;
    let status, message, color;
    
    if (risk < 30) {
        status = 'Monitoring';
        message = 'System stable. No action required.';
        color = '#2d7a4a';
    } else if (risk < 50) {
        status = 'Warning';
        message = 'Risk detected. Preparing mitigation strategy.';
        color = '#b87a2a';
    } else if (risk < 70) {
        status = 'Alert';
        message = 'High risk detected. Shedding non-critical loads.';
        color = '#b87a2a';
    } else {
        status = 'Emergency';
        message = 'Critical. Autonomous intervention triggered.';
        color = '#b33a2a';
    }
    
    DOM.agentStatus.textContent = status;
    DOM.agentStatus.style.color = color;
    DOM.agentMessage.textContent = message;
    
    const isProtected = (risk >= 50);
    const statusText = isProtected ? 'Protected &bull; Critical' : 'Critical &bull; Online';
    const className = isProtected ? 'protection-status protected' : 'protection-status safe';
    
    [DOM.emergencyStatus, DOM.commsStatus, DOM.medicalStatus].forEach(el => {
        el.textContent = statusText;
        el.className = className;
    });
    
    addTimeline('Agent executed: ' + status + ' - ' + message, 
        status === 'Emergency' ? 'critical' : 
        status === 'Alert' ? 'warning' : 'agent');
}

// ============================================
// SIMULATION FUNCTION
// ============================================

function runSimulation() {
    if (state.connected) {
        sendToBackend({ type: 'run_simulation' });
        addTimeline('Simulation requested from backend', 'simulation');
    } else {
        runLocalSimulation();
    }
}

function runLocalSimulation() {
    const currentRisk = parseInt(DOM.riskValue.textContent) || 0;
    const simulatedRisk = Math.max(0, currentRisk - 57);
    
    let output = 'Risk: ' + currentRisk + '% → ' + simulatedRisk + '%<br>';
    output += 'Intervention: ' + (currentRisk > 40 ? 'Load shedding + critical protection' : 'Monitoring only') + '<br>';
    output += 'Status: ' + (simulatedRisk < 30 ? 'Safe - Grid stable' : 'Monitoring - Risk reduced');
    
    DOM.simulationOutput.innerHTML = output;
    DOM.simulationOutput.style.color = simulatedRisk < 30 ? '#2d7a4a' : '#b87a2a';
    
    addTimeline('Simulation: ' + currentRisk + '% → ' + simulatedRisk + '%', 'simulation');
}

// ============================================
// TIMELINE
// ============================================

function addTimeline(message, type) {
    const time = new Date().toLocaleTimeString();
    const timeline = DOM.timeline;
    const item = document.createElement('div');
    item.className = 'timeline-item';
    if (type === 'critical') item.classList.add('critical');
    else if (type === 'warning') item.classList.add('warning');
    else if (type === 'simulation') item.classList.add('simulation');
    else if (type === 'agent') item.classList.add('agent');
    
    item.innerHTML = '<span class="time">[' + time + ']</span> ' + message;
    timeline.prepend(item);
    while (timeline.children.length > 30) {
        timeline.removeChild(timeline.lastChild);
    }
}

// ============================================
// LOCAL SIMULATION (fallback when backend off)
// ============================================

let localSimulationInterval = null;

function startLocalSimulation() {
    if (localSimulationInterval) {
        clearInterval(localSimulationInterval);
    }
    localSimulationInterval = setInterval(updateLocalDashboard, 1000);
    addTimeline('Local simulation mode active', 'info');
}

function updateLocalDashboard() {
    const noise = 0.95 + 0.1 * Math.random();
    
    let voltage, current, temperature;
    
    switch(state.currentScenario) {
        case 'normal':
            voltage = 216 + 5 * Math.random() + 2 * Math.sin(Date.now() / 10000);
            current = 5.5 + 1.5 * Math.random() + 0.5 * Math.sin(Date.now() / 15000);
            temperature = 35 + 3 * Math.random() + 2 * Math.sin(Date.now() / 20000);
            break;
        case 'overheat':
            voltage = 208 + 6 * Math.random();
            current = 6.5 + 1.5 * Math.random();
            temperature = 42 + 5 * Math.random();
            break;
        case 'overload':
            voltage = 198 + 12 * Math.random();
            current = 8 + 3 * Math.random();
            temperature = 38 + 5 * Math.random();
            break;
        case 'voltage_drop':
            voltage = 190 + 15 * Math.random();
            current = 5.5 + 2 * Math.random();
            temperature = 35 + 4 * Math.random();
            break;
    }
    
    const power = (voltage * current) / 1000;
    const risk = calculateLocalRisk(voltage, current, temperature);
    
    DOM.voltage.textContent = voltage.toFixed(1);
    DOM.current.textContent = current.toFixed(1);
    DOM.temperature.textContent = temperature.toFixed(1);
    DOM.power.textContent = power.toFixed(2);
    DOM.riskValue.textContent = risk;
    DOM.riskScore.textContent = risk;
    
    DOM.riskIndicator.className = 'risk-indicator';
    
    if (risk > 70) {
        DOM.riskIndicator.classList.add('critical');
        DOM.riskStatus.textContent = 'Critical';
        DOM.riskStatus.className = 'risk-status-text critical';
        DOM.riskLevel.textContent = 'Critical';
        DOM.riskLevel.className = 'risk-level critical';
        DOM.detectedConditions.innerHTML = getLocalConditions(voltage, current, temperature);
        DOM.failurePrediction.textContent = 'Failure Prediction: Critical - Rapid deterioration detected';
        DOM.failurePrediction.style.color = '#b33a2a';
        DOM.statusIndicator.className = 'status-indicator alert';
        DOM.systemStatus.textContent = 'System Alert';
    } else if (risk > 40) {
        DOM.riskIndicator.classList.add('warning');
        DOM.riskStatus.textContent = 'Warning';
        DOM.riskStatus.className = 'risk-status-text warning';
        DOM.riskLevel.textContent = 'Warning';
        DOM.riskLevel.className = 'risk-level warning';
        DOM.detectedConditions.innerHTML = getLocalConditions(voltage, current, temperature);
        DOM.failurePrediction.textContent = 'Failure Prediction: Warning - Risk indicators present';
        DOM.failurePrediction.style.color = '#b87a2a';
        DOM.statusIndicator.className = 'status-indicator alert';
        DOM.systemStatus.textContent = 'System Alert';
    } else {
        DOM.riskStatus.textContent = 'Normal';
        DOM.riskStatus.className = 'risk-status-text normal';
        DOM.riskLevel.textContent = 'Normal';
        DOM.riskLevel.className = 'risk-level normal';
        DOM.detectedConditions.textContent = 'All parameters within normal range';
        DOM.failurePrediction.textContent = 'Failure Prediction: Normal - System stable';
        DOM.failurePrediction.style.color = '#6b6560';
        DOM.statusIndicator.className = 'status-indicator';
        DOM.systemStatus.textContent = 'System Online';
    }
    
    const confidence = 88 + Math.floor(Math.random() * 10);
    DOM.confidence.textContent = confidence;
    DOM.confidenceFill.style.width = confidence + '%';
}

function calculateLocalRisk(v, c, t) {
    let risk = 0;
    if (v < 195) risk += 35;
    else if (v < 205) risk += 25;
    else if (v < 210) risk += 10;
    if (c > 8.5) risk += 35;
    else if (c > 7.0) risk += 25;
    else if (c > 6.0) risk += 10;
    if (t > 44) risk += 35;
    else if (t > 41) risk += 25;
    else if (t > 38) risk += 10;
    if (state.currentScenario === 'overheat') risk += 20;
    if (state.currentScenario === 'overload') risk += 15;
    if (state.currentScenario === 'voltage_drop') risk += 10;
    return Math.min(100, Math.max(0, risk));
}

function getLocalConditions(v, c, t) {
    let conditions = [];
    if (v < 210) conditions.push('Voltage below safe range (' + v.toFixed(1) + ' V)');
    if (c > 6.5) conditions.push('High current detected (' + c.toFixed(1) + ' A)');
    if (t > 38) conditions.push('Temperature above warning level (' + t.toFixed(1) + ' °C)');
    if (t > 42) conditions.push('Critical temperature (' + t.toFixed(1) + ' °C)');
    return conditions.join('<br>') || 'All parameters within normal range';
}

// ============================================
// KEYBOARD SHORTCUTS
// ============================================

document.addEventListener('keydown', function(e) {
    switch(e.key) {
        case '1': triggerOverheat(); e.preventDefault(); break;
        case '2': triggerOverload(); e.preventDefault(); break;
        case '3': triggerVoltageDrop(); e.preventDefault(); break;
        case '4': resetSystem(); e.preventDefault(); break;
        case '5': runAgent(); e.preventDefault(); break;
        case '6': runSimulation(); e.preventDefault(); break;
    }
});

// ============================================
// EXPOSE GLOBALLY
// ============================================

window.triggerOverheat = triggerOverheat;
window.triggerOverload = triggerOverload;
window.triggerVoltageDrop = triggerVoltageDrop;
window.resetSystem = resetSystem;
window.runAgent = runAgent;
window.runSimulation = runSimulation;

// ============================================
// INIT
// ============================================

console.log('GRIDGUARD AI v2.0.0');
console.log('Backend URL:', BACKEND_URL);
console.log('Press 1=Overheat, 2=Overload, 3=VoltageDrop, 4=Reset, 5=Agent, 6=Simulation');

addTimeline('GRIDGUARD AI v2.0.0 - Starting...', 'info');

// Try to connect to backend
connectBackend();

// If backend not available, local simulation starts automatically
setTimeout(function() {
    addTimeline('System ready - Use buttons or press 1-6', 'info');
}, 1000);