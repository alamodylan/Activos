from flask import Flask, render_template, request, redirect, url_for, send_file
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import qrcode
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# Configuración de la base de datos PostgreSQL
DATABASE_URL = "postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db"
AUTHORIZED_CODE = "atm2406"  # Código de autorización para modificar y eliminar

# Función para conectar a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        raise

# Crear la tabla activos si no existe
def crear_tablas():
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
    CREATE TABLE IF NOT EXISTS activos (
        id SERIAL PRIMARY KEY,
        codigo VARCHAR(50) NOT NULL,
        nombre VARCHAR(100) NOT NULL,
        ubicacion VARCHAR(100) NOT NULL,
        estado VARCHAR(50) NOT NULL,
        responsable VARCHAR(100),
        fecha_actualizacion TIMESTAMP DEFAULT NOW(),
        predio VARCHAR(50),
        marca VARCHAR(50),
        serie VARCHAR(50)
    );
    """
    try:
        cursor.execute(sql)
        conn.commit()
        print("✅ Tabla 'activos' creada exitosamente.")
    except Exception as e:
        print(f"❌ Error al crear la tabla: {e}")
    finally:
        cursor.close()
        conn.close()

# Página principal con búsqueda y filtrado
@app.route("/", methods=["GET"])
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    search_query = request.args.get("search", "").strip()
    filter_estado = request.args.get("estado", "").strip()

    sql = "SELECT * FROM activos WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (codigo ILIKE %s OR nombre ILIKE %s OR ubicacion ILIKE %s OR predio ILIKE %s)"
        params.extend([f"%{search_query}%"] * 4)

    if filter_estado:
        sql += " AND estado = %s"
        params.append(filter_estado)

    cursor.execute(sql, params)
    activos = cursor.fetchall()

    cursor.execute("SELECT DISTINCT estado FROM activos")
    rows = cursor.fetchall()
    estados = [row["estado"] for row in rows] if rows else []

    conn.close()
    return render_template("index.html", activos=activos, estados=estados, search_query=search_query, filter_estado=filter_estado)

# Registrar nuevo activo
@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        codigo_autorizacion = request.form.get("codigo_autorizacion")
        if codigo_autorizacion != AUTHORIZED_CODE:
            return render_template("registrar.html", error="Código de autorización incorrecto.")

        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        ubicacion = request.form["ubicacion"]
        estado = request.form["estado"]
        responsable = request.form["responsable"]
        predio = request.form["predio"]
        marca = request.form["marca"]
        serie = request.form["serie"]
        fecha = datetime.now()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO activos (codigo, nombre, ubicacion, estado, responsable, predio, marca, serie, fecha_actualizacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (codigo, nombre, ubicacion, estado, responsable, predio, marca, serie, fecha))
        conn.commit()
        conn.close()

        generar_codigo_qr(codigo, nombre)
        return redirect(url_for("index"))

    return render_template("registrar.html")

# Generar código QR
def generar_codigo_qr(codigo, nombre):
    qr_folder = "static/qr-codes"
    if not os.path.exists(qr_folder):
        os.makedirs(qr_folder)

    url_base = "https://tudominio.com/activo"
    contenido = f"{url_base}/{codigo}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(contenido)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(qr_folder, f"{codigo}.png")
    img.save(qr_path)
    print(f"✅ Código QR generado: {qr_path} -> {contenido}")

# Exportar activos a Excel
@app.route("/exportar_excel")
def exportar_excel():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activos")
    data = cursor.fetchall()
    conn.close()

    columnas = ["ID", "Código", "Nombre", "Ubicación", "Estado", "Responsable", "Fecha Actualización", "Predio", "Marca", "Serie"]
    
    df = pd.DataFrame([{col: row[col] for col in columnas} for row in data])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Activos")

    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="Listado_Activos.xlsx"
    )

if __name__ == "__main__":
    crear_tablas()
    app.run(host="0.0.0.0", port=8000, debug=True)
    