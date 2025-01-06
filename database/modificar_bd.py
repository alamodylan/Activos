import sqlite3

# Conexión a la base de datos
conn = sqlite3.connect("database/activos.db")
cursor = conn.cursor()

# Modificar la tabla 'activos' para incluir las nuevas columnas
try:
    cursor.execute("ALTER TABLE activos ADD COLUMN predio TEXT DEFAULT ''")
    cursor.execute("ALTER TABLE activos ADD COLUMN marca TEXT DEFAULT ''")
    cursor.execute("ALTER TABLE activos ADD COLUMN serie TEXT DEFAULT ''")
    print("Las columnas 'predio', 'marca' y 'serie' se agregaron correctamente.")
except sqlite3.OperationalError as e:
    print(f"Error al modificar la base de datos: {e}")

# Confirmar cambios y cerrar conexión
conn.commit()
conn.close()