#!/usr/bin/env python3
"""
LED Matrix Web Controller
Simple Flask server to control LED matrix via web interface
"""

from flask import Flask, render_template_string, request, jsonify
import serial
import time
import threading
import json
from datetime import datetime

app = Flask(__name__)

# Configuration - adjust these for your setup
SERIAL_PORT = '/dev/ttyACM2'  # Change to your Pi Pico port (COM3 on Windows)
SERIAL_BAUDRATE = 115200
SERIAL_TIMEOUT = 1

class LEDMatrixController:
    def __init__(self, port=SERIAL_PORT, baudrate=SERIAL_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.connected = False
        self.last_command = None
        self.current_effect = "None"
        
        self.connect()
    
    def connect(self):
        """Connect to the Pi Pico"""
        try:
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
            elif command in ['test', 'border', 'on', 'off', 'clock']:
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

        .btn.clock {
            background: linear-gradient(45deg, #3498db, #2980b9);
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
            height: 6px;
            border-radius: 3px;
            background: #ddd;
            outline: none;
            position: relative;
        }

        /* Non-linear speed slider visual indicator */
        .slider#speed {
            background: linear-gradient(to right, 
                #4CAF50 0%,     /* Fast (green) */
                #4CAF50 30%,    
                #FFC107 30%,    /* Medium (yellow) */
                #FFC107 70%,    
                #f44336 70%,    /* Slow (red) */
                #f44336 100%
            );
        }

        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }

        .slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: linear-gradient(45deg, #667eea, #764ba2);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
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

        .clock-settings {
            background: #e3f2fd;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
        }

        .clock-options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }

        .toggle-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .toggle-switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }

        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .toggle-slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 24px;
        }

        .toggle-slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .toggle-slider {
            background-color: #3498db;
        }

        input:checked + .toggle-slider:before {
            transform: translateX(26px);
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
                <span>{{ port }}</span>
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
                <button class="btn clock" onclick="startEffect('clock')">Clock</button>
            </div>
        </div>

        <div class="section">
            <h3>🕐 Clock Settings</h3>
            <div class="clock-settings">
                <div class="clock-options">
                    <div class="toggle-group">
                        <label class="toggle-switch">
                            <input type="checkbox" id="clock-format" onchange="updateClockSettings()">
                            <span class="toggle-slider"></span>
                        </label>
                        <span>12-hour format</span>
                    </div>
                    <div class="toggle-group">
                        <label class="toggle-switch">
                            <input type="checkbox" id="show-seconds" onchange="updateClockSettings()">
                            <span class="toggle-slider"></span>
                        </label>
                        <span>Show seconds</span>
                    </div>
                    <div class="toggle-group">
                        <label class="toggle-switch">
                            <input type="checkbox" id="blink-colon" checked onchange="updateClockSettings()">
                            <span class="toggle-slider"></span>
                        </label>
                        <span>Blink colon</span>
                    </div>
                </div>
                <div class="button-grid" style="margin-top: 15px;">
                    <button class="btn clock" onclick="showClock()">Show Clock Once</button>
                    <button class="btn clock" onclick="startEffect('clock')">Start Live Clock</button>
                </div>
            </div>
        </div>

        <div class="section">
            <h3>🎛️ Settings</h3>
            
            <div class="control-group">
                <label>Brightness:</label>
                <input type="range" class="slider" id="brightness" min="0" max="15" value="5" 
                       oninput="updateBrightness(this.value)">
                <div class="value-display" id="brightness-value">5</div>
            </div>

            <div class="control-group">
                <label>Speed:</label>
                <input type="range" class="slider" id="speed" min="10" max="500" value="100" 
                       oninput="updateSpeed(this.value)">
                <div class="value-display" id="speed-value" style="min-width: 60px;">100ms</div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #666; margin-top: -10px; margin-bottom: 15px; padding: 0 95px;">
                <span>Fast</span>
                <span>Medium</span>
                <span>Slow</span>
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
        // Clock settings state
        let clockSettings = {
            format24: true,
            showSeconds: false,
            blinkColon: true
        };

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

        // Update brightness
        function updateBrightness(value) {
            document.getElementById('brightness-value').textContent = value;
            sendCommand(`brightness ${value}`);
        }

        // Update speed with non-linear scaling
        function updateSpeed(value) {
            // Non-linear scaling: more precision at lower speeds
            let actualSpeed;
            const sliderValue = parseInt(value);
            
            if (sliderValue <= 150) {
                // 10-150 on slider = 10-150ms (1:1 for fast speeds)
                actualSpeed = sliderValue;
            } else if (sliderValue <= 300) {
                // 150-300 on slider = 150-500ms (expanded range for medium)
                actualSpeed = 150 + ((sliderValue - 150) * 2.33);
            } else {
                // 300-500 on slider = 500-2000ms (expanded range for slow)
                actualSpeed = 500 + ((sliderValue - 300) * 7.5);
            }
            
            actualSpeed = Math.round(actualSpeed);
            document.getElementById('speed-value').textContent = actualSpeed + 'ms';
            sendCommand(`speed ${actualSpeed}`);
        }

        // Update text
        function updateText() {
            const text = document.getElementById('custom-text').value;
            if (text.trim()) {
                sendCommand(`text ${text}`);
                addLog(`📝 Text set to: "${text}"`);
            }
        }

        // Update clock settings
        function updateClockSettings() {
            const format12 = document.getElementById('clock-format').checked;
            const showSeconds = document.getElementById('show-seconds').checked;
            const blinkColon = document.getElementById('blink-colon').checked;
            
            clockSettings.format24 = !format12;
            clockSettings.showSeconds = showSeconds;
            clockSettings.blinkColon = blinkColon;
            
            // Build clock command with options
            let clockCommand = 'clock';
            if (format12) clockCommand += ' 12';
            else clockCommand += ' 24';
            
            if (showSeconds) clockCommand += ' seconds';
            else clockCommand += ' noseconds';
            
            if (blinkColon) clockCommand += ' blink';
            else clockCommand += ' noblink';
            
            sendCommand(clockCommand);
            addLog(`🕐 Clock settings updated`);
        }

        // Show clock once with current settings
        function showClock() {
            let clockCommand = 'clock';
            if (!clockSettings.format24) clockCommand += ' 12';
            if (clockSettings.showSeconds) clockCommand += ' seconds';
            if (!clockSettings.blinkColon) clockCommand += ' noblink';
            
            sendCommand(clockCommand);
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
            } catch (error) {
                updateConnectionStatus(false);
            }
        }, 5000); // Check every 5 seconds

        // Initialize
        window.onload = function() {
            setTimeout(() => {
                addLog('🎯 Ready to control your LED matrix!');
                addLog('🕐 Clock controls available with format options!');
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

@app.route('/status')
def status():
    """Get current status"""
    return jsonify({
        "connected": matrix_controller.connected,
        "current_effect": matrix_controller.current_effect,
        "last_command": matrix_controller.last_command,
        "port": matrix_controller.port
    })

@app.route('/reconnect', methods=['POST'])
def reconnect():
    """Reconnect to the LED matrix"""
    try:
        matrix_controller.disconnect()
        time.sleep(1)
        success = matrix_controller.connect()
        
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
    atexit.register(cleanup)
    
    print("🚀 Starting LED Matrix Web Controller...")
    print(f"📡 Connecting to LED Matrix on {SERIAL_PORT}...")
    
    if matrix_controller.connected:
        print("✅ Connected to LED Matrix!")
        print("🌐 Starting web server...")
        print()
        print("=" * 50)
        print("🎉 LED Matrix Web Controller Ready!")
        print()
        print("📱 Open your browser and go to:")
        print("   http://localhost:5000")
        print("   http://127.0.0.1:5000")
        print()
        print("🔧 To use on other devices on your network:")
        print("   Find your computer's IP address and use:")
        print("   http://YOUR_IP_ADDRESS:5000")
        print()
        print("⚡ Controls available:")
        print("   • All animation effects")
        print("   • Brightness control")
        print("   • Speed control") 
        print("   • Custom text messages")
        print("   • Clock display with format options")
        print("   • Real-time status monitoring")
        print()
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        print()
        
        try:
            app.run(host='0.0.0.0', port=5000, debug=False)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            cleanup()
    else:
        print("❌ Failed to connect to LED Matrix")
        print("🔧 Please check:")
        print(f"   • Pi Pico is connected to {SERIAL_PORT}")
        print("   • LED Matrix code is running on Pi Pico")
        print("   • No other programs are using the serial port")
        print("   • Update SERIAL_PORT in this script if needed")
        print()
        print("💡 Common ports:")
        print("   • Linux/Mac: /dev/ttyACM0, /dev/ttyUSB0")
        print("   • Windows: COM3, COM4, COM5")
        print()
        print("🔄 Edit the SERIAL_PORT variable at the top of this file")