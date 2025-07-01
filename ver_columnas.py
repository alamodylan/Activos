import psycopg2
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://citasatm_user:SlwK1sFIPJal7m8KaDtlRlYu1NseKxnV@dpg-ctdis2jv2p9s73ai7op0-a.oregon-postgres.render.com/citasatm_db")

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Consultar la estructura de la tabla activos
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'activos';
""")

columnas = cur.fetchall()
for columna in columnas:
    print(columna)

cur.close()
conn.close()