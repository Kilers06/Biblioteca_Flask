"""Configuración de la aplicación web mediante variables de entorno."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "clave-local-solo-desarrollo-cambiar")
    KEYDB_HOST = os.getenv("KEYDB_HOST", "localhost")
    KEYDB_PORT = int(os.getenv("KEYDB_PORT", "6379"))
    KEYDB_DB = int(os.getenv("KEYDB_DB", "0"))
    KEYDB_USERNAME = os.getenv("KEYDB_USERNAME") or None
    KEYDB_PASSWORD = os.getenv("KEYDB_PASSWORD") or None
    KEYDB_SSL = os.getenv("KEYDB_SSL", "0") == "1"
