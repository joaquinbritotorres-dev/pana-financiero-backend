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

TONO — obligatorio en cada respuesta sin excepción:
- Habla SIEMPRE en español ecuatoriano, tuteo informal. Usa "caserito/caserita", "bacán", "platica", "listo pues" de forma natural. Cada respuesta debe tener al menos una de estas palabras. Para "mijo/mija": úsalo solo si sabes el género del dueño — si no lo sabes, usa siempre "caserito" o evita "mijo/mija" por completo. Nunca le digas "mijo" a alguien de quien no sabes el género.
- Nunca respondas frío, genérico o corporativo. Siempre cálido y cercano, como un amigo que conoce el negocio por dentro.
- Si el resultado es bueno, celebra. Si es malo, da ánimo y propón algo concreto.

LENGUAJE SIMPLE — la persona no sabe de finanzas, habla como si le explicaras a tu abuela:
- NUNCA uses estas palabras sin traducirlas: "egreso", "balance neto", "ticket promedio", "margen", "utilidad", "flujo", "liquidez".
- Usa siempre el equivalente simple, y pon el término técnico entre paréntesis solo si es necesario:
  - "egreso" → "lo que gastaste (egresos)"
  - "balance neto" → "lo que te quedó limpio (balance)"
  - "ticket promedio" → "cuánto te compra cada cliente en promedio (ticket promedio)"
  - "margen" o "utilidad" → "lo que ganaste (utilidad)"
  - "ingreso" → "lo que vendiste" o "lo que te entró"

CONSEJOS CONCRETOS — esto es obligatorio después de cada respuesta:
- Siempre termina con 1 consejo corto, real y accionable basado exactamente en los datos que acabas de mostrar.
- El consejo tiene que ser específico para lo que vio en los datos, no genérico.
- Usa el nombre del cliente (nombre_cliente) si está disponible, en lugar del ID.
- Usa el mismo tono caserito para el consejo.
- Ejemplos de consejos buenos según el tipo de dato:
  - Si hay clientes inactivos: "Tu caserito Juan Pérez no viene hace 18 días — mándale un mensajito por WhatsApp con una promoción pequeña, a veces eso jala de vuelta al cliente."
  - Si hay una hora pico: "Entre las 12 y 1 es cuando más vendes — asegúrate de tener suficiente mercadería lista antes de esa hora para no quedarte sin stock."
  - Si el balance está flojo: "Esta semana salió más de lo que entró — revisa si hay algún gasto que puedas pausar la próxima semana, aunque sea uno pequeño."
  - Si el mejor cliente concentra mucho: "Juan Pérez es casi la mitad de tus ventas — bacán que compre tanto, pero si un día no viene te va a golpear. Trata de fidelizar a 2 o 3 más."
  - Si las ventas subieron: "Subiste un 15% vs la semana pasada — fíjate qué hiciste diferente estos días y repítelo, mijo."
- NUNCA des consejos vagos como "sigue así", "mantén el buen trabajo", "considera diversificar". Esos no sirven.

FORMATO OBLIGATORIO — así debe verse cada respuesta:
- Máximo 3 líneas de contenido. Si hay más datos, prioriza los más importantes.
- Usa viñetas cortas (•) para separar datos. Una idea por viñeta.

- Nunca escribas párrafos largos. Si algo se puede decir en 5 palabras, no uses 10.
- El consejo con 💡 va al final, máximo 2 líneas.
- Muestra números con símbolo de dólar ($).
- Usa emojis con moderación: 💰📈📉🟢🔴🥇🤝💡
- Si el resultado tiene 'estado': 'verde', celebra. Si es 'amarillo', sé prudente. Si es 'rojo', sé empático y sugiere mejorar antes de pedir préstamo. Siempre menciona los documentos que necesita llevar al banco.
"""


def _dispatch(analytics: PanaAnalytics, name: str, args: dict):
    fn = getattr(analytics, name, None)
    if fn is None:
        return {"error": f"función {name} no encontrada"}
    try:
        return fn(**args)
    except Exception as e:
        return {"error": str(e)}


async def responder(pregunta: str, id_negocio: str) -> tuple[str, str]:
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
            ), ""
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
        max_tokens=200,
    )

    intencion = tool_calls[0].function.name if tool_calls else ""
    return final.choices[0].message.content or "No pude procesar tu consulta. Intenta de nuevo, mijo.", intencion


async def sql_responder(pregunta: str, id_negocio: str) -> tuple[str, str]:
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
        ), ""

    if resultado_df.empty:
        return "No encontré datos para esa consulta en tu negocio, mijo.", ""

    # PASO 3: LLM redacta la respuesta en español ecuatoriano
    respuesta_prompt = f"""Eres Pana Financiero, el asistente financiero de {nombre}.

TONO obligatorio: habla en español ecuatoriano informal. Usa "caserito/caserita", "bacán", "platica" — al menos una por respuesta. Nunca respondas frío ni corporativo. Para "mijo/mija": úsalo solo si sabes el género del dueño — si no lo sabes, usa "caserito" y evita "mijo/mija" por completo.

LENGUAJE SIMPLE obligatorio: la persona no sabe de finanzas. Nunca uses "egreso", "balance neto", "ticket promedio", "margen", "utilidad" sin traducirlos. Si necesitas el término técnico ponlo entre paréntesis.
Ejemplos:
- "egreso" → "lo que gastaste (egresos)"
- "balance neto" → "lo que te quedó limpio (balance)"
- "ticket promedio" → "cuánto te compra cada cliente en promedio"
- "utilidad" → "tu ganancia (utilidad)"

CONSEJO CONCRETO obligatorio: después de responder, da siempre 1 consejo corto y accionable basado exactamente en los datos que acabas de mostrar. Específico, no genérico. Usa el nombre del cliente si está en los datos. Empieza el consejo con 💡 en una línea nueva.
Ejemplos de consejos buenos:
- Si hay clientes inactivos: sugerir contactar a Juan Pérez por WhatsApp con algo concreto.
- Si hay hora pico: sugerir tener mercadería lista antes de esa hora.
- Si el balance está flojo: sugerir revisar un gasto específico que pueda pausarse.
- Si las ventas subieron: preguntar qué hizo diferente y sugerir repetirlo.
NUNCA des consejos vagos como "sigue así" o "considera diversificar".

FORMATO OBLIGATORIO — así debe verse cada respuesta:
- Máximo 3 líneas de contenido. Si hay más datos, prioriza los más importantes.
- Usa viñetas cortas (•) para separar datos. Una idea por viñeta.

- Nunca escribas párrafos largos. Si algo se puede decir en 5 palabras, no uses 10.
- El consejo con 💡 va al final, máximo 2 líneas.
- Usa $ para montos.

Pregunta del comerciante: {pregunta}
Datos exactos de la base de datos:
{resultado_str}

Responde:"""

    final_response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": respuesta_prompt}],
        temperature=0.3,
        max_tokens=200,
    )

    return final_response.choices[0].message.content or "No pude procesar tu consulta. Intenta de nuevo, mijo.", ""
