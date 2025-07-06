import serial
import serial.tools.list_ports
import time
import sys

def find_ports():
    """Find available serial ports"""
    ports = serial.tools.list_ports.comports()
    available_ports = []
    
    print("Available serial ports:")
    for i, port in enumerate(ports):
        print(f"{i+1}. {port.device} - {port.description}")
        available_ports.append(port.device)
    
    return available_ports

def test_connection(port, baudrate):
    """Test connection to a specific port"""
    try:
        print(f"Testing connection to {port} at {baudrate} baud...")
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Wait for connection
        
        print("Connection successful!")
        
        # Send a test command
        print("Sending test command...")
        ser.write(b"help\n")
        ser.flush()
        
        # Wait for response
        time.sleep(1)
        response_received = False
        
        while ser.in_waiting:
            response = ser.readline().decode().strip()
            if response:
                print(f"Response: {response}")
                response_received = True
        
        if response_received:
            print("✓ Device is responding!")
            return True
        else:
            print("✗ No response from device")
            return False
            
    except serial.SerialException as e:
        print(f"✗ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        try:
            ser.close()
        except:
            pass

def test_pi_pico():
    """Test specifically for Pi Pico"""
    print("\n=== Pi Pico Connection Tester ===")
    
    # Find available ports
    ports = find_ports()
    
    if not ports:
        print("No serial ports found!")
        return
    
    # Common Pi Pico baudrates to test
    baudrates = [115200, 9600, 38400, 57600, 230400]
    
    # Test each port with each baudrate
    for port in ports:
        print(f"\nTesting port: {port}")
        
        for baudrate in baudrates:
            if test_connection(port, baudrate):
                print(f"\n🎉 SUCCESS! Use port={port}, baudrate={baudrate}")
                return port, baudrate
    
    print("\n❌ No working connections found")
    print("\nTroubleshooting tips:")
    print("1. Make sure Pi Pico is connected via USB")
    print("2. Check if the LED matrix code is running on the Pi Pico")
    print("3. Try pressing the reset button on the Pi Pico")
    print("4. Make sure no other programs are using the serial port")
    return None, None

def interactive_test():
    """Interactive testing mode"""
    print("\n=== Interactive Serial Test ===")
    
    # Get port from user
    ports = find_ports()
    
    if not ports:
        print("No ports found!")
        return
    
    try:
        port_choice = int(input(f"\nSelect port (1-{len(ports)}): ")) - 1
        if port_choice < 0 or port_choice >= len(ports):
            print("Invalid choice!")
            return
        
        port = ports[port_choice]
        
        # Get baudrate from user
        print("\nCommon baudrates:")
        baudrates = [9600, 38400, 57600, 115200, 230400]
        for i, rate in enumerate(baudrates):
            print(f"{i+1}. {rate}")
        
        rate_choice = int(input(f"Select baudrate (1-{len(baudrates)}): ")) - 1
        if rate_choice < 0 or rate_choice >= len(baudrates):
            print("Invalid choice!")
            return
        
        baudrate = baudrates[rate_choice]
        
        # Test the connection
        print(f"\nTesting {port} at {baudrate} baud...")
        
        try:
            ser = serial.Serial(port, baudrate, timeout=2)
            time.sleep(2)
            
            print("Connection opened successfully!")
            print("Type commands to send to the device (type 'quit' to exit):")
            
            while True:
                command = input("> ").strip()
                
                if command.lower() == 'quit':
                    break
                
                if command:
                    ser.write(f"{command}\n".encode())
                    ser.flush()
                    
                    time.sleep(0.5)
                    
                    while ser.in_waiting:
                        response = ser.readline().decode().strip()
                        if response:
                            print(f"Device: {response}")
            
            ser.close()
            
        except Exception as e:
            print(f"Error: {e}")
            
    except (ValueError, IndexError):
        print("Invalid input!")

def main():
    print("Pi Pico Serial Connection Tester")
    print("=" * 35)
    
    print("\nChoose an option:")
    print("1. Auto-detect Pi Pico connection")
    print("2. Manual/Interactive testing")
    print("3. Just list available ports")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == '1':
            port, baudrate = test_pi_pico()
            if port and baudrate:
                print(f"\nTo use with the LED matrix client:")
                print(f"python led_matrix_client.py {port}")
                print(f"Or modify the PORT and BAUDRATE variables in the client code")
        
        elif choice == '2':
            interactive_test()
        
        elif choice == '3':
            find_ports()
        
        else:
            print("Invalid choice!")
            
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()