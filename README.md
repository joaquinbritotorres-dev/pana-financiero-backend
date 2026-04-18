# Pana Financiero — Backend

FastAPI + Pandas + OpenAI para el asistente conversacional financiero.

## Setup (macOS)

1. Navegar al backend:
   cd backend

2. Crear entorno virtual:
   python3 -m venv venv
   source venv/bin/activate

3. Instalar dependencias:
   pip install -r requirements.txt

4. Configurar API key:
   cp .env.example .env
   # Editar .env y pegar tu OPENAI_API_KEY

5. Correr el servidor:
   uvicorn main:app --reload

El servidor queda en http://localhost:8000
Documentación interactiva: http://localhost:8000/docs

## Endpoints
- GET  /api/negocios       Lista de 4 negocios
- POST /api/ask             Body: {pregunta, id_negocio} → {respuesta}

## Probar con curl
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cuánto vendí hoy?", "id_negocio": "NEG-UIO-0001"}'
