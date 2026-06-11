import os
import pandas as pd
from app import AgenteComparativa
from dotenv import load_dotenv

load_dotenv()

def generate_discrepancy_report(finca_id, desde, hasta):
    agente = AgenteComparativa()
    
    comp = agente.generar_comparativa(finca_id, desde, hasta)
    
    if comp.empty:
        with open("informe_discrepancias.md", "w") as f:
            f.write("# Informe de Discrepancias\nNo hay datos para informar.")
        return

    disc = comp[comp['estado'] != 'OK'].copy()
    
    md = f"# Informe de Discrepancias SIOMA\n\n"
    md += f"**Finca ID:** {finca_id}  \n"
    md += f"**Rango:** {desde} al {hasta}  \n"
    md += f"**Fecha del Informe:** {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n"
    
    md += "### Resumen Ejecutivo\n"
    md += f"- Total de registros analizados: {len(comp)}\n"
    md += f"- Registros OK: {len(comp[comp['estado'] == 'OK'])}\n"
    md += f"- Discrepancias totales: {len(disc)}\n\n"
    
    md += "| Operario | Lote | Labor | Analisis (L-I/L-F) | Mapa (L-I/L-F) | Estado |\n"
    md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for _, row in disc.iterrows():
        l_nombre = row.get('labor_nombre', f"Labor {row['labor_id']}")
        v_i = row.get('v545_linea_i', '-')
        v_f = row.get('v545_linea_f', '-')
        m_i = row.get('mapa_linea_i', '-')
        m_f = row.get('mapa_linea_f', '-')
        
        # Handle None/NaN for display
        v_i = '-' if pd.isna(v_i) else int(v_i)
        v_f = '-' if pd.isna(v_f) else int(v_f)
        m_i = '-' if pd.isna(m_i) else int(m_i)
        m_f = '-' if pd.isna(m_f) else int(m_f)
        
        md += f"| {row['PERSONA']} | {row['LOTE']} | {l_nombre} | {v_i} - {v_f} | {m_i} - {m_f} | {row['estado']} |\n"
    
    with open("informe_discrepancias.md", "w", encoding='utf-8') as f:
        f.write(md)
    print("Informe generado: informe_discrepancias.md")

if __name__ == "__main__":
    generate_discrepancy_report(427, "2026-02-26", "2026-02-26")
