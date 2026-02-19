import requests
import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIABLES DE ENTORNO
# =========================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "prueba123")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")

# =========================
# BASE DE DATOS
# =========================
DB_FILE = "usuarios.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            wa_id TEXT PRIMARY KEY,
            nombre TEXT,
            municipio TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

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
# EXPORTAR USUARIOS
# =========================
@app.route("/exportar", methods=["GET"])
def exportar():
    import csv
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios")
    rows = c.fetchall()
    conn.close()

    csv_file = "usuarios_export.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["wa_id", "nombre", "municipio"])
        writer.writerows(rows)

    return f"Archivo CSV generado: {csv_file}", 200

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

                            if wa_id not in usuarios:
                                usuarios[wa_id] = {"estado": "esperando_nombre"}

                            if msg.get("type") == "text":
                                texto = msg["text"]["body"]
                                respuesta = manejar_conversacion(wa_id, texto)
                                if respuesta:
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

    # Esperando nombre
    if usuario["estado"] == "esperando_nombre":
        usuario["nombre"] = texto
        usuario["estado"] = "esperando_municipio"
        return "Gracias 😊\n\n👉 ¿De qué municipio de Cundinamarca nos escribes?"

    # Esperando municipio
    elif usuario["estado"] == "esperando_municipio":
        usuario["municipio"] = texto
        usuario["estado"] = "registrado"

        # Guardar en base de datos
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO usuarios (wa_id, nombre, municipio)
            VALUES (?, ?, ?)
        """, (wa_id, usuario["nombre"], usuario["municipio"]))
        conn.commit()
        conn.close()

        # Enviar menú numerado
        menu = (
            f"Perfecto {usuario['nombre']} 💚\n\n"
            f"Te registramos como ciudadano de {usuario['municipio']}.\n\n"
            f"Ahora puedes preguntarme sobre escribiendo el número correspondiente:\n\n"
            "1️⃣ ¿Quién es Julio Roberto?\n"
            "2️⃣ Experiencia\n"
            "3️⃣ Proyectos\n"
            "4️⃣ Cómo votar\n"
            "5️⃣ Medio ambiente\n"
            "6️⃣ Seguridad\n"
            "7️⃣ Adulto mayor\n"
            "8️⃣ Contacto"
        )
        return menu

    # Ya registrado → procesar número o texto
    else:
        return procesar_mensaje(texto)

# =========================
# RESPUESTAS FAQ POLÍTICAS
# =========================
def procesar_mensaje(texto):
    texto = texto.strip().lower()
    if texto in ["1", "¿quién es julio roberto?", "quien es"]:
        return "Julio Roberto Salazar es Representante a la Cámara por Cundinamarca, ingeniero civil y líder social 🌱"
    elif texto in ["2", "experiencia"]:
        return "Cuenta con trayectoria en gestión del agua, riesgo, acción comunal y medio ambiente 💪"
    elif texto in ["3", "proyectos"]:
        return "Impulsa dignidad agropecuaria, fortalecimiento UMATA y vías rurales 🚜"
    elif texto in ["4", "cómo votar", "como votar"]:
        return "🗳️ Para votar:\n1️⃣ Acude a tu puesto de votación\n2️⃣ Pide tarjetón Cámara – Cundinamarca\n3️⃣ Busca Partido Conservador\n4️⃣ Marca 💙 C101 💙\n5️⃣ Deposita tu voto"
    elif texto in ["5", "medio ambiente"]:
        return "Defiende el agua, páramos y transición energética 🌿"
    elif texto in ["6", "seguridad"]:
        return "Ha promovido medidas contra extorsión y protección de menores 🛡️"
    elif texto in ["7", "adulto mayor", "vejez"]:
        return "Promueve vejez digna y pensiones justas 👴👵"
    elif texto in ["8", "contacto"]:
        return "📧 julio.salazar@camara.gov.co\n📧 comunicacionesjulioroberto@gmail.com\n\n📘 Facebook: Julio Roberto Salazar Perdomo\n📸 Instagram: @JRobertoSalazarP\n🐦 X: @JRobertoSalazar"
    else:
        return (
            "No entendí tu opción 😅\n\nPor favor escribe el número correspondiente:\n"
            "1️⃣ ¿Quién es Julio Roberto?\n"
            "2️⃣ Experiencia\n"
            "3️⃣ Proyectos\n"
            "4️⃣ Cómo votar\n"
            "5️⃣ Medio ambiente\n"
            "6️⃣ Seguridad\n"
            "7️⃣ Adulto mayor\n"
            "8️⃣ Contacto"
        )

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
        "text": {"body": mensaje}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Respuesta Meta:", response.status_code, response.text)

# =========================
# INICIO FLASK
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))




