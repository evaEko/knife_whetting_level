from machine import I2C, Pin

print("=== Full scan on OLED bus (SDA=6, SCL=8) ===")
i2c = I2C(1, sda=Pin(6), scl=Pin(8), freq=100000)
devs = i2c.scan()
print(f"All devices: {[hex(d) for d in devs]}")

# Try reading BMI160 chip ID at both possible addresses
for addr in [0x68, 0x69]:
    try:
        chip_id = i2c.readfrom_mem(addr, 0x00, 1)[0]
        print(f"  0x{addr:02x} chip_id = 0x{chip_id:02X}")
    except Exception as e:
        print(f"  0x{addr:02x} not responding: {e}")

# Check what 0x10 is
try:
    chip_id = i2c.readfrom_mem(0x10, 0x40, 1)[0]
    print(f"  0x10 BMM150 chip_id = 0x{chip_id:02X} (expect 0x32)")
except Exception as e:
    print(f"  0x10 read error: {e}")
