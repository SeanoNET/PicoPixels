# LED Matrix Control Suite

A complete LED matrix controller and animation system for the Raspberry Pi Pico using MicroPython and a web-based UI. This project allows you to send commands and animations to a 32x8 LED matrix display over serial using a modern, responsive web interface.

---

## 🔧 Features
- Web UI built with Flask and HTML/JS
- Select serial device from dropdown (backend-driven)
- Multiple animated effects:
  - Matrix Rain
  - Fire simulation
  - Plasma, Waves, Scanner
  - Bouncing Balls
  - Pong game
  - Clock display (12/24h, blinking colon, with/without seconds)
  - Scrolling text
- Brightness and speed controls
- Custom text support
- Tested on Raspberry Pi Pico

---

## 🧠 Inspiration & Credit
- Inspired by the **WOPR LED Enclosure** project:
  [https://www.printables.com/model/1167457-1u-rack-mount-wopr-leds-enclosure](https://www.printables.com/model/1167457-1u-rack-mount-wopr-leds-enclosure)

- Hardware driver via `max7219.py`:
  [https://github.com/mcauser/micropython-max7219](https://github.com/mcauser/micropython-max7219)

- Guide for wiring and setup:
  [MicrocontrollersLab - MAX7219 with Pi Pico](https://microcontrollerslab.com/max7219-led-dot-matrix-display-raspberry-pi-pico/)

- [Claude](https://claude.ai/)
---

## 📦 Hardware Requirements
- Raspberry Pi Pico (with MicroPython installed)
- MAX7219 8x8 LED Matrix (4 modules recommended, e.g. 32x8)
- Jumper wires, breadboard

## Enclosure
I am working on a 3d model enclosure for this, I will upload once ready.

### Wiring Example (SPI0)
| MAX7219 Pin | Pico Pin |
|------------|----------|
| VCC        | 3.3V     |
| GND        | GND      |
| DIN        | GP3      |
| CS         | GP5      |
| CLK        | GP2      |

---

## 💻 Uploading to the Pico
1. Flash MicroPython firmware to the Raspberry Pi Pico
2. Use [Thonny](https://thonny.org/) to:
   - Upload `main.py` and `max7219.py` to the Pico
   - Set `main.py` as the startup script
3. Open Thonny’s serial terminal to view logs or test input commands

---

## 🌐 Running the Web UI
1. Clone this repo on your desktop machine
2. Install dependencies (Python 3.x)
   ```bash
   pip install flask pyserial
   ```
3. Run the web controller:
   ```bash
   python app.py
   ```
4. Visit `http://localhost:5000` in your browser
5. Select a serial port, click connect, and send effects!

---

## 🛠️ Commands (via Web UI or Serial)
- `start <effect>` – Start looping animation
- `stop` – Stop current animation
- `<effect>` – Run effect once (e.g. `test`, `border`, `on`, `off`)
- `brightness <0-15>` – Set brightness
- `speed <ms>` – Set speed of animation
- `text <message>` – Set scrolling text
- `clock [12/24] [seconds/noseconds] [blink/noblink]`
- `help` – Show command list
-

---

## 📸 Screenshots
![Home](docs/home.png "Home")

---
