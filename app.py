import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "prueba123")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")


@app.route("/", methods=["GET"])
def home():
    return "Bot activo", 200


@app.route("/webhook", methods=["GET"])
def verify():
    try:
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token incorrecto", 403
    except Exception as e:
        return f"Error interno: {str(e)}", 500


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


