import requests
import csv
import sqlite3
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# =========================
# VARIABLES DE ENTORNO
# =========================
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "prueba123")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
CSV_URL = os.environ.get("CSV_URL", "https://raw.githubusercontent.com/tu_usuario/tu_repo/main/CHATBOT.CSV")
DB_FILE = "chatbot.db"

# =========================
# BASE TEMPORAL EN MEMORIA
# =========================
usuarios = {}

# =========================
# DESCARGAR Y CARGAR CSV EN SQLITE
# =========================
def cargar_base():
    try:
        r = requests.get(CSV_URL)
        r.raise_for_status()
        with open("CHATBOT.csv", "w", encoding="utf-8") as f:
            f.write(r.text)

        # Conectar a SQLite
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        # Crear tabla votaciones
        c.execute("""
        CREATE TABLE IF NOT EXISTS votaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provincia TEXT,
            municipio TEXT,
            zonas TEXT,
            puesto TEXT,
            mesas INTEGER,
            votacion_jr INTEGER,
            votacion_total INTEGER
        )
        """)

        # Cargar CSV
        with open("CHATBOT.csv", newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                c.execute("""
                INSERT OR REPLACE INTO votaciones (provincia, municipio, zonas, puesto, mesas, votacion_jr, votacion_total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['provincia'],
                    row['municipio'],
                    row.get('zonas', ''),
                    row.get('puesto', ''),
                    int(row['mesas']),
                    int(row['votacion_jr']),
                    int(row['votacion_total'])
                ))
        conn.commit()
        conn.close()
        print("Base de datos cargada ✅")
    except Exception as e:
        print("Error cargando base:", e)

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
        return "👋 ¡Bienvenido!\n\n👉 ¿Cuál es tu nombre completo?"
    elif usuario["estado"] == "esperando_nombre":
        usuario["nombre"] = texto
        usuario["estado"] = "esperando_municipio"
        return "Gracias 😊\n\n👉 ¿De qué municipio de Cundinamarca nos escribes?"
    elif usuario["estado"] == "esperando_municipio":
        usuario["municipio"] = texto
        usuario["estado"] = "registrado"
        return (
            f"Perfecto {usuario['nombre']} 💚\n\n"
            "Ahora puedes preguntarme sobre:\n\n"
            "1️⃣ ¿Quién es Julio Roberto?\n"
            "2️⃣ Experiencia\n"
            "3️⃣ Proyectos\n"
            "4️⃣ Cómo votar\n"
            "5️⃣ Medio ambiente\n"
            "6️⃣ Seguridad\n"
            "7️⃣ Adulto mayor\n"
            "8️⃣ Contacto\n"
            "9️⃣ Consultar votaciones anteriores"
        )
    else:
        return procesar_mensaje(wa_id, texto)

# =========================
# RESPUESTAS MENU Y CONSULTA
# =========================
def procesar_mensaje(wa_id, texto):
    texto = texto.strip().lower()
    usuario = usuarios[wa_id]

    # Opciones menú
    if texto == "1":
        return "Julio Roberto Salazar es Representante a la Cámara por Cundinamarca, ingeniero civil y líder social 🌱"
    elif texto == "2":
        return "Cuenta con trayectoria en gestión del agua, riesgo, acción comunal y medio ambiente 💪"
    elif texto == "3":
        return "Impulsa dignidad agropecuaria, fortalecimiento UMATA y vías rurales 🚜"
    elif texto == "4":
        return "🗳️ Para votar:\n1️⃣ Acude a tu puesto de votación\n2️⃣ Pide tarjetón Cámara – Cundinamarca\n3️⃣ Busca Partido Conservador\n4️⃣ Marca 💙 C101 💙\n5️⃣ Deposita tu voto"
    elif texto == "5":
        return "Defiende el agua, páramos y transición energética 🌿"
    elif texto == "6":
        return "Ha promovido medidas contra extorsión y protección de menores 🛡️"
    elif texto == "7":
        return "Promueve vejez digna y pensiones justas 👴👵"
    elif texto == "8":
        return "📧 julio.salazar@camara.gov.co\n📘 Facebook: Julio Roberto Salazar Perdomo\n📸 Instagram: @JRobertoSalazarP\n🐦 X: @JRobertoSalazar"
    elif texto == "9":
        return "Escribe el nombre de la provincia o municipio que quieres consultar:"

    # Consulta votaciones por provincia o municipio
    return consultar_votacion(texto)

# =========================
# CONSULTA VOTACIONES
# =========================
def consultar_votacion(texto):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Primero intentar como provincia
    c.execute("SELECT SUM(votacion_jr), SUM(votacion_total) FROM votaciones WHERE LOWER(provincia)=?", (texto.lower(),))
    result = c.fetchone()
    if result and result[0] is not None:
        vot_jr, vot_total = result
        conn.close()
        return f"📊 Sumatoria en la provincia {texto.title()}:\nVotación Julio Roberto: {vot_jr}\nVotación total: {vot_total}"

    # Si no, intentar como municipio
    c.execute("SELECT SUM(votacion_jr), SUM(votacion_total) FROM votaciones WHERE LOWER(municipio)=?", (texto.lower(),))
    result = c.fetchone()
    conn.close()
    if result and result[0] is not None:
        vot_jr, vot_total = result
        return f"📊 Sumatoria en el municipio {texto.title()}:\nVotación Julio Roberto: {vot_jr}\nVotación total: {vot_total}"

    return "No encontré información para ese municipio o provincia 😅"

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
# MAIN
# =========================
if __name__ == "__main__":
    cargar_base()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)










