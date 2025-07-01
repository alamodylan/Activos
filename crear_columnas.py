import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect("postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db")
cur = conn.cursor()

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

conn.commit()
cur.close()
conn.close()

print("✅ Tabla 'desechos' creada (si no existía).")