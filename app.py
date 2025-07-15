from flask import Flask, render_template, request, redirect, url_for, send_file, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import qrcode
import pandas as pd
from io import BytesIO
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

CLAVE_DESECHO = "atm2406"
CLAVE = "atm2406"
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "atm2406")
# Configuración de la base de datos PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db")
AUTHORIZED_CODE = "atm2406"  # Código de autorización para modificar y eliminar

# Función para conectar a la base de datos
def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Error al conectar con la base de datos: {e}")
        raise

def crear_tabla_bitacora_entregas():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_entregas (
            id SERIAL PRIMARY KEY,
            id_activo INTEGER REFERENCES activos(id),
            persona_recibe TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'pendiente',
            persona_envia TEXT NOT NULL,
            departamento_envia TEXT NOT NULL,
            predio_destino TEXT NOT NULL,
            boleta_firmada BOOLEAN DEFAULT FALSE
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Tabla 'entregas' verificada o creada correctamente.")
def eliminar_tabla_entregas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS entregas;")
    conn.commit()
    cursor.close()
    conn.close()

def crear_tabla_desechos():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS desechos (
            id SERIAL PRIMARY KEY,
            id_activo INTEGER REFERENCES activos(id),
            fecha_desecho TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario_desecha TEXT NOT NULL
        );
    """)

    conn.commit()
    cursor.close()
    conn.close()


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
        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        ubicacion = request.form["ubicacion"]
        estado = request.form["estado"]
        responsable = request.form["responsable"]
        predio = request.form["predio"]
        marca = request.form["marca"]
        serie = request.form["serie"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activos (codigo, nombre, ubicacion, estado, responsable, fecha_actualizacion, predio, marca, serie)
            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s)
            RETURNING id
        """, (codigo, nombre, ubicacion, estado, responsable, predio, marca, serie))

        nuevo_id = cursor.fetchone()["id"]  # ✅ Obtener el ID del nuevo activo
        conn.commit()
        conn.close()

        generar_qr_activo(nuevo_id)  # ✅ Usar el ID real

        return redirect(url_for("index"))
    
    return render_template("registrar.html")


@app.route("/generar_qr/<int:id>")
def generar_qr_activo(id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT codigo FROM activos WHERE id = %s", (id,))
    activo = cursor.fetchone()
    conn.close()

    if not activo:
        return "Activo no encontrado", 404

    codigo = activo["codigo"]

    # Carpeta donde se guardarán los QR
    qr_folder = "static/QR-Codes"
    if not os.path.exists(qr_folder):
        os.makedirs(qr_folder)

    # ✅ URL única para cada activo (URL real de tu app)
    url_base = "https://activos.onrender.com/activo"
    contenido_qr = f"{url_base}/{id}"

    # Generar QR
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(contenido_qr)
    qr.make(fit=True)

    # Guardar la imagen del QR
    qr_path = os.path.join(qr_folder, f"{codigo}.png")
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_path)

    return redirect(url_for('ver_activo', id=id))

@app.route("/activo/<int:id>")
def ver_activo(id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)  # Esto hace que retorne un diccionario
    cursor.execute("SELECT * FROM activos WHERE id = %s", (id,))
    activo = cursor.fetchone()
    conn.close()

    if not activo:
        return "Activo no encontrado", 404

    return render_template("activo.html", activo=activo)
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_activo(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        codigo_autorizacion = request.form.get("codigo_autorizacion")
       

        codigo = request.form["codigo"]
        nombre = request.form["nombre"]
        ubicacion = request.form["ubicacion"]
        estado = request.form["estado"]
        responsable = request.form["responsable"]
        predio = request.form["predio"]
        marca = request.form["marca"]
        serie = request.form["serie"]
        fecha = datetime.now()

        cursor.execute("""
        UPDATE activos
        SET codigo = %s, nombre = %s, ubicacion = %s, estado = %s, responsable = %s, predio = %s, marca = %s, serie = %s, fecha_actualizacion = %s
        WHERE id = %s
        """, (codigo, nombre, ubicacion, estado, responsable, predio, marca, serie, fecha, id))

        conn.commit()
        conn.close()
        return redirect(url_for("index"))

    cursor.execute("SELECT * FROM activos WHERE id = %s", (id,))
    activo = cursor.fetchone()
    conn.close()

    return render_template("editar.html", activo=activo)
@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar_activo(id):
    codigo = request.form.get("codigo_confirmacion", "")

    if codigo != "atm2406":
        print("❌ Código de autorización incorrecto. Eliminación cancelada.")
        return redirect(url_for("index"))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM activos WHERE id = %s", (id,))
        conn.commit()
        print(f"✅ Activo con ID {id} eliminado correctamente.")
    except Exception as e:
        print(f"❌ Error al eliminar activo: {e}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("index"))

# Exportar activos a Excel
@app.route("/exportar_excel")
def exportar_excel():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM activos")
    data = cursor.fetchall()
    conn.close()

    # Verifica que hay datos antes de intentar crear el DataFrame
    if not data:
        return "No hay datos para exportar.", 404

    # Extraer nombres de columnas de la consulta
    columnas = list(data[0].keys())

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
@app.route('/desechar/<int:id>', methods=['POST'])
def desechar_activo(id):
    clave = request.form.get('clave')
    usuario_desecha = request.form.get('usuario_desecha')

    if clave != CLAVE_DESECHO:
        flash('❌ Clave incorrecta para desechar.', 'danger')
        return redirect(url_for('index'))

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Traer todos los campos que vamos a necesitar para insertarlos en la tabla de desechos
        cur.execute("""
            SELECT id, codigo, nombre, ubicacion, predio, marca, serie 
            FROM activos 
            WHERE id = %s
        """, (id,))
        activo = cur.fetchone()

        if activo:
            print(f"✅ Desechando activo: {activo[1]}")

            # Insertar todos los datos en desechos
            cur.execute("""
                INSERT INTO desechos (
                    id_activo, codigo, nombre, ubicacion, predio, marca, serie,
                    fecha_desecho, usuario_desecha
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """, (
                activo[0], activo[1], activo[2], activo[3], activo[4],
                activo[5], activo[6], usuario_desecha
            ))

            # Eliminar de activos
            cur.execute("DELETE FROM activos WHERE id = %s", (id,))
            conn.commit()

            flash('✅ Activo desechado correctamente.', 'success')
        else:
            flash('❌ Activo no encontrado.', 'danger')

    except Exception as e:
        conn.rollback()
        flash(f"⚠️ Error al desechar: {e}", "danger")
    finally:
        cur.close()
        conn.close()

    return redirect(url_for('index'))

@app.route('/ver_desechos')
def ver_desechos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT codigo, nombre, ubicacion, predio, marca, serie, usuario_desecha, fecha_desecho
        FROM desechos
        ORDER BY fecha_desecho DESC;
    """)
    desechados = [dict(zip([desc[0] for desc in cursor.description], row)) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return render_template('desechos.html', desechados=desechados)

@app.route('/generar_acta_desecho', methods=['POST'])
def generar_acta_desecho():
    fecha = request.form.get('fecha')

    # Buscar los activos desechados en esa fecha
    conn = get_db_connection()  # cambia por tu DB si es necesario
    c = conn.cursor()
    c.execute("""
        SELECT id_activo, codigo, nombre, fecha_desecho, usuario_desecha
        FROM desechos
        WHERE fecha_desecho = %s
    """, (fecha,))
    desechos = c.fetchall()
    conn.close()

    if not desechos:
        flash("⚠️ No hay activos desechados en esa fecha.", "warning")
        return redirect(url_for('ver_desechos'))

    # Crear PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Agregar logo
    logo_path = os.path.join(app.root_path, 'static', 'LogoAlamo', 'logo.png')
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 40, height - 80, width=120, preserveAspectRatio=True, mask='auto')

    # Título y fecha
    c.setFont("Helvetica-Bold", 14)
    c.drawString(200, height - 50, "ACTA DE DESECHO DE ACTIVOS")
    c.setFont("Helvetica", 10)
    c.drawString(40, height - 100, f"Fecha del desecho: {fecha}")

    # Encabezados tabla
    y = height - 140
    c.setFont("Helvetica-Bold", 10)
    c.drawString(40, y, "Código")
    c.drawString(150, y, "Nombre")
    c.drawString(400, y, "Desechado por")

    # Cuerpo tabla
    c.setFont("Helvetica", 10)
    y -= 20
    for item in desechos:
        if y < 100:
            c.showPage()
            y = height - 100
        c.drawString(40, y, str(item[1]))  # Código
        c.drawString(150, y, str(item[2]))  # Nombre
        c.drawString(400, y, str(item[4]))  # Usuario
        y -= 20

    # Firmas
    y -= 40
    c.drawString(40, y, "____________________________")
    c.drawString(300, y, "____________________________")
    c.drawString(40, y - 15, "Firma de quien desecha")
    c.drawString(300, y - 15, "Firma del inspector")

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"acta_desecho_{fecha}.pdf",
                     mimetype='application/pdf')

crear_tablas()  # Activos
crear_tabla_desechos()  # Desechados
crear_tabla_bitacora_entregas()  # Bitácora de entregas
if __name__ == "__main__":
    crear_tablas()
    app.run(host="0.0.0.0", port=8000, debug=True)
    