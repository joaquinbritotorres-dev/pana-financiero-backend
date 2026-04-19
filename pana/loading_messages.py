import random

MENSAJES_CARGA = [
    "Revisando tus números, caserito... 🔍",
    "Calculando todo para darte la info exacta... 💰",
    "Un segundito, estoy mirando tus datos... 📊",
    "Buscando la respuesta en tus movimientos... 🧮",
    "Ya casi, caserito, estoy en eso... ⚡",
    "Revisando tu negocio por dentro... 🏪",
    "Dame un momento, te traigo la info... 📈",
]

def get_mensaje_carga() -> str:
    return random.choice(MENSAJES_CARGA)
