import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# Cargar variables del archivo .env
load_dotenv()

# ============================================================
# CONEXIÓN A BASE DE DATOS
# ============================================================

# En Render utilizaremos DATABASE_URL.
# En la PC local podemos seguir utilizando DB_USER, DB_PASSWORD,
# DB_HOST, DB_PORT y DB_NAME desde el archivo .env.

DATABASE_URL_ENV = os.getenv("DATABASE_URL")

if DATABASE_URL_ENV:
    # Render puede entregar la URL comenzando con postgres://
    # SQLAlchemy trabaja mejor con postgresql+psycopg2://
    if DATABASE_URL_ENV.startswith("postgres://"):
        DATABASE_URL_ENV = DATABASE_URL_ENV.replace(
            "postgres://",
            "postgresql+psycopg2://",
            1
        )

    elif DATABASE_URL_ENV.startswith("postgresql://"):
        DATABASE_URL_ENV = DATABASE_URL_ENV.replace(
            "postgresql://",
            "postgresql+psycopg2://",
            1
        )

    DATABASE_URL = DATABASE_URL_ENV

else:
    # ========================================================
    # CONEXIÓN LOCAL
    # ========================================================

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    DATABASE_URL = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
    )


# ============================================================
# CREAR MOTOR
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# ============================================================
# SESIONES
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ============================================================
# OBTENER CONEXIÓN
# ============================================================

def obtener_conexion():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()