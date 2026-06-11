import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def check_cierre():
    try:
        conn = mysql.connector.connect( host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_DATABASE") )
        cursor = conn.cursor(dictionary=True)
        p_id = 204475
        date = '2026-02-26'
        cursor.execute("SELECT lote_id, labor_id, tajos FROM cierre_area_labor_dia_personas WHERE persona_id = %s AND fecha = %s", (p_id, date))
        for r in cursor.fetchall(): print(r)
        conn.close()
    except Exception as e: print(e)

if __name__ == "__main__":
    check_cierre()
