import json
import os
import pandas as pd
from openai import AsyncOpenAI
from .analytics import PanaAnalytics
from .tools import TOOLS
from .loader import get_df, NEGOCIOS_META

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def _system_prompt(id_negocio: str) -> str:
    meta = NEGOCIOS_META.get(id_negocio, {})
    nombre = meta.get("nombre", "tu negocio")
    return f"""Eres Pana Financiero, el asistente financiero conversacional de Deuna Negocios.
Estás ayudando al dueño de "{nombre}".

Reglas importantes:
- Habla en español ecuatoriano, tuteo informal y natural. Usa "caserito", "mijo", "bacán", "platica" con moderación, sin exagerar.
- Usa los datos que te dan las herramientas. NUNCA inventes cifras ni hagas cálculos tú mismo.
- Si una función devuelve resultado vacío, di "no tengo datos de ese período" amablemente.
- Nombra el negocio si aporta claridad.
- Usa emojis con mesura: 💰📈📉🟢🔴🥇🤝📲
- Respuestas breves (2-4 frases), accionables. No escribas párrafos largos.
- Si el resultado tiene números, muéstralos claros con símbolo de dólar ($).
- No uses términos contables complejos: di "lo que te quedó limpio" en vez de "margen neto".
- Si el resultado tiene 'estado': 'verde', celebra con el comerciante. Si es 'amarillo', sé prudente. Si es 'rojo', sé empático y sugiere mejorar el balance antes de pedir préstamo. Siempre menciona los documentos que necesita llevar al banco.
"""


def _dispatch(analytics: PanaAnalytics, name: str, args: dict):
    fn = getattr(analytics, name, None)
    if fn is None:
        return {"error": f"función {name} no encontrada"}
    try:
        return fn(**args)
    except Exception as e:
        return {"error": str(e)}


async def responder(pregunta: str, id_negocio: str) -> str:
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    client = _get_client()

    df = get_df(id_negocio)
    analytics = PanaAnalytics(df)

    messages = [
        {"role": "system", "content": _system_prompt(id_negocio)},
        {"role": "user", "content": pregunta},
    ]

    # Primera llamada: el modelo decide qué tool usar
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    choice = response.choices[0]

    if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
        retry = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="required",
        )
        retry_choice = retry.choices[0]
        if not retry_choice.message.tool_calls:
            return (
                "No entendí bien tu pregunta, caserito. "
                "Puedes preguntarme cosas como: "
                "¿Cuánto vendí hoy?, ¿Quiénes son mis mejores caseritos?, "
                "¿En qué gasté esta semana?, ¿Cuánto me quedó limpio?"
            )
        tool_calls = retry_choice.message.tool_calls
        messages.append(retry_choice.message)
    else:
        tool_calls = choice.message.tool_calls
        messages.append(choice.message)

    for tc in tool_calls:
        args = json.loads(tc.function.arguments)
        result = _dispatch(analytics, tc.function.name, args)
        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(result, ensure_ascii=False, default=str),
        })

    # Segunda llamada: formatea el resultado en español natural
    final = await client.chat.completions.create(
        model=model,
        messages=messages,
    )

    return final.choices[0].message.content or "No pude procesar tu consulta. Intenta de nuevo, mijo."


async def sql_responder(pregunta: str, id_negocio: str) -> str:
    """
    Alternativa a responder() usando Text-to-SQL para precisión exacta.
    El LLM genera SQL → SQLite ejecuta → LLM redacta respuesta.
    Cero alucinaciones numéricas: los números los produce SQLite.
    """
    from .sql_engine import run_sql_query, SCHEMA_DESCRIPTION, _extract_sql

    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    client = _get_client()
    meta = NEGOCIOS_META.get(id_negocio, {})
    nombre = meta.get("nombre", "tu negocio")

    # PASO 1: LLM genera la query SQL
    sql_prompt = f"""Eres un experto en SQL. Tienes esta tabla de base de datos:

{SCHEMA_DESCRIPTION}

Reglas estrictas:
- Solo devuelve la query SQL, nada más
- No expliques nada
- No uses markdown ni backticks
- La query debe ser SQLite válido
- ventas = tipo_movimiento = 'ingreso'
- gastos = tipo_movimiento = 'egreso'

Pregunta de negocio: {pregunta}

SQL:"""

    sql_response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": sql_prompt}],
        temperature=0,
    )

    raw_sql = sql_response.choices[0].message.content or ""

    sql_query = _extract_sql(raw_sql)

    # PASO 2: SQLite ejecuta la query — cero alucinaciones
    try:
        resultado_df = run_sql_query(sql_query, id_negocio)
        resultado_str = resultado_df.to_string(index=False)
    except Exception as e:
        return (
            f"No pude procesar esa consulta, caserito. "
            f"Intenta preguntar de otra forma. (Error interno: {e})"
        )

    if resultado_df.empty:
        return "No encontré datos para esa consulta en tu negocio, mijo."

    # PASO 3: LLM redacta la respuesta en español ecuatoriano
    respuesta_prompt = f"""Eres Pana Financiero, el asistente financiero de {nombre}.
Habla en español ecuatoriano informal. Usa "caserito", "mijo", "bacán" con moderación.
Responde en 2-4 frases máximo. Sé directo y claro. Usa $ para montos.
No uses términos contables complejos.

Pregunta del comerciante: {pregunta}
Datos exactos de la base de datos:
{resultado_str}

Responde de forma natural y conversacional:"""

    final_response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": respuesta_prompt}],
        temperature=0.3,
    )

    return final_response.choices[0].message.content or "No pude procesar tu consulta. Intenta de nuevo, mijo."
