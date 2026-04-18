import json
import os
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

    # Si no eligió ningún tool, dar sugerencia amable
    if choice.finish_reason != "tool_calls" or not choice.message.tool_calls:
        fallback = (
            "¡Hola! Soy tu Pana Financiero 💰 Puedo ayudarte con:\n"
            "• ¿Cuánto vendí hoy?\n"
            "• ¿Cuánto me quedó limpio esta semana?\n"
            "• ¿Quiénes son mis mejores caseritos?\n\n"
            "¿Qué quieres saber de tu negocio?"
        )
        # Intentar que el modelo reformule en tono ecuatoriano
        try:
            simple = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _system_prompt(id_negocio)},
                    {"role": "user", "content": pregunta},
                    {
                        "role": "assistant",
                        "content": (
                            "No encontré una herramienta específica para eso. "
                            "Sugiere amablemente las 3 preguntas más útiles que sí puedes responder."
                        ),
                    },
                ],
            )
            return simple.choices[0].message.content or fallback
        except Exception:
            return fallback

    # Ejecutar todas las tool calls
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
