import os
import sys
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from app import AgenteComparativa

def main():
    load_dotenv()
    
    if len(sys.argv) < 4:
        print("Error: Faltan argumentos.")
        print("Uso: python comparativa.py <finca_id> <desde> <hasta> [version]")
        print("Ejemplo: python comparativa.py 427 2024-06-10 2024-06-10")
        sys.exit(1)
        
    try:
        finca_id = int(sys.argv[1])
    except ValueError:
        print("Error: El ID de la finca debe ser un número entero.")
        sys.exit(1)
        
    desde = sys.argv[2]
    hasta = sys.argv[3]
    version = sys.argv[4] if len(sys.argv) > 4 else 'v545'
    
    if version not in ['v545', 'v715']:
        print("Error: La versión debe ser 'v545' o 'v715'.")
        sys.exit(1)
        
    print(f"Iniciando comparativa (versión {version}) para la finca {finca_id} desde {desde} hasta {hasta}...")
    
    agente = AgenteComparativa()
    try:
        comp = agente.generar_comparativa(finca_id, desde, hasta, version=version)
    except Exception as e:
        print(f"Error al generar la comparativa: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    if comp.empty:
        print("No se encontraron registros para el rango de fechas e ID de finca especificados.")
        sys.exit(0)
        
    total_registros = len(comp)
    registros_ok = len(comp[comp['estado'] == 'OK'])
    discrepancias = comp[comp['estado'] != 'OK']
    total_discrepancias = len(discrepancias)
    
    print("\n" + "="*50)
    print("RESUMEN DE COMPARACIÓN")
    print("="*50)
    print(f"Total registros analizados: {total_registros}")
    print(f"Registros OK: {registros_ok}")
    print(f"Registros con discrepancia: {total_discrepancias}")
    print("="*50 + "\n")
    
    v_prefix = 'v715' if version == 'v715' else 'v545'
    v_col_i = f'{v_prefix}_linea_i'
    v_col_f = f'{v_prefix}_linea_f'
    
    if total_discrepancias > 0:
        print("DISCREPANCIAS ENCONTRADAS:")
        # Formatear salida para consola
        display_cols = ['fecha', 'PERSONA', 'LOTE', 'labor_nombre', v_col_i, v_col_f, 'mapa_linea_i', 'mapa_linea_f', 'estado']
        df_print = discrepancias[display_cols].copy()
        
        # Intentar usar tabulate si está instalado para que quede bonito
        try:
            from tabulate import tabulate
            print(tabulate(df_print, headers='keys', tablefmt='grid', showindex=False))
        except ImportError:
            # Fallback a pandas print
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            print(df_print.to_string(index=False))
    else:
        print("¡Todo OK! No se encontraron discrepancias.")
        
    # Generar el archivo CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"reporte_comparativa_{finca_id}_{timestamp}.csv"
    
    # Renombrar columnas para que coincida con el reporte detallado
    reporte_csv = comp.copy()
    cols_to_use = ['fecha', 'PERSONA', 'FUNC', 'LOTE', 'labor_nombre', v_col_i, v_col_f, 'mapa_linea_i', 'mapa_linea_f', 'estado']
    reporte_csv = reporte_csv[cols_to_use]
    reporte_csv.columns = [
        'Fecha', 'Operario', 'Codigo', 'Lote', 'Labor', 
        f'Analisis_Inicio_{version}', f'Analisis_Fin_{version}', 
        'Mapa_Inicio', 'Mapa_Fin', 'Estado'
    ]
    
    try:
        reporte_csv.to_csv(csv_filename, index=False, sep=';', encoding='utf-8-sig')
        print(f"\nReporte detallado CSV guardado en: {csv_filename}")
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")

if __name__ == "__main__":
    main()
