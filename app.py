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
CSV_URL = os.environ.get("CSV_URL", "https://raw.githubusercontent.com/iedilhuef7-sudo/chatbot-jr/main/CHATBOT.csv")
DB_FILE = "chatbot.db"

usuarios = {}

# =========================
# CARGAR BASE DE VOTACIONES
# =========================
def cargar_base():
    try:
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)

        r = requests.get(CSV_URL)
        r.raise_for_status()

        with open("CHATBOT.csv", "w", encoding="utf-8") as f:
            f.write(r.text)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

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

        c.execute("""
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            documento TEXT,
            celular TEXT,
            municipio TEXT
        )
        """)

        with open("CHATBOT.csv", newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                c.execute("""
                INSERT INTO votaciones (provincia, municipio, zonas, puesto, mesas, votacion_jr, votacion_total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['PROVINCIA'].strip(),
                    row['MUNICIPIO'].strip(),
                    row['ZONAS'].strip(),
                    row['PUESTO'].strip(),
                    int(row['MESAS']),
                    int(row['VOTACION JR']),
                    int(row['VOTACION TOTAL'])
                ))

        conn.commit()
        conn.close()
        print("✅ Base cargada")

    except Exception as e:
        print("❌ Error:", e)

# =========================
# HOME
# =========================
@app.route("/", methods=["GET"])
def home():
    return "Bot activo", 200

# =========================
# WEBHOOK VERIFY
# =========================
@app.route("/webhook", methods=["GET"])
def verify():
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if token == VERIFY_TOKEN:
        return challenge, 200
    return "Token incorrecto", 403

# =========================
# WEBHOOK POST
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    try:
        for entry in data["entry"]:
            for change in entry["changes"]:
                value = change["value"]
                if "messages" in value:
                    for msg in value["messages"]:
                        if msg["type"] == "text":
                            wa_id = msg["from"]
                            texto = msg["text"]["body"]

                            if wa_id not in usuarios:
                                usuarios[wa_id] = {"estado": "inicio"}

                            respuesta = manejar_conversacion(wa_id, texto)
                            enviar_mensaje(wa_id, respuesta)
    except Exception as e:
        print("Error webhook:", e)

    return jsonify({"status": "ok"}), 200

# =========================
# CONVERSACIÓN
# =========================
def manejar_conversacion(wa_id, texto):
    texto = texto.strip()
    usuario = usuarios[wa_id]

    if usuario["estado"] == "inicio":
        usuario["estado"] = "esperando_nombre"
        return "👋 Hola\n\n👉 Escribe tu nombre completo:"

    elif usuario["estado"] == "esperando_nombre":
        usuario["nombre"] = texto
        usuario["estado"] = "esperando_documento"
        return "👉 Escribe tu documento de identidad:"

    elif usuario["estado"] == "esperando_documento":
        usuario["documento"] = texto
        usuario["estado"] = "esperando_municipio"
        return "👉 ¿De qué municipio nos escribes?"

    elif usuario["estado"] == "esperando_municipio":
        usuario["municipio"] = texto
        usuario["celular"] = wa_id
        guardar_persona(usuario)
        usuario["estado"] = "registrado"
        return menu_principal()

    elif usuario["estado"] == "esperando_consulta":
        usuario["estado"] = "registrado"
        return consultar_votacion(texto)

    elif usuario["estado"] == "encuesta":
        usuario["estado"] = "registrado"
        return "🙏 Gracias por tu opinión. ¡Seguimos trabajando por Cundinamarca! 💚"

    else:
        return procesar_mensaje(wa_id, texto)

# =========================
# GUARDAR PERSONA
# =========================
def guardar_persona(usuario):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO personas (nombre, documento, celular, municipio)
        VALUES (?, ?, ?, ?)
    """, (
        usuario["nombre"],
        usuario["documento"],
        usuario["celular"],
        usuario["municipio"]
    ))
    conn.commit()
    conn.close()

# =========================
# MENÚ
# =========================
def menu_principal():
    return (
        "📋 MENÚ\n\n"
        "1️⃣ ¿Quién es Julio Roberto Salazar?\n"
        "2️⃣ ¿A qué partido pertenece?\n"
        "3️⃣ ¿Cómo se puede votar?\n"
        "4️⃣ Experiencia\n"
        "5️⃣ Comisiones del Congreso\n"
        "6️⃣ Causas que defiende\n"
        "7️⃣ Proyectos para el campo\n"
        "8️⃣ Seguridad\n"
        "9️⃣ Consultar votaciones anteriores\n"
        "10️⃣ Ranking municipios\n"
        "11️⃣ Contacto\n"
        "12️⃣ Finalizar"
    )

# =========================
# PROCESAR MENSAJE
# =========================
def procesar_mensaje(wa_id, texto):
    texto = texto.lower().strip()
    usuario = usuarios[wa_id]

    if texto == "1":
        return "Julio Roberto Salazar es Representante a la Cámara por Cundinamarca, ingeniero civil y magíster en gerencia 🌱"

    elif texto == "2":
        return "Pertenece al Partido Conservador Colombiano 💙."

    elif texto == "3":
        return "Marca el número 💙 C101 💙 en el tarjetón de Cámara – Cundinamarca."

    elif texto == "4":
        return "Cuenta con amplia experiencia en gestión pública y ambiental."

    elif texto == "5":
        return "Participa en Comisión Quinta, Paz, Transición Energética y Regalías."

    elif texto == "6":
        return "Defiende agro, medio ambiente, vejez digna, discapacidad y niñez."

    elif texto == "7":
        return "Impulsa UMATA, dignidad agropecuaria y vías rurales 🚜"

    elif texto == "8":
        return "Ha impulsado medidas contra la extorsión y protección de la niñez 🛡️"

    elif texto == "9":
        usuario["estado"] = "esperando_consulta"
        return "✍️ Escribe municipio o provincia:"

    elif texto == "10":
        return ranking_municipios()

    elif texto == "11":
        return (
            "📧 julio.salazar@camara.gov.co\n"
            "📧 comunicacionesjulioroberto@gmail.com\n"
            "📘 Facebook: Julio Roberto Salazar\n"
            "📸 Instagram: @JRobertoSalazarP\n"
            "🐦 X: @JRobertoSalazar\n"
            "🎥 TikTok: @JulioRobertoSalazarP"
        )

    elif texto == "12":
        usuario["estado"] = "encuesta"
        return "¿Pudiste resolver tu consulta? (sí / no)"

    return "❓ Escribe un número del menú."

# =========================
# CONSULTA VOTACIONES
# =========================
def consultar_votacion(texto):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    texto = texto.lower().strip()

    c.execute("""
        SELECT SUM(votacion_jr), SUM(votacion_total)
        FROM votaciones
        WHERE LOWER(TRIM(municipio)) = ?
    """, (texto,))
    r = c.fetchone()

    if r and r[0] is not None:
        conn.close()
        return f"📊 Municipio {texto.title()}:\nJR: {r[0]}\nTotal: {r[1]}"

    c.execute("""
        SELECT SUM(votacion_jr), SUM(votacion_total)
        FROM votaciones
        WHERE LOWER(TRIM(provincia)) = ?
    """, (texto,))
    r = c.fetchone()
    conn.close()

    if r and r[0] is not None:
        return f"📊 Provincia {texto.title()}:\nJR: {r[0]}\nTotal: {r[1]}"

    return "❌ No encontré datos."

# =========================
# RANKING
# =========================
def ranking_municipios():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT municipio, SUM(votacion_jr) as total
        FROM votaciones
        GROUP BY municipio
        ORDER BY total DESC
        LIMIT 5
    """)
    filas = c.fetchall()
    conn.close()

    texto = "🏆 TOP 5 MUNICIPIOS:\n"
    for i, fila in enumerate(filas, 1):
        texto += f"{i}. {fila[0]}: {fila[1]} votos\n"
    return texto

# =========================
# ENVIAR MENSAJE
# =========================
def enviar_mensaje(numero, mensaje):
    if not ACCESS_TOKEN or not PHONE_NUMBER_ID:
        print("Faltan tokens")
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
    requests.post(url, headers=headers, json=payload)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    cargar_base()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
