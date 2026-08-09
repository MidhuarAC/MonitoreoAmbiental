import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker


# Cargar variables del archivo .env
load_dotenv()


# Leer datos de conexión
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


# Construir la conexión de forma segura
# Esto evita problemas con caracteres especiales
# en usuario o contraseña.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)


# Crear el motor de conexión
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Crear sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def obtener_conexion():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()