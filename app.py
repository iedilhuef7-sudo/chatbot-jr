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
                            wa_id = msg["from"]

                            # Texto simple
                            if msg.get("type") == "text":
                                texto = msg["text"]["body"]
                                if wa_id not in usuarios:
                                    usuarios[wa_id] = {"estado": "inicio"}
                                respuesta = manejar_conversacion(wa_id, texto)
                                if respuesta:  # enviar solo si hay texto
                                    enviar_mensaje(wa_id, respuesta)

                            # Respuesta de lista interactiva
                            elif msg.get("type") == "interactive":
                                interactive = msg.get("interactive", {})
                                tipo = interactive.get("type")
                                if tipo == "list_reply":
                                    seleccion = interactive["list_reply"]["title"]
                                    respuesta = procesar_mensaje(seleccion)
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
        return "👋 ¡Bienvenido!\n\nPara continuar necesito algunos datos:\n\n👉 ¿Cuál es tu nombre completo?"

    # Captura nombre
    elif usuario["estado"] == "esperando_nombre":
        usuario["nombre"] = texto
        usuario["estado"] = "esperando_municipio"
        return "Gracias 😊\n\n👉 ¿De qué municipio de Cundinamarca nos escribes?"

    # Captura municipio y muestra menú
    elif usuario["estado"] == "esperando_municipio":
        usuario["municipio"] = texto
        usuario["estado"] = "registrado"

        opciones = [
            "¿Quién es Julio Roberto?",
            "Experiencia",
            "Proyectos",
            "Cómo votar",
            "Medio ambiente",
            "Seguridad",
            "Adulto mayor",
            "Contacto"
        ]

        enviar_mensaje(
            wa_id,
            f"Perfecto {usuario['nombre']} 💚\n\nTe registramos como ciudadano de {usuario['municipio']}.\n\nAhora puedes preguntarme sobre:",
            tipo="menu",
            opciones=opciones
        )
        return ""  # Ya enviamos el menú interactivo

    # Ya registrado → usar FAQ
    else:
        return procesar_mensaje(texto)

# =========================
# RESPUESTAS FAQ POLÍTICAS
# =========================
def procesar_mensaje(texto):
    texto = texto.lower()

    if "partido" in texto:
        return "Pertenezco al Partido Conservador Colombiano 💙. Trabajamos por Cundinamarca con compromiso social y ambiental."

    elif "votar" in texto:
        return "🗳️ Para votar:\n\n1️⃣ Acude a tu puesto de votación\n2️⃣ Pide tarjetón Cámara – Cundinamarca\n3️⃣ Busca Partido Conservador\n4️⃣ Marca 💙 C101 💙\n5️⃣ Deposita tu voto"

    elif "quien es" in texto or "julio roberto" in texto:
        return "Julio Roberto Salazar es Representante a la Cámara por Cundinamarca, ingeniero civil y líder social 🌱"

    elif "experiencia" in texto:
        return "Cuenta con trayectoria en gestión del agua, riesgo, acción comunal y medio ambiente 💪"

    elif "comision" in texto:
        return "Hace parte de:\n✔️ Comisión Quinta\n✔️ Comisión de Paz\n✔️ Comisión de Transición Energética"

    elif "campo" in texto or "agro" in texto:
        return "Impulsa dignidad agropecuaria, fortalecimiento UMATA y vías rurales 🚜"

    elif "seguridad" in texto:
        return "Ha promovido medidas contra extorsión y protección de menores 🛡️"

    elif "adulto" in texto or "vejez" in texto:
        return "Promueve vejez digna y pensiones justas 👴👵"

    elif "discapacidad" in texto:
        return "Autor de proyectos de apoyo a personas con discapacidad 💙"

    elif "medio ambiente" in texto or "sumapaz" in texto:
        return "Defiende el agua, páramos y transición energética 🌿"

    elif "contacto" in texto:
        return "📧 julio.salazar@camara.gov.co\n📧 comunicacionesjulioroberto@gmail.com\n\n📘 Facebook: Julio Roberto Salazar Perdomo\n📸 Instagram: @JRobertoSalazarP\n🐦 X: @JRobertoSalazar"

    else:
        return "👋 Estoy para ayudarte.\n\nPuedes preguntarme por:\n✔️ Quién es\n✔️ Experiencia\n✔️ Proyectos\n✔️ Cómo votar\n✔️ Medio ambiente\n✔️ Seguridad\n✔️ Adulto mayor\n✔️ Contacto"

# =========================
# ENVÍO MENSAJES
# =========================
def enviar_mensaje(numero, mensaje, tipo="text", opciones=None):
    """
    tipo: "text" o "menu"
    opciones: lista de opciones si tipo="menu"
    """
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("Faltan variables de entorno")
        return

    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    if tipo == "text" or not opciones:
        payload = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": mensaje}
        }

    elif tipo == "menu" and opciones:
        # Lista interactiva (hasta 10 opciones)
        lista_items = [{"id": f"item{i+1}", "title": opt} for i, opt in enumerate(opciones)]
        payload = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "body": {"text": mensaje},
                "action": {
                    "button": "Selecciona una opción",
                    "sections": [
                        {
                            "title": "Menú de opciones",
                            "rows": lista_items
                        }
                    ]
                }
            }
        }

    response = requests.post(url, headers=headers, json=payload)
    print("Respuesta Meta:", response.status_code, response.text)

# =========================
# INICIO FLASK
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


