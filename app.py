import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIABLES DE ENTORNO
# =========================

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "prueba123")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
# =========================
# BASE TEMPORAL EN MEMORIA
# =========================
usuarios = {}

# =========================
# HOME
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Bot activo", 200

# =========================
# VERIFICACIÓN WEBHOOK
# =========================
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge, 200
    else:
        return "Token incorrecto", 403

# =========================
# RECEPCIÓN MENSAJES
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Mensaje recibido:", data)

    try:
        if data and "entry" in data:
            for entry in data["entry"]:
                for change in entry["changes"]:
                    value = change.get("value", {})

                    if "messages" in value:
                        for msg in value["messages"]:
                            if msg.get("type") == "text":
                                wa_id = msg["from"]
                                texto = msg["text"]["body"]

                                if wa_id not in usuarios:
                                    usuarios[wa_id] = {"estado": "inicio"}

                                respuesta = manejar_conversacion(wa_id, texto)
                                enviar_mensaje(wa_id, respuesta)

    except Exception as e:
        print("Error en webhook:", e)

    return jsonify({"status": "ok"}), 200

# =========================
# MANEJO DE CONVERSACIÓN
# =========================
def manejar_conversacion(wa_id, texto):
    texto = texto.strip()
    usuario = usuarios[wa_id]

    # Inicio
    if usuario["estado"] == "inicio":
        usuario["estado"] = "esperando_nombre"
        return """👋 ¡Bienvenido!

Para continuar necesito algunos datos:

👉 ¿Cuál es tu nombre completo?"""

    # Captura nombre
    elif usuario["estado"] == "esperando_nombre":
        usuario["nombre"] = texto
        usuario["estado"] = "esperando_municipio"
        return "Gracias 😊\n\n👉 ¿De qué municipio de Cundinamarca nos escribes?"

    # Captura municipio
    elif usuario["estado"] == "esperando_municipio":
        usuario["municipio"] = texto
        usuario["estado"] = "registrado"

        return f"""Perfecto {usuario['nombre']} 💚

Te registramos como ciudadano de {usuario['municipio']}.

Ahora puedes preguntarme sobre:

✔️ ¿Quién es Julio Roberto?
✔️ Experiencia
✔️ Proyectos
✔️ Cómo votar
✔️ Medio ambiente
✔️ Seguridad
✔️ Adulto mayor
✔️ Contacto"""

    # Ya registrado → usar FAQ
    else:
        return procesar_mensaje(texto)

# =========================
# RESPUESTAS FAQ POLÍTICAS
# =========================
def procesar_mensaje(texto):
    texto = texto.lower()

    if "partido" in texto:
        return """Pertenezco al Partido Conservador Colombiano 💙. 
Trabajamos por Cundinamarca con compromiso social y ambiental."""

    elif "votar" in texto:
        return """🗳️ Para votar:

1️⃣ Acude a tu puesto de votación  
2️⃣ Pide tarjetón Cámara – Cundinamarca  
3️⃣ Busca Partido Conservador  
4️⃣ Marca 💙 C101 💙  
5️⃣ Deposita tu voto"""

    elif "quien es" in texto:
        return """Julio Roberto Salazar es Representante a la Cámara por Cundinamarca, ingeniero civil y líder social 🌱"""

    elif "experiencia" in texto:
        return """Cuenta con trayectoria en gestión del agua, riesgo, acción comunal y medio ambiente 💪"""

    elif "comision" in texto:
        return """Hace parte de:
✔️ Comisión Quinta
✔️ Comisión de Paz
✔️ Comisión de Transición Energética"""

    elif "campo" in texto or "agro" in texto:
        return """Impulsa dignidad agropecuaria, fortalecimiento UMATA y vías rurales 🚜"""

    elif "seguridad" in texto:
        return """Ha promovido medidas contra extorsión y protección de menores 🛡️"""

    elif "adulto" in texto or "vejez" in texto:
        return """Promueve vejez digna y pensiones justas 👴👵"""

    elif "discapacidad" in texto:
        return """Autor de proyectos de apoyo a personas con discapacidad 💙"""

    elif "medio ambiente" in texto or "sumapaz" in texto:
        return """Defiende el agua, páramos y transición energética 🌿"""

    elif "contacto" in texto:
        return """📧 julio.salazar@camara.gov.co  
📧 comunicacionesjulioroberto@gmail.com  

📘 Facebook: Julio Roberto Salazar Perdomo  
📸 Instagram: @JRobertoSalazarP  
🐦 X: @JRobertoSalazar"""

    else:
        return """👋 Estoy para ayudarte.

Puedes preguntarme por:

✔️ Quién es
✔️ Experiencia
✔️ Proyectos
✔️ Cómo votar
✔️ Medio ambiente
✔️ Seguridad
✔️ Adulto mayor
✔️ Contacto"""

# =========================
# ENVÍO MENSAJES
# =========================
def enviar_mensaje(numero, mensaje):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("Faltan variables de entorno")
        return

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("Respuesta Meta:", response.status_code, response.text)
