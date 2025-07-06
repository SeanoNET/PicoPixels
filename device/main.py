from machine import Pin, SPI
import max7219
import time
import random
import math
import sys

# Hardware setup
spi = SPI(0, sck=Pin(2), mosi=Pin(3))
cs = Pin(5, Pin.OUT)
display = max7219.Matrix8x8(spi, cs, 4)
display.brightness(5)

print("=== Full 32x8 LED Matrix System ===")

# Display dimensions
WIDTH = 32
HEIGHT = 8

# Global variables
current_effect = None
running = False
speed = 200
brightness = 5
last_update = 0

# Effect variables
drops = []
fire_buffer = [[0 for _ in range(WIDTH)] for _ in range(HEIGHT)]
plasma_offset = 0
wave_offset = 0
balls = []
scroll_text = "HELLO WORLD"
scroll_pos = WIDTH
pong_ball = {'x': WIDTH/2, 'y': HEIGHT/2, 'dx': 1, 'dy': 1}
pong_paddle1 = HEIGHT//2  # Left paddle position
pong_paddle2 = HEIGHT//2  # Right paddle position

# Clock settings
clock_24hour = True  # True for 24-hour format, False for 12-hour
clock_show_seconds = False  # True to show seconds
clock_blink_colon = True  # True to blink the colon separator

def all_on():
    display.fill(1)
    display.show()

def all_off():
    display.fill(0)
    display.show()

def border():
    display.fill(0)
    for x in range(WIDTH):
        display.pixel(x, 0, 1)
        display.pixel(x, HEIGHT-1, 1)
    for y in range(HEIGHT):
        display.pixel(0, y, 1)
        display.pixel(WIDTH-1, y, 1)
    display.show()

def test_pattern():
    print("Running test...")
    for i in range(3):
        all_on()
        time.sleep(0.3)
        all_off()
        time.sleep(0.3)
    border()
    time.sleep(1)
    all_off()
    print("Test complete")

def init_effects():
    """Initialize effect variables"""
    global drops, balls
    
    # Matrix rain - 6 drops for 32 wide display
    drops = []
    for i in range(6):
        drops.append({
            'x': random.randint(0, WIDTH-1),
            'y': random.randint(-5, 0),
            'length': random.randint(3, 5)
        })
    
    # Bouncing balls - 2 balls
    balls = []
    for i in range(2):
        balls.append({
            'x': random.randint(2, WIDTH-3),
            'y': random.randint(2, HEIGHT-3),
            'dx': random.choice([-1, 1]),
            'dy': random.choice([-1, 1])
        })

def matrix_rain():
    """Matrix rain effect"""
    global drops
    display.fill(0)
    
    for drop in drops:
        # Draw trail
        for i in range(drop['length']):
            y = drop['y'] - i
            if 0 <= y < HEIGHT:
                display.pixel(drop['x'], y, 1)
        
        # Move drop down
        drop['y'] += 1
        
        # Reset when off bottom
        if drop['y'] > HEIGHT + 2:
            drop['y'] = random.randint(-5, -1)
            drop['x'] = random.randint(0, WIDTH-1)
    
    display.show()

def fire_effect():
    """Fire simulation"""
    global fire_buffer
    
    # Cool down existing fire
    for y in range(HEIGHT-1):
        for x in range(WIDTH):
            fire_buffer[y][x] = max(0, fire_buffer[y][x] - random.randint(1, 2))
    
    # Add heat at bottom row
    for x in range(WIDTH):
        if random.random() < 0.6:
            fire_buffer[HEIGHT-1][x] = random.randint(10, 15)
    
    # Propagate heat upward
    for y in range(HEIGHT-2, -1, -1):
        for x in range(WIDTH):
            heat = fire_buffer[y+1][x]
            if x > 0:
                heat += fire_buffer[y+1][x-1]
            if x < WIDTH-1:
                heat += fire_buffer[y+1][x+1]
            fire_buffer[y][x] = max(0, heat // 3 - random.randint(0, 2))
    
    # Display fire
    display.fill(0)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if fire_buffer[y][x] > 7:
                display.pixel(x, y, 1)
    display.show()

def wave_effect():
    """Wave pattern"""
    global wave_offset
    display.fill(0)
    wave_offset += 0.3
    
    for x in range(WIDTH):
        # Two sine waves
        y1 = int(HEIGHT/2 + 2 * math.sin(x * 0.3 + wave_offset))
        y2 = int(HEIGHT/2 + 1.5 * math.sin(x * 0.4 + wave_offset + 1.5))
        
        # Keep in bounds
        y1 = max(0, min(HEIGHT-1, y1))
        y2 = max(0, min(HEIGHT-1, y2))
        
        display.pixel(x, y1, 1)
        display.pixel(x, y2, 1)
    
    display.show()

def plasma_effect():
    """Plasma mathematical pattern"""
    global plasma_offset
    display.fill(0)
    plasma_offset += 0.1
    
    for y in range(HEIGHT):
        for x in range(WIDTH):
            value = (math.sin(x * 0.2 + plasma_offset) + 
                    math.sin(y * 0.5 + plasma_offset * 1.2) + 
                    math.sin((x + y) * 0.15 + plasma_offset * 0.8)) / 3
            
            if value > 0.3:
                display.pixel(x, y, 1)
    
    display.show()

def bouncing_balls():
    """Bouncing balls"""
    global balls
    display.fill(0)
    
    for ball in balls:
        # Update position
        ball['x'] += ball['dx']
        ball['y'] += ball['dy']
        
        # Bounce off edges
        if ball['x'] <= 0 or ball['x'] >= WIDTH-1:
            ball['dx'] = -ball['dx']
            ball['x'] = max(0, min(WIDTH-1, ball['x']))
        
        if ball['y'] <= 0 or ball['y'] >= HEIGHT-1:
            ball['dy'] = -ball['dy']
            ball['y'] = max(0, min(HEIGHT-1, ball['y']))
        
        # Draw ball
        display.pixel(int(ball['x']), int(ball['y']), 1)
    
    display.show()

def scanner_effect():
    """KITT-style scanner - fixed to use full width"""
    global wave_offset
    wave_offset += 0.2
    display.fill(0)
    
    # Moving eye position - use full 32 pixel width
    pos = (math.sin(wave_offset) + 1) * (WIDTH - 6) / 2  # Scanner is 6 pixels wide
    center = int(pos)
    
    # Draw scanning pattern across full width
    for i in range(6):
        x = center + i
        if 0 <= x < WIDTH:
            # Bright center, dimmer edges
            if i == 2 or i == 3:  # Center pixels
                for y in range(HEIGHT):
                    display.pixel(x, y, 1)
            elif i == 1 or i == 4:  # Side pixels
                for y in range(2, HEIGHT-2):
                    display.pixel(x, y, 1)
    
    display.show()

def scrolling_text():
    """Simple scrolling text - with debug"""
    global scroll_pos, scroll_text
    
    print(f"DEBUG scrolling_text: Using text = '{scroll_text}'")
    
    display.fill(0)
    
    # Very simple 3-wide font
    simple_font = {
        'A': [0b111, 0b101, 0b111, 0b101, 0b101],
        'B': [0b110, 0b101, 0b110, 0b101, 0b110],
        'C': [0b111, 0b100, 0b100, 0b100, 0b111],
        'D': [0b110, 0b101, 0b101, 0b101, 0b110],
        'E': [0b111, 0b100, 0b111, 0b100, 0b111],
        'F': [0b111, 0b100, 0b111, 0b100, 0b100],
        'G': [0b111, 0b100, 0b101, 0b101, 0b111],
        'H': [0b101, 0b101, 0b111, 0b101, 0b101],
        'I': [0b111, 0b010, 0b010, 0b010, 0b111],
        'J': [0b111, 0b001, 0b001, 0b101, 0b111],
        'K': [0b101, 0b110, 0b100, 0b110, 0b101],
        'L': [0b100, 0b100, 0b100, 0b100, 0b111],
        'M': [0b101, 0b111, 0b101, 0b101, 0b101],
        'N': [0b101, 0b111, 0b111, 0b111, 0b101],
        'O': [0b111, 0b101, 0b101, 0b101, 0b111],
        'P': [0b111, 0b101, 0b111, 0b100, 0b100],
        'Q': [0b111, 0b101, 0b101, 0b111, 0b001],
        'R': [0b111, 0b101, 0b111, 0b110, 0b101],
        'S': [0b111, 0b100, 0b111, 0b001, 0b111],
        'T': [0b111, 0b010, 0b010, 0b010, 0b010],
        'U': [0b101, 0b101, 0b101, 0b101, 0b111],
        'V': [0b101, 0b101, 0b101, 0b101, 0b010],
        'W': [0b101, 0b101, 0b101, 0b111, 0b101],
        'X': [0b101, 0b010, 0b010, 0b010, 0b101],
        'Y': [0b101, 0b101, 0b010, 0b010, 0b010],
        'Z': [0b111, 0b001, 0b010, 0b100, 0b111],
        ' ': [0b000, 0b000, 0b000, 0b000, 0b000],
        '0': [0b111, 0b101, 0b101, 0b101, 0b111],
        '1': [0b010, 0b110, 0b010, 0b010, 0b111],
        '2': [0b111, 0b001, 0b111, 0b100, 0b111],
        '3': [0b111, 0b001, 0b111, 0b001, 0b111],
        '4': [0b101, 0b101, 0b111, 0b001, 0b001],
        '5': [0b111, 0b100, 0b111, 0b001, 0b111],
        '6': [0b111, 0b100, 0b111, 0b101, 0b111],
        '7': [0b111, 0b001, 0b001, 0b001, 0b001],
        '8': [0b111, 0b101, 0b111, 0b101, 0b111],
        '9': [0b111, 0b101, 0b111, 0b001, 0b111]
    }
    
    # Calculate total text width
    total_width = len(scroll_text) * 4  # 3 pixels + 1 space per character
    
    # Draw characters
    char_x = 0
    for char in scroll_text:
        if char in simple_font:
            pattern = simple_font[char]
            for row in range(5):
                for col in range(3):
                    x_pos = scroll_pos + char_x + col
                    y_pos = 1 + row  # Start at Y=1 to center in 8-pixel height
                    
                    if 0 <= x_pos < WIDTH and 0 <= y_pos < HEIGHT:
                        if pattern[row] & (1 << (2 - col)):
                            display.pixel(x_pos, y_pos, 1)
            char_x += 4  # 3 + 1 space
    
    # Move scroll position
    scroll_pos -= 1
    
    # Reset when text is completely off screen
    if scroll_pos < -total_width:
        scroll_pos = WIDTH
    
    display.show()

def pong_effect():
    """Pong game with AI paddles"""
    global pong_ball, pong_paddle1, pong_paddle2
    display.fill(0)
    
    # Move ball
    pong_ball['x'] += pong_ball['dx']
    pong_ball['y'] += pong_ball['dy']
    
    # Ball bounce off top/bottom
    if pong_ball['y'] <= 0 or pong_ball['y'] >= HEIGHT-1:
        pong_ball['dy'] = -pong_ball['dy']
        pong_ball['y'] = max(0, min(HEIGHT-1, pong_ball['y']))
    
    # AI paddle movement (follow ball)
    # Left paddle (x=0)
    if pong_ball['y'] > pong_paddle1:
        pong_paddle1 = min(pong_paddle1 + 1, HEIGHT-2)
    elif pong_ball['y'] < pong_paddle1:
        pong_paddle1 = max(pong_paddle1 - 1, 1)
    
    # Right paddle (x=31) - slightly slower AI
    if random.random() < 0.8:  # 80% chance to move (makes it beatable)
        if pong_ball['y'] > pong_paddle2:
            pong_paddle2 = min(pong_paddle2 + 1, HEIGHT-2)
        elif pong_ball['y'] < pong_paddle2:
            pong_paddle2 = max(pong_paddle2 - 1, 1)
    
    # Ball collision with paddles
    ball_x = int(pong_ball['x'])
    ball_y = int(pong_ball['y'])
    
    # Left paddle collision
    if ball_x <= 1 and abs(ball_y - pong_paddle1) <= 1:
        pong_ball['dx'] = abs(pong_ball['dx'])  # Bounce right
        # Add some angle based on where it hit the paddle
        if ball_y < pong_paddle1:
            pong_ball['dy'] = -1
        elif ball_y > pong_paddle1:
            pong_ball['dy'] = 1
    
    # Right paddle collision
    if ball_x >= WIDTH-2 and abs(ball_y - pong_paddle2) <= 1:
        pong_ball['dx'] = -abs(pong_ball['dx'])  # Bounce left
        # Add some angle based on where it hit the paddle
        if ball_y < pong_paddle2:
            pong_ball['dy'] = -1
        elif ball_y > pong_paddle2:
            pong_ball['dy'] = 1
    
    # Reset ball if it goes off screen (score)
    if ball_x < 0 or ball_x >= WIDTH:
        pong_ball['x'] = WIDTH/2
        pong_ball['y'] = HEIGHT/2
        pong_ball['dx'] = random.choice([-1, 1])
        pong_ball['dy'] = random.choice([-1, 1])
    
    # Draw left paddle (3 pixels tall)
    for i in range(-1, 2):
        y = pong_paddle1 + i
        if 0 <= y < HEIGHT:
            display.pixel(0, y, 1)
    
    # Draw right paddle (3 pixels tall)
    for i in range(-1, 2):
        y = pong_paddle2 + i
        if 0 <= y < HEIGHT:
            display.pixel(WIDTH-1, y, 1)
    
    # Draw ball
    if 0 <= ball_x < WIDTH and 0 <= ball_y < HEIGHT:
        display.pixel(ball_x, ball_y, 1)
    
    # Draw center line (dashed)
    for y in range(0, HEIGHT, 2):
        display.pixel(WIDTH//2, y, 1)
    
    display.show()

def moving_dot():
    """Simple moving dot"""
    global wave_offset
    wave_offset += 0.1
    display.fill(0)
    
    x = int((math.sin(wave_offset) + 1) * (WIDTH - 1) / 2)
    y = int((math.cos(wave_offset * 1.3) + 1) * (HEIGHT - 1) / 2)
    
    display.pixel(x, y, 1)
    display.show()

def clock_display():
    """Display current time"""
    global clock_24hour, clock_show_seconds, clock_blink_colon
    
    display.fill(0)
    
    # Get current time
    current_time = time.localtime()
    hours = current_time[3]
    minutes = current_time[4]
    seconds = current_time[5]
    
    # Convert to 12-hour format if needed
    is_pm = False
    if not clock_24hour:
        is_pm = hours >= 12
        if hours == 0:
            hours = 12
        elif hours > 12:
            hours -= 12
    
    # Mini font for digits (3x5)
    mini_font = {
        '0': [0b111, 0b101, 0b101, 0b101, 0b111],
        '1': [0b010, 0b110, 0b010, 0b010, 0b111],
        '2': [0b111, 0b001, 0b111, 0b100, 0b111],
        '3': [0b111, 0b001, 0b111, 0b001, 0b111],
        '4': [0b101, 0b101, 0b111, 0b001, 0b001],
        '5': [0b111, 0b100, 0b111, 0b001, 0b111],
        '6': [0b111, 0b100, 0b111, 0b101, 0b111],
        '7': [0b111, 0b001, 0b001, 0b001, 0b001],
        '8': [0b111, 0b101, 0b111, 0b101, 0b111],
        '9': [0b111, 0b101, 0b111, 0b001, 0b111],
        ':': [0b000, 0b010, 0b000, 0b010, 0b000],
        ' ': [0b000, 0b000, 0b000, 0b000, 0b000],
        'A': [0b111, 0b101, 0b111, 0b101, 0b101],
        'P': [0b111, 0b101, 0b111, 0b100, 0b100],
        'M': [0b101, 0b111, 0b101, 0b101, 0b101]
    }
    
    # Format time string
    if clock_show_seconds:
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        time_str = f"{hours:02d}:{minutes:02d}"
    
    # Calculate starting X position to center the time
    char_width = 4  # 3 pixels + 1 space
    total_width = len(time_str) * char_width - 1  # -1 for last space
    
    # Adjust for AM/PM indicator if in 12-hour mode
    if not clock_24hour:
        total_width += 8  # Space + AM/PM
    
    start_x = (WIDTH - total_width) // 2
    
    # Draw time
    x_pos = start_x
    for i, char in enumerate(time_str):
        # Blink colon if enabled
        if char == ':' and clock_blink_colon and seconds % 2 == 1:
            char = ' '  # Hide colon on odd seconds
        
        if char in mini_font:
            pattern = mini_font[char]
            for row in range(5):
                for col in range(3):
                    if 0 <= x_pos + col < WIDTH and 1 + row < HEIGHT:
                        if pattern[row] & (1 << (2 - col)):
                            display.pixel(x_pos + col, 1 + row, 1)
            x_pos += char_width
    
    # Add AM/PM indicator if in 12-hour mode
    if not clock_24hour:
        x_pos += 1  # Extra space
        am_pm = "PM" if is_pm else "AM"
        for char in am_pm:
            if char in mini_font:
                pattern = mini_font[char]
                for row in range(5):
                    for col in range(3):
                        if 0 <= x_pos + col < WIDTH and 1 + row < HEIGHT:
                            if pattern[row] & (1 << (2 - col)):
                                display.pixel(x_pos + col, 1 + row, 1)
                x_pos += char_width
    
    display.show()

# Effect dictionary
effects = {
    'matrix': matrix_rain,
    'fire': fire_effect,
    'wave': wave_effect,
    'plasma': plasma_effect,
    'balls': bouncing_balls,
    'scanner': scanner_effect,
    'text': scrolling_text,
    'dot': moving_dot,
    'pong': pong_effect,
    'border': border,
    'on': all_on,
    'off': all_off,
    'test': test_pattern,
    'clock': clock_display
}

def process_command(command):
    """Process commands"""
    global current_effect, running, speed, brightness, scroll_text, scroll_pos
    global clock_24hour, clock_show_seconds, clock_blink_colon
    
    try:
        parts = command.strip().split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        print(f"Command: {cmd}")
        
        if cmd == 'start':
            effect = parts[1] if len(parts) > 1 else 'matrix'
            if effect in effects:
                current_effect = effect
                running = True
                print(f"Started: {effect}")
                effects[effect]()  # Run once immediately
            else:
                print(f"Unknown effect: {effect}")
                print(f"Available: {list(effects.keys())}")
        
        elif cmd == 'stop':
            running = False
            current_effect = None
            all_off()
            print("Stopped")
        
        elif cmd in effects:
            # If it's the text effect, check if we're setting new text
            if cmd == 'text' and len(parts) > 1:
                # Setting new text
                scroll_text = ' '.join(parts[1:]).upper()
                scroll_pos = WIDTH
                print(f"Text set to: {scroll_text}")
                # Also run the effect once to show it
                effects[cmd]()
            # If it's the clock effect, check for options
            elif cmd == 'clock' and len(parts) > 1:
                # Parse clock options
                for opt in parts[1:]:
                    if opt.lower() == '12' or opt.lower() == '12h':
                        clock_24hour = False
                        print("Clock: 12-hour format")
                    elif opt.lower() == '24' or opt.lower() == '24h':
                        clock_24hour = True
                        print("Clock: 24-hour format")
                    elif opt.lower() == 'seconds' or opt.lower() == 'sec':
                        clock_show_seconds = True
                        print("Clock: Showing seconds")
                    elif opt.lower() == 'noseconds' or opt.lower() == 'nosec':
                        clock_show_seconds = False
                        print("Clock: Hiding seconds")
                    elif opt.lower() == 'blink':
                        clock_blink_colon = True
                        print("Clock: Colon blinking enabled")
                    elif opt.lower() == 'noblink':
                        clock_blink_colon = False
                        print("Clock: Colon blinking disabled")
                # Run the clock once
                effects[cmd]()
            else:
                # Just run the effect once
                effects[cmd]()
            print(f"Ran: {cmd}")
        
        elif cmd == 'brightness':
            if len(parts) > 1:
                try:
                    brightness = max(0, min(15, int(parts[1])))
                    display.brightness(brightness)
                    print(f"Brightness: {brightness}")
                except:
                    print("Invalid brightness")
        
        elif cmd == 'speed':
            if len(parts) > 1:
                try:
                    speed = max(50, min(2000, int(parts[1])))
                    print(f"Speed: {speed}ms")
                except:
                    print("Invalid speed")
        
        elif cmd == 'list':
            print(f"Effects: {list(effects.keys())}")
        
        elif cmd == 'help':
            print("Commands:")
            print("start <effect> - Start animated effect")
            print("stop - Stop animation")
            print("<effect> - Run effect once")
            print("brightness <0-15> - Set brightness")
            print("speed <50-2000> - Set animation speed")
            print("text <message> - Set scroll text")
            print("clock [12/24] [seconds/noseconds] [blink/noblink] - Show time")
            print("list - Show all effects")
        
        else:
            print(f"Unknown: {cmd}")
            print("Type 'help' for commands")
                
    except Exception as e:
        print(f"Command error: {e}")

# Initialize effects
init_effects()

# Run startup test
print("Running startup test...")
test_pattern()

print("Ready! Try these commands:")
print("start matrix")
print("start fire") 
print("start wave")
print("start scanner")
print("start pong")
print("text HELLO")
print("start text")
print("clock - Show current time")
print("start clock - Live clock")

# Main loop with fixed input handling
input_buffer = ""

while True:
    try:
        # Handle input
        try:
            import select
            if select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                if char:
                    if char == '\n' or char == '\r':
                        if input_buffer.strip():
                            print(f"DEBUG MAIN: Processing command: '{input_buffer.strip()}'")
                            process_command(input_buffer.strip())
                            input_buffer = ""
                    else:
                        input_buffer += char
        except Exception as e:
            print(f"DEBUG MAIN: Input error: {e}")
            pass
        
        # Run current effect
        if running and current_effect and current_effect in effects:
            current_time = time.ticks_ms()
            if time.ticks_diff(current_time, last_update) >= speed:
                effects[current_effect]()
                last_update = current_time
        
        time.sleep(0.01)
        
    except KeyboardInterrupt:
        print("Shutting down...")
        all_off()
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(0.1)
