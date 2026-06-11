# 🌲 Agente de Comparativa de Líneas SIOMA

Este agente automatizado realiza una comparativa entre la información de **Línea Inicial (LI)** y **Línea Final (LF)** generada por la variable **v_545** (PHP) y la información registrada en el **Mapa de Labores** (cierre de área).

## 🚀 Propósito

El objetivo es identificar discrepancias entre el cálculo dinámico de líneas basado en spots (v_545) y lo que se visualiza físicamente en el mapa de labores, asegurando la integridad de la información reportada.

## 📋 Requisitos

- Python 3.7+
- Acceso a la base de datos MySQL de SIOMA

## 🔧 Instalación

1.  Navega a la carpeta del proyecto:
    ```bash
    cd e:\Sioma\desarrollo\agente_comparativa
    ```
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configura el archivo `.env` con las credenciales de base de datos (ya incluido al crear el proyecto).

## 💻 Uso

### 🖥️ Consola (CLI)

Ejecuta el script proporcionando el `ID de la Finca`, `Fecha desde` y `Fecha hasta`:

```bash
python comparativa.py <finca_id> <desde> <hasta>
```

**Ejemplo:**
```bash
python comparativa.py 31 2024-02-18 2024-02-19
```

### 🌐 Interfaz Web

Para iniciar la interfaz web interactiva (Flask) que incluye mapas y visualización detallada, ejecuta:

```bash
python app.py
```

Luego, abre tu navegador web e ingresa a la siguiente dirección:
[http://localhost:5000](http://localhost:5000)

### 📊 Reporte Generado

El agente mostrará un resumen de las discrepancias en la consola y generará un archivo CSV detallado con el nombre `reporte_comparativa_<finca_id>_<timestamp>.csv` para un análisis profundo.

### 🔍 Lógica de Comparación

- **v_545 Data:** Simula la lógica de `v_545.php` consultando las tablas de labores de palma (`l_pal_artils`, `l_pal_artlis`, etc.) y calculando las líneas mínima/máxima por persona/lote/día.
- **Mapa Labores Data:** Consulta la tabla `cierre_area_labor_dia_personas` y extrae las líneas inicial/final (tajos) almacenadas en formato JSON.
- **Cruze:** Une ambas fuentes por `persona_id`, `lote_id`, `labor_id` y `fecha` para detectar diferencias en los rangos de línea.

---
🚀 *Desarrollado para SIOMA - Automatización de Control de Labores*
