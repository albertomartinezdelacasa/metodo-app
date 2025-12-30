from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import notion_service as nc
import agent_service as agent

app = FastAPI(
    title="Metodo API",
    description="API para gestionar base de conocimiento en Notion",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EntryCreate(BaseModel):
    titulo: str
    tipo: Optional[str] = None
    contenido: str = ""
    tags: Optional[List[str]] = None
    fecha: Optional[str] = None


class EntryUpdate(BaseModel):
    titulo: Optional[str] = None
    tipo: Optional[str] = None
    contenido: Optional[str] = None
    tags: Optional[List[str]] = None


@app.get("/")
def root():
    return {"status": "ok", "service": "Metodo API", "version": "1.0.0"}


@app.get("/entries")
def list_entries(
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: Nota, Análisis, Conocimiento, Diario"),
    limit: int = Query(100, ge=1, le=100)
):
    """Listar todas las entradas"""
    try:
        entries = nc.get_all_entries(tipo=tipo, limit=limit)
        return {"count": len(entries), "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entries/{entry_id}")
def get_entry(entry_id: str):
    """Obtener una entrada por ID"""
    try:
        entry = nc.get_entry_by_id(entry_id)
        return entry
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/entries")
def create_entry(entry: EntryCreate):
    """Crear nueva entrada"""
    try:
        result = nc.create_entry(
            titulo=entry.titulo,
            tipo=entry.tipo,
            contenido=entry.contenido,
            tags=entry.tags,
            fecha=entry.fecha
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/entries/{entry_id}")
def update_entry(entry_id: str, entry: EntryUpdate):
    """Actualizar entrada existente"""
    try:
        result = nc.update_entry(
            page_id=entry_id,
            titulo=entry.titulo,
            tipo=entry.tipo,
            contenido=entry.contenido,
            tags=entry.tags
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/entries/{entry_id}")
def delete_entry(entry_id: str):
    """Archivar entrada"""
    try:
        result = nc.delete_entry(entry_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
def search(q: str = Query(..., min_length=1, description="Texto a buscar")):
    """Buscar entradas"""
    try:
        results = nc.search_entries(q)
        return {"count": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ AGENTE IA ============

class AgentMessage(BaseModel):
    message: str
    include_library: bool = True


class ConceptRequest(BaseModel):
    concepto: str


class ElementoMecanicoRequest(BaseModel):
    elemento_mecanico: str


@app.post("/agent/chat")
def agent_chat(request: AgentMessage):
    """Chat libre con el agente"""
    try:
        response = agent.chat_with_agent(request.message, request.include_library)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/develop")
def agent_develop_concept(request: ConceptRequest):
    """Sugerir formas de desarrollar un concepto"""
    try:
        response = agent.suggest_development(request.concepto)
        return {"concepto": request.concepto, "sugerencias": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/absurd")
def agent_suggest_absurd(request: ElementoMecanicoRequest):
    """Proponer realidades absurdas a partir de un elemento mecanico"""
    try:
        response = agent.suggest_absurd_realities(request.elemento_mecanico)
        return {"elemento_mecanico": request.elemento_mecanico, "realidades_absurdas": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agent/analyze")
def agent_analyze_concept(request: ConceptRequest):
    """Analizar un concepto y sus posibilidades"""
    try:
        response = agent.analyze_concept(request.concepto)
        return {"concepto": request.concepto, "analisis": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agent/examples")
def agent_find_examples(
    tecnica: Optional[str] = Query(None, description="Buscar por tecnica"),
    concepto: Optional[str] = Query(None, description="Buscar por concepto similar")
):
    """Buscar ejemplos en la biblioteca"""
    try:
        response = agent.find_similar_examples(tecnica=tecnica, concepto=concepto)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ FRONTEND ============
# Servir archivos estáticos del frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/app")
    @app.get("/app/{path:path}")
    def serve_frontend(path: str = ""):
        index_path = os.path.join(frontend_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        raise HTTPException(status_code=404, detail="Frontend not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
