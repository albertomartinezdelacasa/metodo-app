from notion_client import Client
from typing import Optional
from config import NOTION_TOKEN, NOTION_DATABASE_ID

notion = Client(auth=NOTION_TOKEN)


def get_all_entries(tipo: Optional[str] = None, limit: int = 100):
    """Obtener todas las entradas de la base de datos"""
    filter_params = {}

    if tipo:
        filter_params["filter"] = {
            "property": "Tipo",
            "select": {"equals": tipo}
        }

    response = notion.databases.query(
        database_id=NOTION_DATABASE_ID,
        page_size=limit,
        **filter_params
    )

    return [parse_entry(page) for page in response["results"]]


def get_entry_by_id(page_id: str):
    """Obtener una entrada por su ID"""
    page = notion.pages.retrieve(page_id=page_id)
    blocks = notion.blocks.children.list(block_id=page_id)

    entry = parse_entry(page)
    entry["contenido"] = extract_content(blocks["results"])

    return entry


def create_entry(titulo: str, tipo: str, contenido: str, tags: list = None, fecha: str = None):
    """Crear una nueva entrada"""
    properties = {
        "Nombre": {"title": [{"text": {"content": titulo}}]},
    }

    if tipo:
        properties["Tipo"] = {"select": {"name": tipo}}

    if tags:
        properties["Tags"] = {"multi_select": [{"name": tag} for tag in tags]}

    if fecha:
        properties["Fecha"] = {"date": {"start": fecha}}

    new_page = notion.pages.create(
        parent={"database_id": NOTION_DATABASE_ID},
        properties=properties,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": contenido}}]
                }
            }
        ] if contenido else []
    )

    return {"id": new_page["id"], "url": new_page["url"]}


def update_entry(page_id: str, titulo: str = None, tipo: str = None, contenido: str = None, tags: list = None):
    """Actualizar una entrada existente"""
    properties = {}

    if titulo:
        properties["Nombre"] = {"title": [{"text": {"content": titulo}}]}

    if tipo:
        properties["Tipo"] = {"select": {"name": tipo}}

    if tags is not None:
        properties["Tags"] = {"multi_select": [{"name": tag} for tag in tags]}

    if properties:
        notion.pages.update(page_id=page_id, properties=properties)

    if contenido:
        existing_blocks = notion.blocks.children.list(block_id=page_id)
        for block in existing_blocks["results"]:
            notion.blocks.delete(block_id=block["id"])

        notion.blocks.children.append(
            block_id=page_id,
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": contenido}}]
                    }
                }
            ]
        )

    return {"id": page_id, "updated": True}


def delete_entry(page_id: str):
    """Archivar una entrada"""
    notion.pages.update(page_id=page_id, archived=True)
    return {"id": page_id, "archived": True}


def search_entries(query: str):
    """Buscar entradas por texto"""
    response = notion.search(
        query=query,
        filter={"property": "object", "value": "page"}
    )

    results = []
    for page in response["results"]:
        if page.get("parent", {}).get("database_id") == NOTION_DATABASE_ID.replace("-", ""):
            results.append(parse_entry(page))

    return results


def parse_entry(page: dict) -> dict:
    """Parsear una página de Notion a formato simple"""
    props = page.get("properties", {})

    titulo = ""
    if "Nombre" in props and props["Nombre"]["title"]:
        titulo = props["Nombre"]["title"][0]["plain_text"]

    tipo = ""
    if "Tipo" in props and props["Tipo"].get("select"):
        tipo = props["Tipo"]["select"]["name"]

    tags = []
    if "Tags" in props and props["Tags"].get("multi_select"):
        tags = [t["name"] for t in props["Tags"]["multi_select"]]

    fecha = ""
    if "Fecha" in props and props["Fecha"].get("date"):
        fecha = props["Fecha"]["date"]["start"]

    return {
        "id": page["id"],
        "titulo": titulo,
        "tipo": tipo,
        "tags": tags,
        "fecha": fecha,
        "url": page.get("url", ""),
        "created_time": page.get("created_time", ""),
        "last_edited_time": page.get("last_edited_time", "")
    }


def extract_content(blocks: list) -> str:
    """Extraer contenido de texto de los bloques"""
    content_parts = []

    for block in blocks:
        block_type = block.get("type")

        if block_type == "paragraph":
            texts = block.get("paragraph", {}).get("rich_text", [])
            content_parts.append("".join(t.get("plain_text", "") for t in texts))

        elif block_type == "heading_1":
            texts = block.get("heading_1", {}).get("rich_text", [])
            content_parts.append("# " + "".join(t.get("plain_text", "") for t in texts))

        elif block_type == "heading_2":
            texts = block.get("heading_2", {}).get("rich_text", [])
            content_parts.append("## " + "".join(t.get("plain_text", "") for t in texts))

        elif block_type == "bulleted_list_item":
            texts = block.get("bulleted_list_item", {}).get("rich_text", [])
            content_parts.append("- " + "".join(t.get("plain_text", "") for t in texts))

    return "\n\n".join(content_parts)
