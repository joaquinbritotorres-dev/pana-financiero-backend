TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ventas_del_dia",
            "description": (
                "Obtiene el total vendido, número de transacciones y ticket promedio de un día específico. "
                "Úsala cuando el usuario pregunta cuánto vendió hoy, ayer, o en una fecha concreta. "
                "Ejemplo: '¿Cuánto vendí hoy?', '¿Cómo me fue ayer?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha": {
                        "type": "string",
                        "description": "Fecha en formato YYYY-MM-DD, o 'hoy' para el día más reciente del dataset.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comparar_periodos",
            "description": (
                "Compara los ingresos de esta semana vs la anterior, o de este mes vs el anterior. "
                "Úsala cuando el usuario pregunta si vendió más o menos que antes. "
                "Ejemplo: '¿Vendí más que la semana pasada?', '¿Cómo voy vs el mes anterior?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo": {
                        "type": "string",
                        "enum": ["semana", "mes"],
                        "description": "'semana' para comparar semana actual vs anterior. 'mes' para mes actual vs anterior.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "balance_neto",
            "description": (
                "Calcula el balance neto (ingresos menos egresos) de esta semana o este mes. "
                "Úsala cuando el usuario pregunta cuánto le quedó limpio, su ganancia neta, o si está ganando o perdiendo. "
                "Ejemplo: '¿Cuánto me quedó limpio esta semana?', '¿Estoy ganando o perdiendo este mes?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo": {
                        "type": "string",
                        "enum": ["semana", "mes"],
                        "description": "'semana' para balance de esta semana, 'mes' para balance de este mes.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "top_caseritos",
            "description": (
                "Devuelve el top de clientes que más compraron en la semana o el mes. "
                "Úsala cuando el usuario pregunta por sus mejores clientes, sus caseritos top, o quiénes más compran. "
                "Ejemplo: '¿Quiénes son mis mejores caseritos?', '¿Quién me compra más?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo": {
                        "type": "string",
                        "enum": ["semana", "mes"],
                        "description": "'semana' o 'mes' según el período que pregunta el usuario.",
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Cuántos clientes mostrar. Por defecto 3.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clientes_inactivos",
            "description": (
                "Lista los clientes que solían comprar con frecuencia pero no han vuelto hace tiempo. "
                "Úsala cuando el usuario pregunta qué clientes no han vuelto, a quién debería llamar, o quiénes se alejaron. "
                "Ejemplo: '¿Qué clientes no han vuelto?', '¿A quién debería contactar?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dias_umbral": {
                        "type": "integer",
                        "description": "Días de inactividad para considerar a un cliente inactivo. Por defecto 14.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "patron_horario",
            "description": (
                "Analiza a qué horas del día se vende más y menos. "
                "Úsala cuando el usuario pregunta en qué horario vende más, cuándo hay más clientes, o cuándo están más ocupados. "
                "Ejemplo: '¿A qué hora vendo más?', '¿Cuándo hay más movimiento?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mejor_peor_dia",
            "description": (
                "Identifica el mejor día (más ventas) y el peor día del período. También el día de la semana estructuralmente más flojo. "
                "Úsala cuando el usuario pregunta cuál fue su mejor o peor día, o qué día de la semana les va peor. "
                "Ejemplo: '¿Cuál fue mi mejor día esta semana?', '¿Qué día me va peor?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo": {
                        "type": "string",
                        "enum": ["semana", "mes"],
                        "description": "'semana' o 'mes'.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_egresos",
            "description": (
                "Muestra el resumen de gastos y egresos del período, con las categorías donde más se gastó. "
                "Úsala cuando el usuario pregunta en qué gastó, a dónde se fue su plata, o sus principales gastos. "
                "Ejemplo: '¿En qué gasté esta semana?', '¿A dónde se fue mi dinero?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "periodo": {
                        "type": "string",
                        "enum": ["semana", "mes"],
                        "description": "'semana' o 'mes'.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "proyeccion_mes_actual",
            "description": (
                "Proyecta cuánto se va a vender al final del mes basándose en el ritmo actual. "
                "Úsala cuando el usuario pregunta cuánto va a cerrar el mes, cuánto le falta para su meta, o cómo va el mes. "
                "Ejemplo: '¿Cuánto voy a cerrar este mes?', '¿Cómo voy en el mes?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_transacciones",
            "description": (
                "Busca transacciones específicas por comentario o ID de cliente. "
                "Úsala cuando el usuario pide buscar una transacción, ver movimientos de un cliente específico, o encontrar algo por descripción. "
                "Ejemplo: 'Búscame las ventas con comentario empanadas', '¿Qué compró el cliente CLI-001?'"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto a buscar en comentarios o ID de cliente.",
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Número máximo de resultados. Por defecto 10.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
