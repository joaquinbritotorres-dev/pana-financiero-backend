from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from pana.loader import load_all, get_negocios_list
from pana.assistant import responder


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all()
    yield


app = FastAPI(title="Pana Financiero API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    pregunta: str
    id_negocio: str


class AskResponse(BaseModel):
    respuesta: str
    mensaje_carga: str = ""


@app.get("/")
def health():
    return {"status": "ok", "service": "Pana Financiero API"}


@app.get("/api/negocios")
def negocios():
    return get_negocios_list()


@app.post("/api/ask", response_model=AskResponse)
async def ask(body: AskRequest):
    if not body.pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
    if not body.id_negocio.strip():
        raise HTTPException(status_code=400, detail="id_negocio requerido")
    try:
        from pana.loading_messages import get_mensaje_carga
        respuesta = await responder(body.pregunta, body.id_negocio)
        return AskResponse(respuesta=respuesta, mensaje_carga=get_mensaje_carga())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask/sql", response_model=AskResponse)
async def ask_sql(body: AskRequest):
    """
    Endpoint Text-to-SQL: precisión exacta para fechas y datos puntuales.
    El LLM genera SQL, SQLite ejecuta, el LLM solo redacta.
    """
    if not body.pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía")
    if not body.id_negocio.strip():
        raise HTTPException(status_code=400, detail="id_negocio requerido")
    try:
        from pana.assistant import sql_responder
        from pana.loading_messages import get_mensaje_carga
        respuesta = await sql_responder(body.pregunta, body.id_negocio)
        return AskResponse(respuesta=respuesta, mensaje_carga=get_mensaje_carga())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
