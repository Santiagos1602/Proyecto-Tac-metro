from machine import Pin
import network, socket, time, json
import gc

# ── Hardware ─────────────────────────────────
hall   = Pin(4, Pin.IN, Pin.PULL_UP)
led = Pin(26, Pin.OUT)
pulsos = 0
rpm    = 0
rpm_max = 0
historial = []

def contar_pulso(pin):
    global pulsos
    pulsos += 1

hall.irq(trigger=Pin.IRQ_FALLING, handler=contar_pulso)

# ── WiFi Access Point ─────────────────────────
from config import SSID, PASSWORD,
  PANEL_KEY

ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid=SSID,
  password=PASSWORD)

# ── Servidor HTTP ─────────────────────────────
srv = socket.socket()
srv.bind(socket.getaddrinfo('0.0.0.0', 80)[0][-1])
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.listen(5)
print("Servidor activo — abre 192.168.4.1")

ultimo_calculo = time.ticks_ms()

sesiones = []  # IPs autorizadas

login_html = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0d0a;color:#e6edf3;font-family:monospace;
     min-height:100vh;display:flex;flex-direction:column;
     align-items:center;justify-content:center;padding:1.5rem}
h1{color:#39d353;margin-bottom:10px}
input{padding:14px;font-size:18px;border-radius:10px;
      border:1px solid #1e2e1e;width:240px;text-align:center;
      margin:8px 0;background:#111511;color:#e6edf3}
button{padding:14px 40px;font-size:18px;border-radius:10px;
       border:none;background:#39d353;color:#0a0d0a;
       cursor:pointer;font-weight:bold}
</style></head><body>
<h1>Tacometro Digital</h1>
<p>Ingrese la clave de acceso</p>
<input type='password' id='k' placeholder='Clave'>
<button onclick="location.href='/?clave='+document.getElementById('k').value">
Entrar</button>
</body></html>"""

while True:
    # Calcular RPM cada 1 segundo
    ahora = time.ticks_ms()
    if time.ticks_diff(ahora, ultimo_calculo) >= 1000:
        rpm = pulsos * 60
        pulsos = 0
        ultimo_calculo = ahora
        if rpm > rpm_max: rpm_max = rpm
        historial.append(rpm)
        if len(historial) > 20: historial.pop(0)

    # Atender petición HTTP
    try:
        srv.settimeout(0.1)
        cl, addr = srv.accept()
        peticion = cl.recv(1024).decode()
        ip_cliente = str(addr[0])

        # Verificar si envían clave
        if "clave=" in peticion:
            clave = peticion.split("clave=")[1].split(" ")[0].split("&")[0]
            if clave == PANEL_KEY:
                if ip_cliente not in sesiones:
                    sesiones.append(ip_cliente)

        # Si NO está autorizado, mostrar login
        if ip_cliente not in sesiones:
            cl.send(login_html)
            cl.close()
            gc.collect()
        else:
            # Cliente autorizado
            if '/datos' in peticion:
                datos = {
                    "rpm": rpm,
                    "rpm_max": rpm_max,
                    "historial": historial[-10:],
                    "estado": "ALTO" if rpm > 3000 else "NORMAL"
                }
                respuesta = ("HTTP/1.1 200 OK\r\n"
                            "Content-Type: application/json\r\n\r\n"
                            + json.dumps(datos))
                cl.send(respuesta)
        else:
            # ── Dashboard HTML principal ────────────
            html = """HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
<!DOCTYPE html><html><head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Tacómetro ESP32</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0a0d0a;color:#e6edf3;font-family:monospace;
     min-height:100vh;display:flex;flex-direction:column;
     align-items:center;justify-content:center;padding:1.5rem}
h1{color:#39d353;font-size:1.4rem;margin-bottom:0.3rem;text-align:center}
.sub{color:#6b7280;font-size:0.7rem;margin-bottom:2rem}
.rpm-big{font-size:6rem;font-weight:900;color:#39d353;
         text-shadow:0 0 40px #39d35340;line-height:1;
         transition:color 0.3s}
.rpm-unit{color:#6b7280;font-size:1rem;margin-bottom:0.5rem}
.estado{font-size:0.9rem;font-weight:bold;margin-bottom:1.5rem;transition:color 0.3s}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;
       width:100%;max-width:360px}
.card{background:#111511;border:1px solid #1e2e1e;border-radius:10px;
      padding:1rem;text-align:center}
.card-val{font-size:1.8rem;font-weight:700;color:#39d353}
.card-lbl{color:#6b7280;font-size:0.7rem;margin-top:0.2rem}
.barra-wrap{width:100%;max-width:360px;margin-top:1rem;
            background:#111511;border:1px solid #1e2e1e;
            border-radius:10px;padding:1rem}
.barra-lbl{color:#6b7280;font-size:0.65rem;text-transform:uppercase;
           letter-spacing:0.1em;margin-bottom:0.5rem}
.barra{height:12px;background:#1e2e1e;border-radius:6px;overflow:hidden}
.barra-fill{height:100%;background:#39d353;border-radius:6px;
            transition:width 0.5s,background 0.3s}
.hist-wrap{width:100%;max-width:360px;margin-top:0.75rem;
           background:#111511;border:1px solid #1e2e1e;
           border-radius:10px;padding:1rem}
.hist-title{color:#6b7280;font-size:0.65rem;text-transform:uppercase;
            letter-spacing:0.1em;margin-bottom:0.5rem}
.barras-hist{display:flex;align-items:flex-end;gap:3px;height:50px}
.bar-h{background:#2ea043;border-radius:2px 2px 0 0;flex:1;
       transition:height 0.3s,background 0.3s;min-height:2px}
.refresh{color:#334155;font-size:0.65rem;margin-top:1rem}
</style></head><body>
<h1>⚙️ Tacómetro Digital</h1>
<div class='sub'>ESP32 · Sensor Hall · UAG Ing. Software</div>
<div class='rpm-big' id='rpm'>---</div>
<div class='rpm-unit'>RPM</div>
<div class='estado' id='estado'>Esperando motor...</div>
<div class='cards'>
  <div class='card'><div class='card-val' id='rmax'>---</div><div class='card-lbl'>RPM Máximas</div></div>
  <div class='card'><div class='card-val' id='pulsos'>---</div><div class='card-lbl'>Pulsos/seg</div></div>
</div>
<div class='barra-wrap'>
  <div class='barra-lbl'>Nivel de RPM (0 – 6000)</div>
  <div class='barra'><div class='barra-fill' id='bfill'></div></div>
</div>
<div class='hist-wrap'>
  <div class='hist-title'>Historial últimas 10 lecturas</div>
  <div class='barras-hist' id='hist'></div>
</div>
<div class='refresh'>↻ Actualizando cada 1s</div>
<script>
async function actualizar(){
  try{
    const r=await fetch('/datos');
    const d=await r.json();
    const rpm=d.rpm;
    const color=rpm>3000?'#ff4444':rpm>1500?'#ffd700':'#39d353';
    document.getElementById('rpm').textContent=rpm;
    document.getElementById('rpm').style.color=color;
    document.getElementById('rmax').textContent=d.rpm_max;
    document.getElementById('pulsos').textContent=Math.round(rpm/60);
    document.getElementById('estado').textContent=
      rpm==0?'Motor detenido':d.estado=='ALTO'?'⚠ RPM ALTO':'✓ Normal';
    document.getElementById('estado').style.color=color;
    const pct=Math.min(100,Math.round(rpm/6000*100));
    document.getElementById('bfill').style.width=pct+'%';
    document.getElementById('bfill').style.background=color;
    const max=Math.max(...d.historial,1);
    document.getElementById('hist').innerHTML=
      d.historial.map(v=>
        `<div class='bar-h' style='height:${Math.round(v/max*100)}%;
         background:${v>3000?'#ff4444':v>1500?'#ffd700':'#2ea043'}'></div>`
      ).join('');
  }catch(e){}
}
setInterval(actualizar,1000);
actualizar();
</script></body></html>"""
            cl.send(html)

        cl.close()
        gc.collect()
    except OSError as e:
      if e.args[0] != 11:
        print("Error:", e)  