import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def search_arulfo():
    try:
        conn = mysql.connector.connect( host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_DATABASE") )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT persona_id, codigo, nombre, apellidos FROM personas WHERE nombre LIKE '%ARULFO%'")
        for r in cursor.fetchall(): print(r)
        conn.close()
    except Exception as e: print(e)

if __name__ == "__main__":
    search_arulfo()
