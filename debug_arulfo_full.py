import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def find_missing_arulfo_all():
    try:
        conn = mysql.connector.connect( host=os.getenv("DB_HOST"), user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"), database=os.getenv("DB_DATABASE") )
        cursor = conn.cursor(dictionary=True)
        l_id = 28376; p_id = 203333; date = '2026-02-26'
        cursor.execute(f"""
            SELECT s.linea, count(*) as pts 
            FROM l_pal_artils l
            LEFT JOIN labors_plans_plantas_new lpp ON lpp.tabla_labor_id = l.l_pal_artil_id AND lpp.labor_id = 359
            LEFT JOIN plantas p ON lpp.planta_id = p.planta_id
            LEFT JOIN spots s ON p.spot_id = s.spot_id
            WHERE l.persona_id = {p_id} AND l.lote_id = {l_id} AND l.fecha BETWEEN '{date} 00:00:00' AND '{date} 23:59:59'
            GROUP BY s.linea
            ORDER BY cast(s.linea as UNSIGNED)
        """)
        rows = cursor.fetchall()
        for r in rows: print(f"{r['linea']}: {r['pts']}")
        conn.close()
    except Exception as e: print(e)

if __name__ == "__main__":
    find_missing_arulfo_all()
