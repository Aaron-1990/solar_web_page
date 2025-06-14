#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess

def run_command(command):
    """Ejecuta un comando en la terminal y maneja los errores."""
    print(f"▶️ Ejecutando: {' '.join(command)}")
    
    # Usamos subprocess.run para ejecutar el comando
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
    
    # Si el comando falla (código de retorno no es 0), muestra el error y termina.
    if result.returncode != 0:
        print(f"❌ Error al ejecutar el comando:")
        print(result.stderr)
        sys.exit(1) # Termina el script con un código de error
    
    # Si todo va bien, muestra la salida del comando.
    print(result.stdout)
    print("-" * 30)
    return True

# --- Lógica Principal del Script ---

# 1. Pedir el mensaje para el commit.
commit_message = input("📝 Introduce el mensaje para tu commit: ")
if not commit_message:
    print("❌ El mensaje del commit no puede estar vacío. Abortando.")
    sys.exit(1)

# 2. Definir la secuencia de comandos de Git
git_commands = [
    ["git", "add", "."],
    ["git", "commit", "-m", commit_message],
    ["git", "push"]
]

# 3. Ejecutar cada comando en secuencia
print("\nIniciando proceso de sincronización con GitHub...")
print("=" * 30)

for command in git_commands:
    run_command(command)

print("✅ ¡Proceso completado! Tus cambios han sido subidos a GitHub.")