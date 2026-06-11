import os
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

class AgenteComparativa:
    def __init__(self):
        self.db_config = {
            'host': os.getenv("DB_HOST"),
            'user': os.getenv("DB_USER"),
            'password': os.getenv("DB_PASSWORD"),
            'database': os.getenv("DB_DATABASE")
        }
    
    def get_db_connection(self):
        return mysql.connector.connect(**self.db_config)

    def obtener_nombres_labores(self):
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT labor_id, nombre FROM labors")
        rows = cursor.fetchall()
        conn.close()
        return {row['labor_id']: row['nombre'] for row in rows}

    def obtener_poligonos(self, finca_id):
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Obtener lotes de la finca
        cursor.execute("SELECT lote_id, nombre FROM lotes WHERE finca_id = %s", (finca_id,))
        lotes = {row['lote_id']: row['nombre'] for row in cursor.fetchall()}
        
        if not lotes:
            conn.close()
            return []
            
        # Obtener puntos de los lotes
        lote_ids = tuple(lotes.keys())
        query = f"SELECT lote_id, lat, lng FROM puntos_lotes WHERE lote_id IN ({','.join(['%s']*len(lote_ids))}) ORDER BY lote_id, punto_lote_id"
        cursor.execute(query, lote_ids)
        rows = cursor.fetchall()
        conn.close()
        
        # Agrupar por lote
        poligonos = {}
        for row in rows:
            lid = row['lote_id']
            if lid not in poligonos:
                poligonos[lid] = {'nombre': lotes[lid], 'puntos': []}
            poligonos[lid]['puntos'].append([float(row['lat']), float(row['lng'])])
            
        return list(poligonos.values())

    def obtener_spots_finca(self, finca_id):
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT linea, lat, lng FROM spots WHERE finca_id = %s", (finca_id,))
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            r['lat'] = float(r['lat'])
            r['lng'] = float(r['lng'])
        return rows

    def obtener_lotes_activos_persona(self, finca_id, persona_id, fecha):
        if not persona_id or not fecha:
            return None
            
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        lote_ids = set()
        
        # 1. Buscar en cierre_area_labor_dia_personas
        query_cierre = """
            SELECT DISTINCT lote_id FROM cierre_area_labor_dia_personas 
            WHERE finca_id = %s AND persona_id = %s AND fecha = %s
        """
        try:
            cursor.execute(query_cierre, (finca_id, persona_id, fecha))
            for r in cursor.fetchall():
                if r[0]: lote_ids.add(int(r[0]))
        except Exception as e:
            print(f"Error query lotes cierre: {e}")
            
        # 2. Buscar en las tablas de labores
        tablas_labores = [
            'l_pal_artils', 'l_pal_artlis', 'l_pal_asisms', 'l_pal_antess', 'l_pal_artifs', 'l_pal_polins'
        ]
        for t in tablas_labores:
            try:
                query_labor = f"""
                    SELECT DISTINCT lote_id FROM {t}
                    WHERE finca_id = %s AND persona_id = %s AND fecha BETWEEN %s AND %s
                """
                cursor.execute(query_labor, (finca_id, persona_id, f"{fecha} 00:00:00", f"{fecha} 23:59:59"))
                for r in cursor.fetchall():
                    if r[0]: lote_ids.add(int(r[0]))
            except:
                pass
                
        conn.close()
        return list(lote_ids)

    def obtener_poligonos_filtrados(self, finca_id, persona_id=None, fecha=None):
        lote_ids = self.obtener_lotes_activos_persona(finca_id, persona_id, fecha)
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if lote_ids is not None:
            if not lote_ids: 
                conn.close()
                return []
            lote_ids_str = ",".join([str(lid) for lid in lote_ids])
            cursor.execute(f"SELECT lote_id, nombre FROM lotes WHERE finca_id = %s AND lote_id IN ({lote_ids_str})", (finca_id,))
        else:
            cursor.execute("SELECT lote_id, nombre FROM lotes WHERE finca_id = %s", (finca_id,))
            
        lotes = {row['lote_id']: row['nombre'] for row in cursor.fetchall()}
        
        if not lotes:
            conn.close()
            return []
            
        lote_ids_keys = tuple(lotes.keys())
        query = f"SELECT lote_id, lat, lng FROM puntos_lotes WHERE lote_id IN ({','.join(['%s']*len(lote_ids_keys))}) ORDER BY lote_id, punto_lote_id"
        cursor.execute(query, lote_ids_keys)
        rows = cursor.fetchall()
        conn.close()
        
        poligonos = {}
        for row in rows:
            lid = row['lote_id']
            if lid not in poligonos:
                poligonos[lid] = {'nombre': lotes[lid], 'puntos': []}
            poligonos[lid]['puntos'].append([float(row['lat']), float(row['lng'])])
            
        return list(poligonos.values())

    def obtener_spots_filtrados(self, finca_id, persona_id=None, fecha=None):
        lote_ids = self.obtener_lotes_activos_persona(finca_id, persona_id, fecha)
        
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if lote_ids is not None:
            if not lote_ids:
                conn.close()
                return []
            lote_ids_str = ",".join([str(lid) for lid in lote_ids])
            cursor.execute(f"SELECT lote_id, linea, lat, lng, posicion, poligono FROM spots WHERE finca_id = %s AND lote_id IN ({lote_ids_str}) ORDER BY lote_id, linea, posicion", (finca_id,))
        else:
            cursor.execute("SELECT lote_id, linea, lat, lng, posicion, poligono FROM spots WHERE finca_id = %s ORDER BY lote_id, linea, posicion", (finca_id,))
            
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            r['lat'] = float(r['lat'])
            r['lng'] = float(r['lng'])
            r['posicion'] = int(r['posicion']) if r['posicion'] is not None else 0
            if r.get('poligono'):
                try:
                    if isinstance(r['poligono'], str):
                        r['poligono'] = json.loads(r['poligono'])
                    elif isinstance(r['poligono'], bytes):
                        r['poligono'] = json.loads(r['poligono'].decode('utf-8'))
                except:
                    r['poligono'] = None
        return rows

    def obtener_coordenadas(self, finca_id, persona_id, fecha):
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = f"SELECT lat AS latitud, lng AS longitud, fecha FROM coordenadas_{finca_id} WHERE persona_id = %s AND fecha BETWEEN %s AND %s ORDER BY fecha"
        try:
            cursor.execute(query, (persona_id, f"{fecha} 00:00:00", f"{fecha} 23:59:59"))
            rows = cursor.fetchall()
            for row in rows:
                if isinstance(row['fecha'], datetime):
                    row['fecha'] = row['fecha'].strftime('%Y-%m-%d %H:%M:%S')
                row['latitud'] = float(row['latitud']) if row['latitud'] else 0.0
                row['longitud'] = float(row['longitud']) if row['longitud'] else 0.0
        except Exception as e:
            print(f"Error query coordenadas: {e}")
            rows = []
        conn.close()
        return rows

    def obtener_puntos_labores(self, finca_id, persona_id, fecha, version='v545'):
        if version == 'v715':
            tablas = ['l_pal_polins']
        else:
            tablas = ['l_pal_artils', 'l_pal_artlis', 'l_pal_asisms', 'l_pal_antess', 'l_pal_artifs']
            
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        puntos = []
        for t in tablas:
            query = f"""
                SELECT l.lat, l.lng, l.fecha, 
                       l.tipo_labor_id, tl.nombre as labor_nombre
                FROM {t} l
                LEFT JOIN tipo_labors tl ON l.tipo_labor_id = tl.tipo_labor_id
                WHERE l.finca_id = %s AND l.persona_id = %s AND l.fecha BETWEEN %s AND %s
            """
            try:
                cursor.execute(query, (finca_id, persona_id, f"{fecha} 00:00:00", f"{fecha} 23:59:59"))
                rows = cursor.fetchall()
                for r in rows:
                    if r['lat'] is not None and r['lng'] is not None:
                        r['lat'] = float(r['lat'])
                        r['lng'] = float(r['lng'])
                        if isinstance(r['fecha'], datetime):
                            r['fecha'] = r['fecha'].strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            r['fecha'] = str(r['fecha']) if r['fecha'] else ""
                        r['labor_nombre'] = r['labor_nombre'] if r['labor_nombre'] else f"Tipo {r['tipo_labor_id']}"
                        puntos.append(r)
            except Exception as e:
                pass
                
        conn.close()
        return puntos

    def obtener_config_finca(self, finca_id):
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT linea_palma FROM fincas WHERE finca_id = %s", (finca_id,))
        row = cursor.fetchone()
        conn.close()
        default_config = {"cumplimiento": 0.25, "salto": 3, "maxLine": 1}
        if row and row['linea_palma']:
            try:
                config = json.loads(row['linea_palma'])
                # Asegurar tipos y valores por defecto si faltan claves
                return {
                    "cumplimiento": float(config.get("cumplimiento", 0.25)),
                    "salto": int(config.get("salto", 3)),
                    "maxLine": int(config.get("maxLine", 1))
                }
            except: pass
        return default_config

    def obtener_spots_totales(self, finca_id):
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT lote_id, cast(linea as UNSIGNED) as linea, count(*) as total 
            FROM spots 
            WHERE finca_id = %s 
            GROUP BY lote_id, linea
        """, (finca_id,))
        rows = cursor.fetchall()
        conn.close()
        return {(r['lote_id'], r['linea']): r['total'] for r in rows}

    def calcular_rangos(self, lineas, salto_permitido=3):
        if lineas is None or len(lineas) == 0: return []
        lineas = sorted([int(l) for l in lineas if l is not None])
        if len(lineas) == 0: return []
        
        rangos = []
        inicio = lineas[0]
        anterior = lineas[0]
        
        for i in range(1, len(lineas)):
            if lineas[i] - anterior > salto_permitido:
                rangos.append((inicio, anterior))
                inicio = lineas[i]
            anterior = lineas[i]
        rangos.append((inicio, anterior))
        return rangos

    def obtener_datos_gps_generico(self, finca_id, desde, hasta, tablas_labores):
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        subqueries = []
        params = []
        for tabla, labor_id in tablas_labores:
            id_col = f"{tabla[:-1]}_id" if tabla.endswith('s') else f"{tabla}_id"
            sub = f"""
                select l.finca_id, l.lote_id, cast(s.linea as UNSIGNED) as linea, l.persona_id, {labor_id} as labor_id,
                       date_format(l.fecha, '%Y-%m-%d') as DATA_STR,
                       count(*) as puntos_labor
                from {tabla} l
                left join labors_plans_plantas_new lpp on lpp.tabla_labor_id = l.{id_col} and lpp.labor_id = {labor_id}
                left join plantas p on lpp.planta_id = p.planta_id
                left join spots s on p.spot_id = s.spot_id
                where l.finca_id = %s and l.fecha between %s and %s
                group by l.finca_id, l.lote_id, s.linea, l.persona_id, DATA_STR
            """
            subqueries.append(sub)
            params.extend([finca_id, f"{desde} 00:00:00", f"{hasta} 23:59:59"])
            
        full_query = f"""
            SELECT d.finca_id, d.lote_id, l.nombre as LOTE, d.persona_id, p.codigo as FUNC,
                   concat(p.nombre, ' ', p.apellidos) as PERSONA, d.labor_id, d.DATA_STR, d.linea, d.puntos_labor
            FROM ( {" union all ".join(subqueries)} ) AS d
            inner join lotes l on d.lote_id = l.lote_id
            inner join personas p on d.persona_id = p.persona_id
        """
        cursor.execute(full_query, params)
        rows = cursor.fetchall()
        conn.close()
        return pd.DataFrame(rows)

    def obtener_datos_analisis_cierre(self, finca_id, desde, hasta, labor_ids, version_prefix):
        conn = self.get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        labor_ids_str = ",".join([str(lid) for lid in labor_ids])
        
        query = f"""
            SELECT c.lote_id, l.nombre as LOTE, c.persona_id, p.codigo as FUNC,
                   concat(p.nombre, ' ', p.apellidos) as PERSONA, c.labor_id, 
                   date_format(c.fecha, '%Y-%m-%d') as fecha, c.tajos,
                   cal.area_recorrida, cal.area_total
            FROM cierre_area_labor_dia_personas c
            INNER JOIN lotes l ON c.lote_id = l.lote_id
            INNER JOIN personas p ON c.persona_id = p.persona_id
            LEFT JOIN cierre_area_lotes cal ON cal.lote_id = c.lote_id 
                                           AND cal.persona_id = c.persona_id 
                                           AND cal.labor_id = c.labor_id 
                                           AND cal.fecha = c.fecha
            WHERE c.finca_id = %s AND c.labor_id IN ({labor_ids_str}) AND c.fecha BETWEEN %s AND %s
        """
        try:
            cursor.execute(query, (finca_id, f"{desde} 00:00:00", f"{hasta} 23:59:59"))
            rows = cursor.fetchall()
        except Exception as e:
            print(f"Error query cierre_area_labor_dia_personas: {e}")
            rows = []
        conn.close()
        
        if not rows:
            return pd.DataFrame()
            
        config = self.obtener_config_finca(finca_id)
        resultados = []
        
        for row in rows:
            tajos_str = row['tajos']
            if not tajos_str: continue
            try:
                tajos = json.loads(tajos_str)
            except:
                continue
                
            lineas = []
            for tajo in tajos:
                li = tajo.get('LI')
                lf = tajo.get('LF')
                if li is not None and lf is not None:
                    try:
                        lineas.extend(range(int(li), int(lf) + 1))
                    except:
                        pass
            
            lineas = sorted(list(set(lineas)))
            rangos = self.calcular_rangos(lineas, salto_permitido=config['salto'])
            
            for ri, rf in rangos:
                resultados.append({
                    'persona_id': row['persona_id'], 
                    'FUNC': row['FUNC'], 
                    'PERSONA': row['PERSONA'],
                    'lote_id': row['lote_id'], 
                    'LOTE': row['LOTE'], 
                    'labor_id': row['labor_id'],
                    'fecha': row['fecha'], 
                    f'{version_prefix}_linea_i': ri, 
                    f'{version_prefix}_linea_f': rf
                })
                
        return pd.DataFrame(resultados)

    def obtener_datos_v545(self, finca_id, desde, hasta):
        labor_ids = [359, 360, 361, 171, 172]
        return self.obtener_datos_analisis_cierre(finca_id, desde, hasta, labor_ids, 'v545')

    def obtener_datos_v715(self, finca_id, desde, hasta):
        labor_ids = [265, 267, 1]
        return self.obtener_datos_analisis_cierre(finca_id, desde, hasta, labor_ids, 'v715')


    def _procesar_datos_por_config(self, finca_id, df_base, version_col_name):
        if df_base.empty: return pd.DataFrame()
        config = self.obtener_config_finca(finca_id)
        spots_totales = self.obtener_spots_totales(finca_id)
        resultados = []
        for (p_id, l_id, lab_id, fecha_str), group in df_base.groupby(['persona_id', 'lote_id', 'labor_id', 'DATA_STR']):
            lineas_cumplidas = []
            for _, row in group.iterrows():
                if pd.isna(row['linea']) or pd.isna(row['lote_id']): continue
                total_linea = spots_totales.get((int(row['lote_id']), int(row['linea'])), 1)
                if (row['puntos_labor'] / total_linea) >= config['cumplimiento']:
                    lineas_cumplidas.append(int(row['linea']))
            rangos = self.calcular_rangos(lineas_cumplidas, salto_permitido=config['salto'])
            for ri, rf in rangos:
                resultados.append({
                    'persona_id': p_id, 'FUNC': group['FUNC'].iloc[0], 'PERSONA': group['PERSONA'].iloc[0],
                    'lote_id': l_id, 'LOTE': group['LOTE'].iloc[0], 'labor_id': lab_id,
                    'fecha': fecha_str, f'{version_col_name}_linea_i': ri, f'{version_col_name}_linea_f': rf
                })
        return pd.DataFrame(resultados)



    def obtener_datos_mapa(self, finca_id, desde, hasta, version='v545'):
        if version == 'v715':
            tablas_labores = [('l_pal_polins', 265), ('l_pal_polins', 267), ('l_pal_polins', 1)]
        else:
            tablas_labores = [
                ('l_pal_artils', 359), ('l_pal_artlis', 360), ('l_pal_asisms', 361),
                ('l_pal_antess', 171), ('l_pal_artifs', 172)
            ]
        df_base = self.obtener_datos_gps_generico(finca_id, desde, hasta, tablas_labores)
        if df_base.empty: return pd.DataFrame()
        return self._procesar_datos_por_config(finca_id, df_base, 'mapa')

    def generar_comparativa(self, finca_id, desde, hasta, version='v545'):
        if version == 'v715':
            df_analisis = self.obtener_datos_v715(finca_id, desde, hasta)
            v_prefix = 'v715'
        else:
            df_analisis = self.obtener_datos_v545(finca_id, desde, hasta)
            v_prefix = 'v545'
            
        df_mapa = self.obtener_datos_mapa(finca_id, desde, hasta, version=version)
        v_col_i = f'{v_prefix}_linea_i'
        v_col_f = f'{v_prefix}_linea_f'
        
        if df_analisis.empty and df_mapa.empty: return pd.DataFrame()
        
        if df_analisis.empty:
            comp = df_mapa.copy()
            comp[v_col_i] = None; comp[v_col_f] = None
        elif df_mapa.empty:
            comp = df_analisis.copy()
            comp['mapa_linea_i'] = None; comp['mapa_linea_f'] = None
        else:
            merge_keys = ['persona_id', 'lote_id', 'labor_id', 'fecha']
            df_analisis['temp_idx'] = df_analisis.groupby(merge_keys).cumcount()
            df_mapa['temp_idx'] = df_mapa.groupby(merge_keys).cumcount()
            
            comp = pd.merge(df_analisis, df_mapa, on=merge_keys + ['temp_idx'], how='outer', suffixes=('', '_mapa'))
            comp.drop(columns=['temp_idx'], inplace=True)
            
            for col in ['PERSONA', 'FUNC', 'LOTE']:
                if col + '_mapa' in comp.columns:
                    comp[col] = comp[col].fillna(comp[col + '_mapa'])
                    comp.drop(columns=[col + '_mapa'], inplace=True)

        comp['estado'] = 'OK'
        comp.loc[comp[v_col_i].isna(), 'estado'] = 'Sin Cierre'
        comp.loc[comp['mapa_linea_i'].isna(), 'estado'] = 'Solo en Analisis'
        
        mask_ambos = comp[v_col_i].notna() & comp['mapa_linea_i'].notna()
        mask_dif = (comp[v_col_i] != comp['mapa_linea_i']) | (comp[v_col_f] != comp['mapa_linea_f'])
        comp.loc[mask_ambos & mask_dif, 'estado'] = 'DISCREPANCIA'

        # Evaluar si la extensión de cualquiera de los rangos existentes es menor a 5 líneas
        mask_v_menor_5 = comp[v_col_i].notna() & ((comp[v_col_f] - comp[v_col_i] + 1) < 5)
        mask_m_menor_5 = comp['mapa_linea_i'].notna() & ((comp['mapa_linea_f'] - comp['mapa_linea_i'] + 1) < 5)
        comp.loc[mask_v_menor_5 | mask_m_menor_5, 'estado'] = 'Menos de 5 líneas'

        
        nombres_labores = self.obtener_nombres_labores()
        comp['labor_nombre'] = comp['labor_id'].map(
            lambda x: nombres_labores.get(int(x), f"Labor {x}") if not pd.isna(x) and str(x).isdigit() else f"Labor {x}"
        )
        comp.sort_values(by=['PERSONA', 'fecha'], inplace=True)
        return comp

agente = AgenteComparativa()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/comparar', methods=['POST'])
def comparar():
    datos = request.json
    finca_id = datos.get('finca_id')
    desde = datos.get('desde')
    hasta = datos.get('hasta')
    
    comparativa = agente.generar_comparativa(finca_id, desde, hasta)
    if comparativa.empty: return jsonify({'error': 'No hay datos'}), 404
    
    config = agente.obtener_config_finca(finca_id)
    
    conn = agente.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nombre FROM fincas WHERE finca_id = %s", (finca_id,))
    row = cursor.fetchone()
    conn.close()
    finca_nombre = row['nombre'] if row else f"Finca {finca_id}"
    
    return jsonify({
        'registros': comparativa.fillna('-').to_dict(orient='records'),
        'config': {
            'nombre': finca_nombre,
            'cumplimiento': int(config['cumplimiento'] * 100),
            'salto': config['salto']
        }
    })

@app.route('/descargar_reporte', methods=['GET'])
def descargar_reporte():
    try:
        from flask import make_response
        finca_id = request.args.get('finca_id')
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        
        if not finca_id or not desde or not hasta:
            return "Error: Faltan parámetros", 400
        
        comp = agente.generar_comparativa(finca_id, desde, hasta)
        if comp.empty:
            return "Error: No hay datos", 404
        
        reporte = comp[comp['estado'] != 'OK'].copy()
        if reporte.empty:
            return "Info: No hay discrepancias", 404
        
        cols = ['fecha', 'PERSONA', 'FUNC', 'LOTE', 'labor_nombre', 'v545_linea_i', 'v545_linea_f', 'mapa_linea_i', 'mapa_linea_f', 'estado']
        reporte = reporte[cols]
        reporte.columns = ['Fecha', 'Operario', 'Codigo', 'Lote', 'Labor', 'Analisis_Inicio', 'Analisis_Fin', 'Mapa_Inicio', 'Mapa_Fin', 'Estado']
        
        # Generar CSV con punto y coma
        csv_content = reporte.to_csv(index=False, sep=';', encoding='utf-8')
        
        # Inyectar BOM para Excel y crear respuesta
        output = "\ufeff" + csv_content
        response = make_response(output)
        
        # Nombre de archivo sin espacios para máxima compatibilidad
        filename = f"Reporte_Discrepancias_Finca_{finca_id}.csv"
        
        # Cabeceras ultra-compatibles
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Pragma"] = "public"
        response.headers["Expires"] = "0"
        response.headers["Cache-Control"] = "must-revalidate, post-check=0, pre-check=0"
        
        return response
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    print("!!! ERROR DETECTADO !!!")
    print(traceback.format_exc())
    return jsonify({
        "error": str(e),
        "traceback": traceback.format_exc()
    }), 500

@app.route('/coordenadas', methods=['POST'])
def coordenadas():
    datos = request.json
    finca_id, persona_id, fecha = datos.get('finca_id'), datos.get('persona_id'), datos.get('fecha')
    return jsonify(agente.obtener_coordenadas(finca_id, persona_id, fecha))

@app.route('/detalle/<int:finca_id>/<int:persona_id>/<fecha>')
def detalle(finca_id, persona_id, fecha):
    conn = agente.get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nombre, apellidos, codigo FROM personas WHERE persona_id = %s", (persona_id,))
    persona = cursor.fetchone()
    conn.close()
    nombre = f"{persona['nombre']} {persona['apellidos']}" if persona else f"ID: {persona_id}"
    codigo = persona['codigo'] if persona else "-"
    return render_template('detalle.html', finca_id=finca_id, persona_id=persona_id, fecha=fecha, nombre=nombre, codigo=codigo)

@app.route('/poligonos/<int:finca_id>')
def poligonos(finca_id):
    persona_id = request.args.get('persona_id', type=int)
    fecha = request.args.get('fecha')
    return jsonify(agente.obtener_poligonos_filtrados(finca_id, persona_id, fecha))

@app.route('/spots/<int:finca_id>')
def spots(finca_id):
    persona_id = request.args.get('persona_id', type=int)
    fecha = request.args.get('fecha')
    return jsonify(agente.obtener_spots_filtrados(finca_id, persona_id, fecha))

@app.route('/puntos_labores/<int:finca_id>/<int:persona_id>/<fecha>')
def puntos_labores(finca_id, persona_id, fecha):
    return jsonify(agente.obtener_puntos_labores(finca_id, persona_id, fecha, version='v545'))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
