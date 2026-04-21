# 1. Download MicroPython (only needed once, you already have it)
wget https://github.com/jkorte-dev/micropython-board-NRF52840/raw/main/firmware/micropython-NRF52840-supermini-v1.24.0-preview.uf2

# 2. Double-tap reset on the board, wait for NICENANO to mount
watch -n 1 ls /run/media/eko/

# 3. Flash it
/usr/bin/cp micropython-NRF52840-supermini-v1.24.0-preview.uf2 /run/media/eko/NICENANO/

# 4. Connect to REPL
screen /dev/ttyACM1 115200

## Flashing MicroPython on nice!nano

### Requirements
- nice!nano v1 or v2
- Linux with `mpremote` installed

### Install mpremote
pip install mpremote --break-system-packages

### Flash MicroPython (one-time setup)
1. Download firmware:
   wget https://github.com/jkorte-dev/micropython-board-NRF52840/raw/main/firmware/micropython-NRF52840-supermini-v1.24.0-preview.uf2

2. Double-tap reset on board, wait for NICENANO to mount

3. Flash:
   /usr/bin/cp micropython-NRF52840-supermini-v1.24.0-preview.uf2 /run/media/$USER/NICENANO/

### Deploy firmware
mpremote connect /dev/ttyACM0 cp main.py :main.py
mpremote connect /dev/ttyACM0 reset

### REPL access
screen /dev/ttyACM0 115200

# Flash
mpremote connect /dev/ttyACM0 cp config.py :config.py
mpremote connect /dev/ttyACM0 cp bmi160.py :bmi160.py
mpremote connect /dev/ttyACM0 cp ssd1306.py :ssd1306.py
mpremote connect /dev/ttyACM0 cp main.py :main.py
mpremote connect /dev/ttyACM0 reset
