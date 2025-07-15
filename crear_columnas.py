import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect("postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db")
cur = conn.cursor()

# Crear tabla si no existe
cur.execute("""
CREATE TABLE IF NOT EXISTS desechos (
    id SERIAL PRIMARY KEY,
    id_activo INTEGER,
    codigo VARCHAR,
    nombre VARCHAR,
    fecha_desecho TIMESTAMP,
    usuario_desecha VARCHAR
);
""")

# Agregar columnas faltantes (solo si no existen)
cur.execute("ALTER TABLE desechos ADD COLUMN IF NOT EXISTS ubicacion VARCHAR;")
cur.execute("ALTER TABLE desechos ADD COLUMN IF NOT EXISTS predio VARCHAR;")
cur.execute("ALTER TABLE desechos ADD COLUMN IF NOT EXISTS marca VARCHAR;")
cur.execute("ALTER TABLE desechos ADD COLUMN IF NOT EXISTS serie VARCHAR;")

conn.commit()
cur.close()
conn.close()

print("✅ Tabla 'desechos' verificada y columnas aseguradas.")