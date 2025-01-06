import sqlite3
import os

# Crear la carpeta 'database/' si no existe
if not os.path.exists("database"):
    os.makedirs("database")

# Conexión a la base de datos
try:
    conn = sqlite3.connect("database/activos.db")
    cursor = conn.cursor()

    # Crear tabla o actualizarla
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        ubicacion TEXT NOT NULL,
        estado TEXT NOT NULL,
        responsable TEXT,
        predio TEXT DEFAULT '',
        marca TEXT DEFAULT '',
        serie TEXT DEFAULT '',
        fecha_actualizacion TEXT NOT NULL
    );
    """)

    # Verificar y agregar columnas si faltan
    columns_to_add = [
        ("predio", "TEXT DEFAULT ''"),
        ("marca", "TEXT DEFAULT ''"),
        ("serie", "TEXT DEFAULT ''")
    ]

    for column, definition in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE activos ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError:
            print(f"La columna '{column}' ya existe. No se realizaron cambios.")

    # Confirmar cambios y cerrar conexión
    conn.commit()
    conn.close()
    print("Base de datos y tabla creadas o actualizadas correctamente.")
except sqlite3.Error as e:
    print(f"Error al crear o actualizar la base de datos: {e}")