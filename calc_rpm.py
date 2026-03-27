from machine import Pin
import time

hall    = Pin(4, Pin.IN, Pin.PULL_UP)
led     = Pin(2, Pin.OUT)
pulsos  = 0
rpm     = 0

# ── Función de interrupción (ISR) ────────────
# Se llama AUTOMÁTICAMENTE cada vez que el imán pasa
def contar_pulso(pin):
    global pulsos
    pulsos += 1
    led.value(1)   # Flash visual del pulso
    led.value(0)

# Activar interrupción en flanco de bajada (imán detectado)
hall.irq(trigger=Pin.IRQ_FALLING, handler=contar_pulso)

print("=== TACÓMETRO DIGITAL ===")
print("Enciende el motor y observa las RPM...")
print("-" * 30)

while True:
    pulsos = 0           # Resetear contador
    time.sleep(1)        # Esperar 1 segundo

    # RPM = pulsos en 1 segundo × 60
    # (asume 1 imán por revolución)
    rpm = pulsos * 60

    print(f"Pulsos/seg: {pulsos:3d} | RPM: {rpm:6d}")