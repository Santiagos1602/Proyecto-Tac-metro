# Agregar después de calcular rpm en el loop:

if rpm == 0:
    led.value(0)              # Motor detenido — LED apagado
elif rpm < 1500:
    led.value(1)              # RPM bajo — LED encendido fijo
elif rpm < 3000:
    # RPM medio — parpadeo lento
    led.value(1); time.sleep_ms(200)
    led.value(0)
else:
    # RPM alto — parpadeo rápido (zona roja)
    for _ in range(5):
        led.value(1); time.sleep_ms(50)
        led.value(0); time.sleep_ms(50)