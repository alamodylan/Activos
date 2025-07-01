import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Añadir las columnas solo si no existen
try:
    cur.execute("ALTER TABLE activos ADD COLUMN fecha_desecho DATE;")
    print("✅ Columna fecha_desecho agregada.")
except psycopg2.errors.DuplicateColumn:
    print("ℹ️ La columna fecha_desecho ya existía.")
    conn.rollback()

try:
    cur.execute("ALTER TABLE activos ADD COLUMN usuario_desecha VARCHAR;")
    print("✅ Columna usuario_desecha agregada.")
except psycopg2.errors.DuplicateColumn:
    print("ℹ️ La columna usuario_desecha ya existía.")
    conn.rollback()

conn.commit()
cur.close()
conn.close()