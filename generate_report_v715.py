import os
import pandas as pd
from app import AgenteComparativa
from dotenv import load_dotenv

load_dotenv()

def generate_discrepancy_report_v715(finca_id=724, desde="2024-02-18", hasta="2024-02-19"):
    """
    Genera un informe de discrepancias para la versión V_715 (Polinización).
    Por defecto usa la Finca 724 (Palmar de Altamira).
    """
    agente = AgenteComparativa()
    
    print(f"Generando comparativa V_715 para Finca {finca_id} ({desde} al {hasta})...")
    comp = agente.generar_comparativa(finca_id, desde, hasta, version='v715')
    
    output_md = f"informe_discrepancias_v715_finca{finca_id}.md"
    
    if comp.empty:
        with open(output_md, "w", encoding='utf-8') as f:
            f.write(f"# Informe de Discrepancias V_715\nNo hay datos para informar en el rango {desde} a {hasta}.")
        print(f"No se encontraron datos. Se generó un informe vacío: {output_md}")
        return

    # Filtrar solo discrepancias
    disc = comp[comp['estado'] != 'OK'].copy()
    
    md = f"# Informe de Discrepancias SIOMA (V_715)\n\n"
    md += f"**Finca ID:** {finca_id} (PALMAR DE ALTAMIRA)  \n"
    md += f"**Rango de consulta:** {desde} al {hasta}  \n"
    md += f"**Fecha del Informe:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n"
    
    md += "### Resumen Ejecutivo\n"
    md += f"- Total de registros analizados: {len(comp)}\n"
    md += f"- Registros OK: {len(comp[comp['estado'] == 'OK'])}\n"
    md += f"- Discrepancias totales: {len(disc)}\n\n"
    
    md += "| Operario | Lote | Labor | Analisis V_715 (I-F) | Mapa (I-F) | Estado |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for _, row in disc.iterrows():
        v_i = row.get('v715_linea_i', '-')
        v_f = row.get('v715_linea_f', '-')
        m_i = row.get('mapa_linea_i', '-')
        m_f = row.get('mapa_linea_f', '-')
        
        # Formatear nulos
        v_i = '-' if pd.isna(v_i) else int(v_i)
        v_f = '-' if pd.isna(v_f) else int(v_f)
        m_i = '-' if pd.isna(m_i) else int(m_i)
        m_f = '-' if pd.isna(m_f) else int(m_f)
        
        md += f"| {row['PERSONA']} | {row['LOTE']} | {row['labor_nombre']} | {v_i} - {v_f} | {m_i} - {m_f} | {row['estado']} |\n"
    
    with open(output_md, "w", encoding='utf-8') as f:
        f.write(md)
        
    # Guardar también en CSV para análisis profundo
    output_csv = f"reporte_v715_finca{finca_id}_{desde}.csv"
    comp.to_csv(output_csv, sep=';', index=False, encoding='utf-8-sig')
    
    print(f"Informe generado con éxito:")
    print(f"- Markdown: {output_md}")
    print(f"- CSV: {output_csv}")

if __name__ == "__main__":
    # Puedes cambiar los parámetros aquí o por línea de comandos si lo adaptamos
    import sys
    f_id = 724
    d = "2024-04-15" # Fecha de ejemplo para probar
    h = "2024-04-15"
    
    if len(sys.argv) > 1:
        f_id = int(sys.argv[1])
    if len(sys.argv) > 2:
        d = sys.argv[2]
    if len(sys.argv) > 3:
        h = sys.argv[3]
        
    generate_discrepancy_report_v715(f_id, d, h)
