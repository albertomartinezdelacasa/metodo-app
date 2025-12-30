from groq import Groq
from config import GROQ_API_KEY
import notion_service as ns

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Eres un asistente especializado en analisis y escritura de chistes.

Tu conocimiento se basa en el METODO, un sistema de analisis de humor con estos conceptos:

ESTRUCTURA DE UN CHISTE:
1. PREMISA: Contiene el concepto principal y prepara la informacion
   - Concepto: puede ser simple o compuesto
   - Elemento mecanico: detalle de la realidad que tenemos asumido

2. RUPTURA: Donde se altera la realidad usando una tecnica
   - Tecnicas: personificacion, exageracion, inversion, literalizacion, etc.
   - Transforma el elemento mecanico en algo absurdo

3. REMATE: Como se representa la realidad absurda
   - Estructuras: "es como...", "esto es peor que...", directo, etc.

FORMAS DE DISECCIONAR UN CONCEPTO:
- Lo que tienen en comun (ej: casa+arbol -> madera)
- Por tipos/diferenciacion (ej: camara -> seguridad -> esta en el techo)
- [Otras que se vayan descubriendo]

TU ROL:
- Ayudar a ESCRIBIR chistes, no escribirlos por el usuario
- Sugerir formas de desarrollar conceptos
- Proponer realidades absurdas a partir de elementos mecanicos
- Buscar ejemplos en la biblioteca de chistes analizados
- Sugerir tecnicas de ruptura aplicables

IMPORTANTE:
- Eres una herramienta de apoyo al proceso creativo
- No escribes chistes completos, sugieres direcciones
- Te basas en la biblioteca de chistes analizados cuando sea relevante
"""


def get_library_context():
    """Obtiene el contexto de la biblioteca de chistes analizados"""
    try:
        entries = ns.get_all_entries(limit=50)

        # Filtrar entradas relevantes (ejemplos, catalogos)
        relevant = []
        for entry in entries:
            titulo = entry.get("titulo", "").upper()
            if any(keyword in titulo for keyword in ["EJEMPLO", "CATALOGO", "PRINCIPIO"]):
                relevant.append(entry)

        if not relevant:
            return "La biblioteca de chistes analizados esta vacia."

        context = "BIBLIOTECA DE CHISTES ANALIZADOS:\n\n"
        for entry in relevant:
            context += f"## {entry.get('titulo', 'Sin titulo')}\n"
            # Obtener contenido completo
            try:
                full_entry = ns.get_entry_by_id(entry["id"])
                context += f"{full_entry.get('contenido', '')}\n\n"
            except:
                pass

        return context
    except Exception as e:
        return f"Error al obtener biblioteca: {str(e)}"


def chat_with_agent(user_message: str, include_library: bool = True):
    """Enviar mensaje al agente y obtener respuesta"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Agregar contexto de la biblioteca si se solicita
    if include_library:
        library_context = get_library_context()
        messages.append({
            "role": "system",
            "content": f"CONTEXTO DE LA BIBLIOTECA:\n\n{library_context}"
        })

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=2000
    )

    return response.choices[0].message.content


def suggest_development(concepto: str):
    """Sugerir formas de desarrollar un concepto"""
    prompt = f"""Tengo el concepto: "{concepto}"

Ayudame a desarrollarlo:
1. Que tipo de concepto es (simple/compuesto)?
2. Como podria diseccionarlo para encontrar el elemento mecanico?
3. Que detalles de la realidad tiene asumidos?
4. Que tecnicas de ruptura podrian funcionar?

Dame sugerencias concretas, no escribas el chiste por mi."""

    return chat_with_agent(prompt)


def suggest_absurd_realities(elemento_mecanico: str):
    """Proponer realidades absurdas a partir de un elemento mecanico"""
    prompt = f"""Tengo este elemento mecanico (detalle de la realidad): "{elemento_mecanico}"

Proponme realidades absurdas que podrian surgir de alterar este elemento.
Dame varias opciones usando diferentes tecnicas de ruptura.

Solo dame las ideas/direcciones, no chistes completos."""

    return chat_with_agent(prompt)


def analyze_concept(concepto: str):
    """Analizar un concepto y sus posibilidades"""
    prompt = f"""Analiza el concepto: "{concepto}"

1. Tipos: tiene diferentes tipos/variantes?
2. Contexto: donde aparece normalmente?
3. Caracteristicas: que lo define?
4. Asociaciones: con que otros conceptos se relaciona?
5. Elementos mecanicos potenciales: que detalles de la realidad tiene?

Basate en ejemplos de la biblioteca si hay alguno similar."""

    return chat_with_agent(prompt)


def find_similar_examples(tecnica: str = None, concepto: str = None):
    """Buscar ejemplos similares en la biblioteca"""
    if tecnica:
        prompt = f"Busca en la biblioteca ejemplos de chistes que usen la tecnica: {tecnica}"
    elif concepto:
        prompt = f"Busca en la biblioteca ejemplos de chistes con conceptos similares a: {concepto}"
    else:
        prompt = "Dame un resumen de los ejemplos disponibles en la biblioteca"

    return chat_with_agent(prompt)
