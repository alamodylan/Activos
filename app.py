from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import os
from datetime import datetime
import qrcode
import pandas as pd
from io import BytesIO
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# Ruta de la base de datos
DATABASE_URL = "postgres://SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a:5432/citasatm_user"
AUTHORIZED_CODE = "atm2406"  # Código de autorización para modificar y eliminar

# Conexión a la base de datos
def conectar_db():
    try:
        conn = psycopg2.connect(
            dbname="citasatm_user",
            user="SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV",
            password="SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV",
            host="dpg-ctdis2jv2p9s73ai7op0-a",
            port="5432"
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        raise
def crear_tablas():
    conn = conectar_db()  # Usa tu función conectar_db existente
    cursor = conn.cursor()

    # Comando SQL para crear la tabla `activos`
    sql = """
    CREATE TABLE IF NOT EXISTS activos (
        id SERIAL PRIMARY KEY,                 -- ID único y autoincremental
        codigo VARCHAR(50) NOT NULL,           -- Código del activo
        nombre VARCHAR(100) NOT NULL,          -- Nombre del activo
        ubicacion VARCHAR(100) NOT NULL,       -- Ubicación del activo
        estado VARCHAR(50) NOT NULL,           -- Estado (e.g., Activo/Inactivo)
        responsable VARCHAR(100),              -- Responsable del activo
        fecha_actualizacion TIMESTAMP DEFAULT NOW(), -- Fecha de actualización
        predio VARCHAR(50),                    -- Predio donde se encuentra el activo
        marca VARCHAR(50),                     -- Marca del activo
        serie VARCHAR(50)                      -- Serie del activo
    );
    """

    try:
        cursor.execute(sql)  # Ejecuta el comando SQL
        conn.commit()        # Guarda los cambios
        print("Tabla 'activos' creada exitosamente.")
    except Exception as e:
        print(f"Error al crear la tabla: {e}")
    finally:
        cursor.close()
        conn.close()

# Página principal con búsqueda y filtrado
@app.route("/", methods=["GET", "POST"])
def index():
    conn = conectar_db()
    cursor = conn.cursor()

    # Verificar si hay búsqueda o filtros aplicados
    search_query = request.args.get("search", "").strip()
    filter_estado = request.args.get("estado", "").strip()

    # Construir consulta SQL dinámicamente
    sql = "SELECT * FROM activos WHERE 1=1"
    params = []

    if search_query:
        sql += " AND (codigo LIKE ? OR nombre LIKE ? OR ubicacion LIKE ? OR predio LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])

    if filter_estado:
        sql += " AND estado = ?"
        params.append(filter_estado)

    cursor.execute(sql, params)
    activos = cursor.fetchall()
    conn.close()

    # Obtener opciones únicas para filtrar por estado
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT estado FROM activos")
    estados = [row[0] for row in cursor.fetchall()]
    conn.close()

    return render_template("index.html", activos=activos, estados=estados, search_query=search_query, filter_estado=filter_estado)

# Registro de nuevo activo con autorización
@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        # Verificar el código de autorización
        codigo_autorizacion = request.form.get("codigo_autorizacion")
        if codigo_autorizacion != AUTHORIZED_CODE:
            return render_template("registrar.html", error="Código de autorización incorrecto.")

        # Recopilar datos del formulario
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        ubicacion = request.form["ubicacion"]
        estado = request.form["estado"]
        responsable = request.form["responsable"]
        predio = request.form["predio"]
        marca = request.form["marca"]
        serie = request.form["serie"]
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insertar en la base de datos
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO activos (codigo, nombre, ubicacion, estado, responsable, predio, marca, serie, fecha_actualizacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (codigo, nombre, ubicacion, estado, responsable, predio, marca, serie, fecha))
        conn.commit()
        conn.close()

        # Generar código QR
        generar_codigo_qr(codigo, nombre)
        return redirect(url_for("index"))
    return render_template("registrar.html")

# Ver detalles de un activo
@app.route("/activo/<int:id>")
def ver_activo(id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activos WHERE id = ?", (id,))
    activo = cursor.fetchone()
    conn.close()
    return render_template("activo.html", activo=activo)

# Editar un activo con autorización
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_activo(id):
    conn = conectar_db()
    cursor = conn.cursor()

    if request.method == "POST":
  
        codigo_autorizacion = request.form.get("codigo_autorizacion")
        if codigo_autorizacion != AUTHORIZED_CODE:
            return render_template("editar.html", activo={"id": id}, error="Código de autorización incorrecto.")

       
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        ubicacion = request.form["ubicacion"]
        estado = request.form["estado"]
        responsable = request.form["responsable"]
        predio = request.form["predio"]
        marca = request.form["marca"]
        serie = request.form["serie"]
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
        UPDATE activos
        SET codigo = ?, nombre = ?, ubicacion = ?, estado = ?, responsable = ?, predio = ?, marca = ?, serie = ?, fecha_actualizacion = ?
        WHERE id = ?
        """, (codigo, nombre, ubicacion, estado, responsable, predio, marca, serie, fecha, id))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    # Obtener los datos del activo para editar
    cursor.execute("SELECT * FROM activos WHERE id = ?", (id,))
    activo = cursor.fetchone()
    conn.close()

    return render_template("editar.html", activo=activo)

# Eliminar un activo con autorización
@app.route("/eliminar/<int:id>", methods=["GET", "POST"])
def eliminar_activo(id):
    if request.method == "POST":
        # Verificar el código de autorización
        codigo_autorizacion = request.form.get("codigo_autorizacion")
        if codigo_autorizacion != AUTHORIZED_CODE:
            return render_template("eliminar.html", id=id, error="Código de autorización incorrecto.")

        # Eliminar el activo
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM activos WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for("index"))


    return render_template("eliminar.html", id=id)

@app.route("/generar_qr/<int:id>")
def generar_qr_activo(id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo, nombre FROM activos WHERE id = ?", (id,))
    activo = cursor.fetchone()
    conn.close()

    if activo:
        codigo, nombre = activo
        generar_codigo_qr(codigo, nombre)
        return redirect(url_for("ver_activo", id=id))
    else:
        return "Activo no encontrado", 404

def generar_codigo_qr(codigo, nombre):
    
    qr_folder = "static/qr-codes"
    if not os.path.exists(qr_folder):
        os.makedirs(qr_folder)

    # Contenido del código QR: enlace a la página del activo
    url_base = "https://activos.onrender.com"  # Cambiado para red local
    contenido = f"{url_base}/activo/{codigo}"

    # Generar QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(contenido)
    qr.make(fit=True)

    # Guardar imagen
    img = qr.make_image(fill_color="black", back_color="white")
    qr_path = os.path.join(qr_folder, f"{codigo}.png")
    img.save(qr_path)
    print(f"Código QR generado: {qr_path} -> {contenido}")

@app.route("/exportar_excel")
def exportar_excel():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activos")
    data = cursor.fetchall()
    conn.close()

    columnas = ["ID", "Código", "Nombre", "Ubicación", "Estado", "Responsable", "Fecha Actualización", "Predio", "Marca", "Serie"]
    df = pd.DataFrame(data, columns=columnas)

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
    