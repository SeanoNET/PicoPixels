#!/usr/bin/env python3
"""
LED Matrix Web Controller
Simple Flask server to control LED matrix via web interface
"""

from flask import Flask, render_template_string, request, jsonify
import serial
import serial.tools.list_ports
import time
import threading
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 1

class LEDMatrixController:
    def __init__(self, baudrate=SERIAL_BAUDRATE):
        self.port = None
        self.baudrate = baudrate
        self.serial_connection = None
        self.connected = False
        self.last_command = None
        self.current_effect = "None"

    def connect(self, port=None):
        """Connect to the Pi Pico"""
        if port:
            self.port = port

        if not self.port:
            print("❌ No port specified")
            return False

        try:
            # Disconnect existing connection if any
            if self.serial_connection:
                self.disconnect()

            self.serial_connection = serial.Serial(
                self.port,
                self.baudrate,
                timeout=SERIAL_TIMEOUT
            )
            time.sleep(2)  # Wait for connection to stabilize
            self.connected = True
            print(f"✅ Connected to LED Matrix on {self.port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to {self.port}: {e}")
            self.connected = False
            return False

    def send_command(self, command):
        """Send command to the LED matrix"""
        if not self.connected:
            return {"status": "error", "message": "Not connected to LED matrix"}

        try:
            # Send command
            self.serial_connection.write(f"{command}\r\n".encode())
            self.serial_connection.flush()

            # Wait for response
            time.sleep(0.1)
            responses = []

            # Read any available responses
            for _ in range(5):  # Try up to 5 times
                if self.serial_connection.in_waiting:
                    response = self.serial_connection.readline().decode().strip()
                    if response:
                        responses.append(response)
                time.sleep(0.05)

            self.last_command = command

            # Update current effect if it's a start command
            if command.startswith('start '):
                self.current_effect = command.split(' ', 1)[1]
            elif command == 'stop':
                self.current_effect = "None"
            elif command in ['test', 'border', 'on', 'off']:
                self.current_effect = command

            print(f"📤 Sent: {command}")
            if responses:
                print(f"📥 Response: {', '.join(responses)}")

            return {
                "status": "success",
                "command": command,
                "responses": responses,
                "current_effect": self.current_effect
            }

        except Exception as e:
            print(f"❌ Error sending command '{command}': {e}")
            return {"status": "error", "message": str(e)}

    def disconnect(self):
        """Disconnect from the LED matrix"""
        if self.serial_connection:
            self.serial_connection.close()
            self.connected = False
            print("🔌 Disconnected from LED matrix")

# Global controller instance
matrix_controller = LEDMatrixController()

# HTML template (embedded)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LED Matrix Controller</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%23667eea'/><rect x='10' y='10' width='80' height='80' fill='%23764ba2'/><circle cx='25' cy='25' r='3' fill='%23ff6b6b'/><circle cx='35' cy='25' r='3' fill='%23ffa500'/><circle cx='45' cy='25' r='3' fill='%23ffeb3b'/><circle cx='55' cy='25' r='3' fill='%234caf50'/><circle cx='65' cy='25' r='3' fill='%232196f3'/><circle cx='75' cy='25' r='3' fill='%239c27b0'/><rect x='20' y='35' width='60' height='4' fill='%23ecf0f1' opacity='0.8'/><rect x='20' y='45' width='40' height='4' fill='%23ecf0f1' opacity='0.6'/><rect x='20' y='55' width='50' height='4' fill='%23ecf0f1' opacity='0.7'/><rect x='20' y='65' width='35' height='4' fill='%23ecf0f1' opacity='0.5'/><rect x='20' y='75' width='45' height='4' fill='%23ecf0f1' opacity='0.6'/></svg>" type="image/svg+xml">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            max-width: 600px;
            width: 100%;
        }

        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
            font-size: 2.5rem;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .status {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 25px;
            border-left: 4px solid #28a745;
        }

        .status h3 {
            color: #2c3e50;
            margin-bottom: 10px;
        }

        .status-item {
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            color: #6c757d;
        }

        .section {
            margin-bottom: 30px;
        }

        .section h3 {
            color: #2c3e50;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }

        .button-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }

        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn.stop {
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }

        .btn.test {
            background: linear-gradient(45deg, #f39c12, #e67e22);
        }

        .control-group {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
        }

        .control-group label {
            font-weight: 600;
            color: #2c3e50;
            min-width: 80px;
        }

        .slider {
            flex: 1;
            -webkit-appearance: none;
            height: 8px;
            border-radius: 4px;
            background: #ddd;
            outline: none;
            position: relative;
        }

        .slider.speed-slider {
            background: linear-gradient(90deg, #ff6b6b 0%, #ffa500 25%, #ffeb3b 50%, #4caf50 75%, #2196f3 100%);
        }

        .slider.brightness-slider {
            background: linear-gradient(90deg, #000000 0%, #333333 25%, #666666 50%, #999999 75%, #ffffff 100%);
        }

        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: white;
            border: 3px solid #667eea;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }

        .slider::-moz-range-thumb {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: white;
            border: 3px solid #667eea;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }

        .value-display {
            min-width: 40px;
            text-align: center;
            font-weight: 600;
            color: #667eea;
        }

        .text-input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        .text-input {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }

        .text-input:focus {
            outline: none;
            border-color: #667eea;
        }

        .port-settings {
            background: #f3e5f5;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #9c27b0;
        }

        .port-select {
            flex: 1;
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            margin-right: 10px;
            min-width: 0;
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .port-control-group {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            flex-wrap: wrap;
        }

        .port-control-group label {
            font-weight: 600;
            color: #2c3e50;
            min-width: 100px;
            flex-shrink: 0;
        }

        .port-dropdown-container {
            display: flex;
            gap: 10px;
            flex: 1;
            align-items: center;
            min-width: 200px;
            max-width: 100%;
        }

        .port-select:focus {
            outline: none;
            border-color: #9c27b0;
        }

        .port-status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            font-size: 14px;
            font-weight: 500;
            display: none;
        }

        .port-status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .port-status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .port-status.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .log {
            background: #2c3e50;
            color: #ecf0f1;
            border-radius: 10px;
            padding: 15px;
            height: 150px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            margin-top: 20px;
        }

        .log-entry {
            margin-bottom: 5px;
            opacity: 0;
            animation: fadeIn 0.3s ease forwards;
        }

        @keyframes fadeIn {
            to { opacity: 1; }
        }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
        }

        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        .status-dot.connected {
            background: #28a745;
        }

        .status-dot.disconnected {
            background: #dc3545;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 LED Matrix Control Center</h1>

        <div class="status">
            <h3>System Status</h3>
            <div class="status-item">
                <span>Connection:</span>
                <div class="connection-status">
                    <div class="status-dot connected" id="status-dot"></div>
                    <span id="connection-status">{{ 'Connected' if connected else 'Disconnected' }}</span>
                </div>
            </div>
            <div class="status-item">
                <span>Current Effect:</span>
                <span id="current-effect">{{ current_effect }}</span>
            </div>
            <div class="status-item">
                <span>Matrix Size:</span>
                <span>32x8 (4 modules)</span>
            </div>
            <div class="status-item">
                <span>Port:</span>
                <span>{{ port or 'None Selected' }}</span>
            </div>
        </div>

        <div class="section">
            <h3>🔌 Port Settings</h3>
            <div class="port-settings">
                <div class="port-control-group">
                    <label>Available Ports:</label>
                    <div class="port-dropdown-container">
                        <select id="port-dropdown" class="port-select" onchange="connectToSelectedPort()">
                            <option value="">Scanning...</option>
                        </select>
                    </div>
                </div>
                <div class="button-grid" style="margin-top: 15px;">
                    <button class="btn" onclick="reconnectCurrent()">Reconnect Current</button>
                </div>
                <div id="port-status" class="port-status"></div>
            </div>
        </div>

        <div class="section">
            <h3>🎮 Quick Controls</h3>
            <div class="button-grid">
                <button class="btn test" onclick="sendCommand('test')">Test</button>
                <button class="btn" onclick="sendCommand('border')">Border</button>
                <button class="btn" onclick="sendCommand('on')">All On</button>
                <button class="btn" onclick="sendCommand('off')">All Off</button>
                <button class="btn stop" onclick="sendCommand('stop')">Stop</button>
            </div>
        </div>

        <div class="section">
            <h3>✨ Animation Effects</h3>
            <div class="button-grid">
                <button class="btn" onclick="startEffect('matrix')">Matrix Rain</button>
                <button class="btn" onclick="startEffect('fire')">Fire</button>
                <button class="btn" onclick="startEffect('wave')">Waves</button>
                <button class="btn" onclick="startEffect('plasma')">Plasma</button>
                <button class="btn" onclick="startEffect('scanner')">Scanner</button>
                <button class="btn" onclick="startEffect('balls')">Bouncing Balls</button>
                <button class="btn" onclick="startEffect('pong')">Pong Game</button>
                <button class="btn" onclick="startEffect('text')">Scrolling Text</button>
            </div>
        </div>

        <div class="section">
            <h3>🎛️ Settings</h3>

            <div class="control-group">
                <label>Brightness:</label>
                <input type="range" class="slider brightness-slider" id="brightness" min="0" max="4" value="2" step="1"
                       oninput="updateBrightness(this.value)">
                <div class="value-display" id="brightness-value">Normal</div>
            </div>

            <div class="control-group">
                <label>Speed:</label>
                <input type="range" class="slider speed-slider" id="speed" min="0" max="4" value="2" step="1"
                       oninput="updateSpeed(this.value)">
                <div class="value-display" id="speed-value">Normal</div>
            </div>

            <div class="text-input-group">
                <input type="text" class="text-input" id="custom-text" placeholder="Enter custom text..." value="HELLO WORLD">
                <button class="btn" onclick="updateText()">Set Text</button>
            </div>
        </div>

        <div class="log" id="log">
            <div class="log-entry">🚀 LED Matrix Controller Ready</div>
            <div class="log-entry">💡 Click any effect to get started!</div>
        </div>
    </div>

    <script>
        // Send command to server
        async function sendCommand(command) {
            try {
                const response = await fetch('/command', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ command: command })
                });

                const result = await response.json();

                if (result.status === 'success') {
                    addLog(`✅ ${command} → Success`);
                    document.getElementById('current-effect').textContent = result.current_effect;
                    updateConnectionStatus(true);
                } else {
                    addLog(`❌ ${command} → ${result.message}`);
                    updateConnectionStatus(false);
                }
            } catch (error) {
                addLog(`❌ Network Error: ${error.message}`);
                updateConnectionStatus(false);
            }
        }

        // Start animation effect
        function startEffect(effect) {
            sendCommand(`start ${effect}`);
        }

        // Speed and brightness preset mappings
        const speedPresets = {
            0: { label: 'Super Slow', value: 1000 },
            1: { label: 'Slow', value: 500 },
            2: { label: 'Normal', value: 200 },
            3: { label: 'Fast', value: 100 },
            4: { label: 'Super Fast', value: 50 }
        };

        const brightnessPresets = {
            0: { label: 'Off', value: 0 },
            1: { label: 'Dim', value: 3 },
            2: { label: 'Normal', value: 8 },
            3: { label: 'Bright', value: 12 },
            4: { label: 'Max', value: 15 }
        };

        // Update brightness
        function updateBrightness(presetIndex) {
            const preset = brightnessPresets[presetIndex];
            document.getElementById('brightness-value').textContent = preset.label;
            sendCommand(`brightness ${preset.value}`);
        }

        // Update speed
        function updateSpeed(presetIndex) {
            const preset = speedPresets[presetIndex];
            document.getElementById('speed-value').textContent = preset.label;
            sendCommand(`speed ${preset.value}`);
        }

        // Update text
        function updateText() {
            const text = document.getElementById('custom-text').value;
            if (text.trim()) {
                sendCommand(`text ${text}`);
                addLog(`📝 Text set to: "${text}"`);
            }
        }

        // Update connection status
        function updateConnectionStatus(connected) {
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('connection-status');

            if (connected) {
                statusDot.className = 'status-dot connected';
                statusText.textContent = 'Connected';
            } else {
                statusDot.className = 'status-dot disconnected';
                statusText.textContent = 'Disconnected';
            }
        }

        // Add log entry
        function addLog(message) {
            const log = document.getElementById('log');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.textContent = `${new Date().toLocaleTimeString()} - ${message}`;
            log.appendChild(entry);
            log.scrollTop = log.scrollHeight;

            // Keep only last 20 entries
            while (log.children.length > 20) {
                log.removeChild(log.firstChild);
            }
        }

        // Show port status message
        function showPortStatus(message, type) {
            const statusDiv = document.getElementById('port-status');
            statusDiv.textContent = message;
            statusDiv.className = `port-status ${type}`;
            statusDiv.style.display = 'block';
        }

        // Handle Enter key in text input
        document.getElementById('custom-text').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                updateText();
            }
        });

        // Check connection status periodically
        setInterval(async function() {
            try {
                const response = await fetch('/status');
                const status = await response.json();
                updateConnectionStatus(status.connected);
                document.getElementById('current-effect').textContent = status.current_effect;

                // Update port display if it has changed
                updatePortStatus(status.port);
            } catch (error) {
                updateConnectionStatus(false);
            }
        }, 5000); // Check every 5 seconds

        // Port management functions
        async function scanPorts() {
            try {
                const response = await fetch('/available-ports');
                const data = await response.json();

                const dropdown = document.getElementById('port-dropdown');
                dropdown.innerHTML = '';

                // Add default option
                const defaultOption = document.createElement('option');
                defaultOption.value = '';
                defaultOption.textContent = 'Select a port...';
                dropdown.appendChild(defaultOption);

                if (data.ports && data.ports.length > 0) {
                    data.ports.forEach(port => {
                        const option = document.createElement('option');
                        option.value = port.device;
                        option.textContent = `${port.device} - ${port.description}`;
                        dropdown.appendChild(option);
                    });
                    showPortStatus('Found ' + data.ports.length + ' available ports', 'info');
                } else {
                    showPortStatus('No serial ports detected', 'error');
                }
            } catch (error) {
                showPortStatus('Error scanning ports: ' + error.message, 'error');
            }
        }

        async function connectToSelectedPort() {
            const selectedPort = document.getElementById('port-dropdown').value;

            if (!selectedPort) {
                return; // No port selected
            }

            showPortStatus('Connecting to ' + selectedPort + '...', 'info');
            addLog('🔌 Attempting to connect to: ' + selectedPort);

            try {
                const response = await fetch('/change-port', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ port: selectedPort })
                });

                const result = await response.json();

                if (result.status === 'success') {
                    showPortStatus('✅ Connected to ' + selectedPort, 'success');
                    addLog('✅ Successfully connected to: ' + selectedPort);
                    updateConnectionStatus(true);

                    // Update the port display in the status section
                    updatePortStatus(selectedPort);
                } else {
                    showPortStatus('❌ Failed to connect: ' + result.message, 'error');
                    addLog('❌ Connection failed: ' + result.message);
                    updateConnectionStatus(false);

                    // Reset dropdown to empty selection on failure
                    document.getElementById('port-dropdown').value = '';
                }
            } catch (error) {
                showPortStatus('❌ Connection error: ' + error.message, 'error');
                addLog('❌ Connection error: ' + error.message);
                updateConnectionStatus(false);

                // Reset dropdown to empty selection on failure
                document.getElementById('port-dropdown').value = '';
            }
        }

        // Update the port display in the status section
        function updatePortStatus(port) {
            const portElements = document.querySelectorAll('.status-item span');
            portElements.forEach(element => {
                if (element.previousElementSibling && element.previousElementSibling.textContent === 'Port:') {
                    element.textContent = port;
                }
            });
        }

        async function reconnectCurrent() {
            showPortStatus('Reconnecting to current port...', 'info');

            try {
                const response = await fetch('/reconnect', { method: 'POST' });
                const result = await response.json();

                if (result.status === 'success') {
                    showPortStatus('✅ Reconnected successfully', 'success');
                    addLog('🔌 Reconnected to current port');
                    updateConnectionStatus(true);
                } else {
                    showPortStatus('❌ Reconnection failed: ' + result.message, 'error');
                    updateConnectionStatus(false);
                }
            } catch (error) {
                showPortStatus('❌ Reconnection error: ' + error.message, 'error');
                updateConnectionStatus(false);
            }
        }

        // Initialize
        window.onload = function() {
            // Scan for available ports on load
            scanPorts();

            setTimeout(() => {
                addLog('🎯 Ready to control your LED matrix!');
                addLog('🔌 Select a port from the dropdown to connect!');
            }, 1000);
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main web interface"""
    return render_template_string(HTML_TEMPLATE,
                                connected=matrix_controller.connected,
                                current_effect=matrix_controller.current_effect,
                                port=matrix_controller.port)

@app.route('/command', methods=['POST'])
def handle_command():
    """Handle command from web interface"""
    try:
        data = request.get_json()
        command = data.get('command', '')

        if not command:
            return jsonify({"status": "error", "message": "No command provided"})

        result = matrix_controller.send_command(command)
        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/available-ports')
def available_ports():
    """Get list of available serial ports"""
    try:
        ports = serial.tools.list_ports.comports()
        port_list = []

        for port in ports:
            port_list.append({
                'device': port.device,
                'description': port.description,
                'hwid': port.hwid if hasattr(port, 'hwid') else ''
            })

        return jsonify({
            "status": "success",
            "ports": port_list
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "ports": []
        })

@app.route('/test-port', methods=['POST'])
def test_port():
    """Test connection to a specific port without switching"""
    try:
        data = request.get_json()
        test_port_path = data.get('port', '')

        if not test_port_path:
            return jsonify({"status": "error", "message": "No port specified"})

        # Try to connect to the port
        test_serial = serial.Serial(
            test_port_path,
            SERIAL_BAUDRATE,
            timeout=2
        )
        time.sleep(1)  # Brief connection test
        test_serial.close()

        return jsonify({
            "status": "success",
            "message": f"Port {test_port_path} is available and responding"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Port test failed: {str(e)}"
        })

@app.route('/change-port', methods=['POST'])
def change_port():
    """Change to a new serial port"""
    try:
        data = request.get_json()
        new_port = data.get('port', '')

        if not new_port:
            return jsonify({"status": "error", "message": "No port specified"})

        # Disconnect from current port
        matrix_controller.disconnect()

        # Connect to new port
        success = matrix_controller.connect(new_port)

        if success:
            return jsonify({
                "status": "success",
                "message": f"Successfully switched to {new_port}",
                "current_port": new_port
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Failed to connect to {new_port}"
            })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Port change failed: {str(e)}"
        })

@app.route('/status')
def status():
    """Get current status"""
    return jsonify({
        "connected": matrix_controller.connected,
        "current_effect": matrix_controller.current_effect,
        "last_command": matrix_controller.last_command,
        "port": matrix_controller.port or "None"
    })

@app.route('/reconnect', methods=['POST'])
def reconnect():
    """Reconnect to the current LED matrix port"""
    try:
        if not matrix_controller.port:
            return jsonify({"status": "error", "message": "No port selected"})

        current_port = matrix_controller.port
        matrix_controller.disconnect()
        time.sleep(1)
        success = matrix_controller.connect(current_port)

        if success:
            return jsonify({"status": "success", "message": "Reconnected successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to reconnect"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def cleanup():
    """Cleanup function"""
    if matrix_controller:
        matrix_controller.disconnect()

if __name__ == '__main__':
    import atexit
    import os
    atexit.register(cleanup)

    # Check if running as a service (installed in /opt/picopixels)
    is_service = os.path.dirname(os.path.abspath(__file__)) == '/opt/picopixels'
    port = 5123 if is_service else 5000
    
    print("🚀 Starting LED Matrix Web Controller...")
    if is_service:
        print("🔧 Running as system service")

    print("🌐 Starting web server...")
    print()
    print("=" * 50)
    print("🎉 LED Matrix Web Controller Ready!")
    print()
    print("📱 Open your browser and go to:")
    print(f"   http://localhost:{port}")
    print(f"   http://127.0.0.1:{port}")
    print()
    print("🔧 To use on other devices on your network:")
    print("   Find your computer's IP address and use:")
    print(f"   http://YOUR_IP_ADDRESS:{port}")
    print()
    print("⚡ Controls available:")
    print("   • All animation effects")
    print("   • Brightness control")
    print("   • Speed control")
    print("   • Custom text messages")
    print("   • Real-time status monitoring")
    print()
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    print()

    try:
        app.run(host='0.0.0.0', port=port, debug=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        cleanup()
