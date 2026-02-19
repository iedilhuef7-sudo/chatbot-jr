import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# CONFIG DESDE VARIABLES DE ENTORNO
# =========================

VERIFY_TOKEN = os.environ.get("prueba123")
ACCESS_TOKEN = os.environ.get("EAAmKGOiDrvQBQ1fIEpOLH7lzXv8MLuMZAWpgP8euzahBuD7ZB5b8VSjvbymR2KSiQ1stZAUnTVZBn3qxdFZCxgCeDpqZBZARsTUHZCniukt8rAZBgsRavwp3wqzZCUJXeGKwTMqRR1AOfhWZAfGgZA7DUhcXehf3teX53EWCpQBRekr8aZCTyNZBdw1b4KhZCRopnb981oBi6ZCSqsipnsgAd0ZAy3mSeEOzyraGezYbDQaTt1GN8vs60K6y5dVusFzmlrPTjymnn16kqxd9JKu1IlweiZCwZDZD")
PHONE_NUMBER_ID = os.environ.get("1001578813037387")


@app.route("/", methods=["GET"])
def home():
    return "Bot activo", 200


@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Error de verificación", 403


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
                            sender = msg["from"]

                            if msg.get("type") == "text":
                                texto = msg["text"]["body"]
                                respuesta = procesar_mensaje(texto)
                                enviar_mensaje(sender, respuesta)

    except Exception as e:
        print("Error en webhook:", e)

    return jsonify({"status": "ok"}), 200


def procesar_mensaje(texto):
    texto = texto.lower()

    if "1" in texto:
        return "Julio Roberto es Ingeniero Civil y Representante a la Cámara por Cundinamarca 💙"
    elif "2" in texto:
        return "Trabaja por el agro, medio ambiente, seguridad y comunidades 🌱"
    elif "3" in texto:
        return "Para votar marca Partido Conservador 💙 número C101"
    else:
        return """Hola 👋 Soy el asistente virtual de Julio Roberto Salazar 💚

1️⃣ ¿Quién es?
2️⃣ Proyectos
3️⃣ ¿Cómo votar?
"""


def enviar_mensaje(numero, mensaje):
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
