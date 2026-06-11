import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def find_table():
    try:
        conn = mysql.connector.connect( host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_DATABASE") )
        cursor = conn.cursor(dictionary=True)
        l_id = 28376; p_id = 204475; date = '2026-02-26'
        tables = [('l_pal_artils', 359), ('l_pal_artlis', 360), ('l_pal_asisms', 361), ('l_pal_antess', 171), ('l_pal_artifs', 172)]
        for t, lab_id in tables:
            cursor.execute(f"SELECT s.linea FROM {t} l LEFT JOIN labors_plans_plantas_new lpp ON lpp.tabla_labor_id = l.{t[:-1]}_id AND lpp.labor_id = {lab_id} LEFT JOIN plantas p ON lpp.planta_id = p.planta_id LEFT JOIN spots s ON p.spot_id = s.spot_id WHERE l.persona_id = {p_id} AND l.lote_id = {l_id} AND l.fecha BETWEEN '{date} 00:00:00' AND '{date} 23:59:59' GROUP BY s.linea")
            results = [r['linea'] for r in cursor.fetchall() if r['linea'] is not None]
            if results:
                print(f"Found in {t}: {sorted([int(r) for r in results])}")
        conn.close()
    except Exception as e: print(e)

if __name__ == "__main__":
    find_table()
