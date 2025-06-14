#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from datetime import date
from pathlib import Path # Importamos la clase Path

# --- Configuración Automática ---
LOGS_DIRECTORY = "logs"

# ¡Magia! Detecta automáticamente el nombre del proyecto a partir del nombre 
# del directorio que contiene este script.
try:
    PROJECT_NAME = Path(__file__).resolve().parent.name
except NameError:
    # Esto es un fallback por si el script se ejecuta en un entorno
    # donde __file__ no está definido.
    PROJECT_NAME = "mi-proyecto"


# --- Lógica del Script ---

# 1. Obtener la fecha de hoy y preparar los nombres de archivo y carpeta
today = date.today()
formatted_date = today.strftime("%Y-%m-%d")
log_filename = f"{formatted_date}.md"
log_filepath = os.path.join(LOGS_DIRECTORY, log_filename)

# 2. Verificar si el directorio 'logs' existe, si no, crearlo.
if not os.path.isdir(LOGS_DIRECTORY):
    print(f"Directorio '{LOGS_DIRECTORY}' no encontrado. Creándolo...")
    os.makedirs(LOGS_DIRECTORY)
    print("Directorio creado.")

# 3. Verificar si el archivo de log para hoy ya existe.
if not os.path.exists(log_filepath):
    print(f"Creando archivo de log para hoy: {log_filepath}")

    # --- PLANTILLA MEJORADA Y AUTOMÁTICA ---
    template_content = f"""# Reporte de Avance - {formatted_date}

> **Instrucción para la IA:**
> Para generar el contenido de este reporte, copia y pega el siguiente prompt en el chat al finalizar tu jornada.
>
> ```prompt
> Actúa como mi asistente para el proyecto '{PROJECT_NAME}'. Necesito generar el reporte de progreso para el día de hoy, {formatted_date}. Basado en nuestra conversación y los cambios que discutimos, crea un resumen en formato Markdown con estas tres secciones: '✅ Avances de Hoy', '📂 Archivos Modificados', y '🚀 Siguientes Pasos'.
> ```

---

### ✅ Avances de Hoy

- *Pega aquí los avances generados por la IA.*

### 📂 Archivos Modificados

- *Pega aquí los archivos modificados generados por la IA.*

### 🚀 Siguientes Pasos

- *Pega aquí los siguientes pasos generados por la IA.*

"""

    # 4. Crear y escribir la plantilla en el archivo del día.
    with open(log_filepath, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print(f"¡Archivo de log creado para el proyecto '{PROJECT_NAME}' y listo para ser llenado!")
else:
    print(f"El archivo de log para hoy ({log_filepath}) ya existe. ¡Listo para editar!")