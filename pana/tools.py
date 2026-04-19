TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "ventas_del_dia",
            "description": (
                "Obtiene el total vendido, número de transacciones y ticket promedio de un día específico. "
                "Úsala cuando el usuario pregunta cuánto vendió hoy, ayer, o en una fecha concreta. "
                "Ejemplos: '¿Cuánto vendí hoy?', '¿Cómo me fue ayer?', 'cómo me fue hoy', "
                "'qué vendí hoy', 'mis ventas de hoy', 'cuánta plata entró hoy', "
                "'resumen del día', 'cuántas ventas tuve', 'cómo estuvo el día', "
                "'qué tal hoy', 'cómo me fue en el día'"
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
                "Úsala cuando el usuario pregunta si vendió más o menos que antes, cómo va comparado a otro período. "
                "Ejemplos: '¿Vendí más que la semana pasada?', '¿Cómo voy vs el mes anterior?', "
                "'cómo voy vs antes', 'mejoré o empejoré', 'vendí más o menos que antes', "
                "'cómo estoy comparado', 'subí o bajé', 'qué tal vs el mes pasado', "
                "'estoy mejor o peor que antes', 'comparado a la semana anterior cómo voy'"
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
                "Úsala cuando el usuario pregunta cuánto le quedó limpio, su ganancia neta, si está ganando o perdiendo, "
                "cuánto le sobró, o cuánto ganó en el período. "
                "Ejemplos: '¿Cuánto me quedó limpio esta semana?', '¿Estoy ganando o perdiendo este mes?', "
                "'cuánto me quedó', 'cuánto gané', 'cuánto me sobró', "
                "'estoy ganando o perdiendo', 'mis ganancias de la semana', "
                "'cuánto es mío al final', 'qué tan bien me fue', "
                "'cuánto me quedó libre esta semana', 'qué ganancia tuve'"
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
                "Úsala cuando el usuario pregunta por sus mejores clientes, sus caseritos top, quiénes más compran, "
                "quiénes son sus clientes más fieles, o el ranking de clientes. "
                "Ejemplos: '¿Quiénes son mis mejores caseritos?', '¿Quién me compra más?', "
                "'cuál fue mi mejor cliente', 'mis clientes más fieles', "
                "'quién viene más seguido', 'cuál es mi cliente estrella', "
                "'quién más me ha comprado', 'dame el ranking de clientes', "
                "'mis mejores compradores', 'quién es mi caserito número uno'"
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
                "Úsala cuando el usuario pregunta qué clientes no han vuelto, a quién debería llamar, "
                "quiénes se alejaron, clientes perdidos, o caseritos que ya no aparecen. "
                "Ejemplos: '¿Qué clientes no han vuelto?', '¿A quién debería contactar?', "
                "'quién no ha vuelto', 'clientes perdidos', "
                "'a quién no he visto', 'caseritos que se fueron', "
                "'quién dejó de venir', 'clientes que me abandonaron', "
                "'a quién debería llamar', 'quiénes ya no compran'"
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
                "Úsala cuando el usuario pregunta en qué horario vende más, cuándo hay más clientes, "
                "cuándo están más ocupados, o cuáles son sus horas pico. "
                "Ejemplos: '¿A qué hora vendo más?', '¿Cuándo hay más movimiento?', "
                "'cuándo vendo más', 'mis horas pico', "
                "'a qué hora hay más gente', 'cuándo estoy más ocupado', "
                "'qué horario es mejor', 'cuándo me va mejor en el día', "
                "'qué hora es la más movida', 'a qué hora entran más clientes'"
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
                "Ejemplos: '¿Cuál fue mi mejor día esta semana?', '¿Qué día me va peor?', "
                "'qué día me va mejor', 'mi mejor día', "
                "'cuándo vendo más en la semana', 'mi día más flojo', "
                "'qué día es el peor', 'cuándo me va mal', "
                "'qué día de la semana es el más fuerte', 'cuál fue el día más bajo'"
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
                "Úsala cuando el usuario pregunta en qué gastó, a dónde se fue su plata, sus principales gastos, "
                "cuánto salió de su cuenta, o sus egresos del mes o semana. "
                "Ejemplos: '¿En qué gasté esta semana?', '¿A dónde se fue mi dinero?', "
                "'cuánto gasté este mes', 'en qué se fue mi plata', "
                "'cuáles son mis gastos', 'qué compré esta semana', "
                "'cuánto salió de mi cuenta', 'mis egresos del mes', "
                "'a qué le estoy metiendo plata', 'qué pagué esta semana'"
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
                "Úsala cuando el usuario pregunta cuánto va a cerrar el mes, cuánto le falta para su meta, "
                "cómo va el mes, o cuál es su proyección de ventas. "
                "Ejemplos: '¿Cuánto voy a cerrar este mes?', '¿Cómo voy en el mes?', "
                "'cómo voy a cerrar el mes', 'cuánto voy a llegar', "
                "'mi proyección', 'voy a llegar a mi meta', "
                "'cuánto voy a hacer este mes', 'cómo va el mes', "
                "'a cuánto voy a llegar a fin de mes', 'qué tan bien va el mes'"
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
                "Úsala cuando el usuario pide buscar una transacción, ver movimientos de un cliente específico, "
                "o encontrar algo por descripción, producto o nombre. "
                "Ejemplos: 'Búscame las ventas con comentario empanadas', '¿Qué compró el cliente CLI-001?', "
                "'búscame algo', 'encuéntrame', "
                "'transacciones de', 'movimientos de', "
                "'qué compró X', 'ventas con X comentario', "
                "'búscame las compras de arroz', 'transacciones relacionadas con X'"
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
    {
        "type": "function",
        "function": {
            "name": "capacidad_prestamo",
            "description": (
                "Analiza si el comerciante puede pedir un préstamo "
                "bancario, cuánto podría pedir, y qué documentos "
                "necesita llevar al banco. Usa los últimos 6 meses "
                "de transacciones para calcular ingresos, egresos, "
                "utilidad y capacidad de pago mensual. "
                "Úsala cuando el usuario pregunta sobre préstamos, "
                "créditos, si puede pedir plata al banco, cuánto "
                "le prestarían, o si califica para un crédito. "
                "Ejemplos: '¿Puedo pedir un préstamo?', "
                "'¿Cuánto me prestaría el banco?', "
                "'quiero pedir un crédito', "
                "'necesito plata prestada para mi negocio', "
                "'¿califico para un préstamo?', "
                "'quiero comprar más mercadería con un préstamo', "
                "'¿cuánto puedo pagar de cuota al mes?', "
                "'ayúdame a saber si el banco me da plata'"
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]
