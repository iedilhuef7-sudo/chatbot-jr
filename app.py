import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔐 CONFIGURACIÓN
VERIFY_TOKEN = "prueba123"

ACCESS_TOKEN = "EAAmKGOiDrvQBQ1fIEpOLH7lzXv8MLuMZAWpgP8euzahBuD7ZB5b8VSjvbymR2KSiQ1stZAUnTVZBn3qxdFZCxgCeDpqZBZARsTUHZCniukt8rAZBgsRavwp3wqzZCUJXeGKwTMqRR1AOfhWZAfGgZA7DUhcXehf3teX53EWCpQBRekr8aZCTyNZBdw1b4KhZCRopnb981oBi6ZCSqsipnsgAd0ZAy3mSeEOzyraGezYbDQaTt1GN8vs60K6y5dVusFzmlrPTjymnn16kqxd9JKu1IlweiZCwZDZD"
PHONE_NUMBER_ID = "1001578813037387"


# 🔎 VERIFICACIÓN DEL WEBHOOK (META)
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if token == VERIFY_TOKEN:
        return challenge
    return "Error de verificación", 403


# 📩 RECIBIR MENSAJES
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Mensaje recibido:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
        sender = data["entry"][0]["changes"][0]["value"]["messages"][0]["from"]

        response = procesar_mensaje(message)
        enviar_mensaje(sender, response)

    except Exception as e:
        print("Error:", e)

    return jsonify({"status": "ok"}), 200


# 🧠 LÓGICA DEL BOT
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


# 📤 ENVIAR MENSAJE A WHATSAPP
def enviar_mensaje(numero, mensaje):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": mensaje
        }
    }

    response = requests.post(url, headers=headers, json=data)
    print("Respuesta Meta:", response.text)


# 🚀 IMPORTANTE PARA RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


