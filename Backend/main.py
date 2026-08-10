from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from datetime import datetime
import pandas as pd
import io
import os

from Backend.database import engine


# ============================================================
# APLICACIÓN
# ============================================================

app = FastAPI(
    title="Sistema de Monitoreo Ambiental",
    description="Sistema de consulta de datos históricos de calidad de agua",
    version="0.1.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# FRONTEND
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "Frontend")

app.mount(
    "/frontend",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend"
)

# ============================================================
# INICIO
# ============================================================

@app.get("/")
def inicio():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "index.html")
    )

# ============================================================
# PRUEBA BASE DE DATOS
# ============================================================

@app.get("/api/prueba-bd")
def prueba_base_datos():

    try:

        with engine.connect() as conexion:

            resultado = conexion.execute(
                text("SELECT 1")
            )

            valor = resultado.scalar()

        return {
            "base_de_datos": "conectada",
            "resultado": valor,
            "estado": "OK"
        }

    except Exception as error:

        return {
            "base_de_datos": "error",
            "detalle": str(error),
            "estado": "ERROR"
        }


# ============================================================
# ESTACIONES
# ============================================================

@app.get("/api/estaciones")
def obtener_estaciones():

    try:

        with engine.connect() as conexion:

            resultado = conexion.execute(
                text("""
                    SELECT
                        id,
                        codigo,
                        nombre,
                        descripcion,
                        latitud,
                        longitud,
                        activo
                    FROM estaciones
                    WHERE activo = TRUE
                    ORDER BY codigo
                """)
            )

            estaciones = []

            for fila in resultado:

                estaciones.append({

                    "id": fila.id,

                    "codigo": fila.codigo,

                    "nombre": fila.nombre,

                    "descripcion": fila.descripcion,

                    "latitud": fila.latitud,

                    "longitud": fila.longitud,

                    "activo": fila.activo

                })

        return estaciones

    except Exception as error:

        return {

            "estado": "ERROR",

            "detalle": str(error)

        }


# ============================================================
# MEDICIONES
# ============================================================

@app.get("/api/mediciones")
def obtener_mediciones(

    estacion: str,

    parametro: str,

    fecha_inicio: datetime,

    fecha_fin: datetime

):

    parametros_permitidos = {

        "ph": "ph",

        "conductividad": "conductividad",

        "caudal": "caudal",

        "tds": "tds",

        "od": "od",

        "turbidez": "turbidez"

    }


    parametro = parametro.lower()


    if parametro not in parametros_permitidos:

        return {

            "estado": "ERROR",

            "detalle": "Parámetro no válido",

            "parametros_permitidos":
                list(parametros_permitidos.keys())

        }


    columna = parametros_permitidos[parametro]


    try:

        with engine.connect() as conexion:

            consulta = text(f"""

                SELECT

                    m.fecha_hora,

                    m.{columna} AS valor

                FROM mediciones_agua m

                INNER JOIN estaciones e

                    ON m.estacion_id = e.id

                WHERE e.codigo = :estacion

                AND m.fecha_hora >= :fecha_inicio

                AND m.fecha_hora <= :fecha_fin

                AND m.{columna} IS NOT NULL

                ORDER BY m.fecha_hora

            """)


            resultado = conexion.execute(

                consulta,

                {

                    "estacion": estacion,

                    "fecha_inicio": fecha_inicio,

                    "fecha_fin": fecha_fin

                }

            )


            datos = []


            for fila in resultado:

                datos.append({

                    "fecha_hora": fila.fecha_hora,

                    "valor":
                        float(fila.valor)
                        if fila.valor is not None
                        else None

                })


        return {

            "estado": "OK",

            "estacion": estacion,

            "parametro": parametro,

            "fecha_inicio": fecha_inicio,

            "fecha_fin": fecha_fin,

            "total": len(datos),

            "datos": datos

        }


    except Exception as error:

        return {

            "estado": "ERROR",

            "detalle": str(error)

        }


# ============================================================
# IMPORTAR EXCEL
# ============================================================

@app.post("/api/importar-excel")
async def importar_excel(

    archivo: UploadFile = File(...)

):

    try:

        # ----------------------------------------------------
        # COMPROBAR EXTENSIÓN
        # ----------------------------------------------------

        if not archivo.filename.lower().endswith(
            (".xlsx", ".xls")
        ):

            return {

                "estado": "ERROR",

                "detalle":
                    "El archivo debe ser Excel (.xlsx o .xls)"

            }


        # ----------------------------------------------------
        # LEER ARCHIVO
        # ----------------------------------------------------

        contenido = await archivo.read()


        df = pd.read_excel(
            io.BytesIO(contenido)
        )


        # ----------------------------------------------------
        # LIMPIAR NOMBRES DE COLUMNAS
        # ----------------------------------------------------

        df.columns = [
            str(columna).strip()
            for columna in df.columns
        ]


        # ----------------------------------------------------
        # COLUMNAS OBLIGATORIAS
        # ----------------------------------------------------

        columnas_requeridas = [

            "fecha",

            "punto",

            "pH",

            "conductividad",

            "caudal",

            "TDS",

            "OD",

            "turbidez"

        ]


        faltantes = [

            columna

            for columna in columnas_requeridas

            if columna not in df.columns

        ]


        if faltantes:

            return {

                "estado": "ERROR",

                "detalle":
                    "Faltan columnas obligatorias",

                "columnas_faltantes":
                    faltantes

            }


        # ----------------------------------------------------
        # FECHAS
        # ----------------------------------------------------

        df["fecha"] = pd.to_datetime(

            df["fecha"],

            errors="coerce"

        )


        fechas_invalidas = int(

            df["fecha"].isna().sum()

        )


        if fechas_invalidas > 0:

            return {

                "estado": "ERROR",

                "detalle":
                    "Existen fechas inválidas",

                "filas_afectadas":
                    fechas_invalidas

            }


        # ----------------------------------------------------
        # PUNTOS
        # ----------------------------------------------------

        df["punto"] = (

            df["punto"]

            .astype(str)

            .str.strip()

        )


        # ----------------------------------------------------
        # PARÁMETROS NUMÉRICOS
        # ----------------------------------------------------

        parametros = [

            "pH",

            "conductividad",

            "caudal",

            "TDS",

            "OD",

            "turbidez"

        ]


        for parametro in parametros:

            df[parametro] = pd.to_numeric(

                df[parametro],

                errors="coerce"

            )


        # ----------------------------------------------------
        # CONTADORES
        # ----------------------------------------------------

        registros_insertados = 0

        registros_duplicados = 0

        puntos_creados = 0


        # ====================================================
        # GUARDAR EN POSTGRESQL
        # ====================================================

        with engine.begin() as conexion:

            for _, fila in df.iterrows():

                codigo = fila["punto"]


                # ------------------------------------------------
                # BUSCAR ESTACIÓN
                # ------------------------------------------------

                resultado = conexion.execute(

                    text("""
                        SELECT
                            id
                        FROM estaciones
                        WHERE codigo = :codigo
                    """),

                    {
                        "codigo": codigo
                    }

                )


                estacion = resultado.fetchone()


                # ------------------------------------------------
                # SI NO EXISTE, CREAR ESTACIÓN
                # ------------------------------------------------

                if estacion is None:

                    resultado = conexion.execute(

                        text("""
                            INSERT INTO estaciones (

                                codigo,

                                nombre,

                                activo

                            )

                            VALUES (

                                :codigo,

                                :nombre,

                                TRUE

                            )

                            RETURNING id
                        """),

                        {

                            "codigo": codigo,

                            "nombre":
                                f"Punto {codigo}"

                        }

                    )


                    estacion_id = resultado.scalar()


                    puntos_creados += 1


                else:

                    estacion_id = estacion.id


                # ------------------------------------------------
                # INSERTAR MEDICIÓN
                # ------------------------------------------------

                resultado_insertar = conexion.execute(

                    text("""
                        INSERT INTO mediciones_agua (

                            estacion_id,

                            fecha_hora,

                            ph,

                            conductividad,

                            caudal,

                            tds,

                            od,

                            turbidez

                        )

                        VALUES (

                            :estacion_id,

                            :fecha_hora,

                            :ph,

                            :conductividad,

                            :caudal,

                            :tds,

                            :od,

                            :turbidez

                        )

                        ON CONFLICT (

                            estacion_id,

                            fecha_hora

                        )

                        DO NOTHING

                    """),

                    {

                        "estacion_id":
                            estacion_id,

                        "fecha_hora":
                            fila["fecha"],

                        "ph":
                            fila["pH"],

                        "conductividad":
                            fila["conductividad"],

                        "caudal":
                            fila["caudal"],

                        "tds":
                            fila["TDS"],

                        "od":
                            fila["OD"],

                        "turbidez":
                            fila["turbidez"]

                    }

                )


                # ------------------------------------------------
                # CONTAR INSERTADOS / DUPLICADOS
                # ------------------------------------------------

                if resultado_insertar.rowcount == 1:

                    registros_insertados += 1

                else:

                    registros_duplicados += 1


        # ====================================================
        # RESPUESTA
        # ====================================================

        return {

            "estado": "OK",

            "archivo":
                archivo.filename,

            "filas_excel":
                len(df),

            "registros_importados":
                registros_insertados,

            "registros_duplicados":
                registros_duplicados,

            "puntos_creados":
                puntos_creados

        }


    except Exception as error:

        return {

            "estado": "ERROR",

            "detalle": str(error)
        }