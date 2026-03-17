from machine import Pin
import time

# Sensor Hall en D4 — activo en LOW (0 = imán cerca)
hall = Pin(4, Pin.IN, Pin.PULL_UP)
led  = Pin(2, Pin.OUT)

print("=== SENSOR HALL — Acerca el imán ===")

ultimo = 1

while True:
    actual = hall.value()
    if actual == 0 and ultimo == 1:
        print("🧲 PULSO detectado")
        led.value(1)
        time.sleep_ms(50)
        led.value(0)
    ultimo = actual
    time.sleep_ms(10)