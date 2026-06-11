import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def print_arulfo():
    conn = mysql.connector.connect( host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_DATABASE") )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT persona_id, codigo, nombre, apellidos FROM personas WHERE nombre LIKE '%ARULFO%'")
    for r in cursor.fetchall():
        print(f"ID: {r['persona_id']}, Code: {r['codigo']}, Name: {r['nombre']} {r['apellidos']}")
    conn.close()

if __name__ == "__main__":
    print_arulfo()
