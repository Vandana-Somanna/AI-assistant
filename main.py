
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from pathlib import Path

from agent import chat as agent_chat
import rag
# from mylogs import setup_logging
# # Initialize logging FIRST
# LOG_PATH = setup_logging()
# logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

app = FastAPI()

# --------------------------
# Setup Paths
# --------------------------
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)

# --------------------------
# 1. CHAT INTERFACE
# --------------------------

# GET: Opens the Chat UI in your browser
@app.get("/chat", response_class=HTMLResponse)
async def get_chat_ui():
    template = TEMPLATES_DIR / "chat.html"
    if not template.exists():
        raise HTTPException(404, "chat.html not found in templates folder")
    return template.read_text(encoding="utf-8")

# POST: The actual logic that the UI calls
@app.post("/chat")
async def chat_api(request: Request):
    try:
        body = await request.json()
        message = body.get("message")
        session_id = body.get("session_id", "default")

        if not message:
            raise HTTPException(400, "Message is required")

        answer = agent_chat(message, session_id=session_id)
        return {"session_id": session_id, "answer": answer}
    except Exception as e:
        raise HTTPException(500, f"Chat error: {str(e)}")


# --------------------------
# 2. UPLOAD INTERFACE
# --------------------------

# GET: Opens the Upload UI in your browser
@app.get("/upload", response_class=HTMLResponse)
async def get_upload_ui():
    template = TEMPLATES_DIR / "upload.html"
    if not template.exists():
        raise HTTPException(404, "upload.html not found in templates folder")
    return template.read_text(encoding="utf-8")

# POST: The logic to handle the file upload
@app.post("/upload")
async def upload_api(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(400, "Only .txt files allowed")

    docs_dir = Path(rag.DOCS_DIR)
    docs_dir.mkdir(exist_ok=True)
    
    dest = docs_dir / file.filename
    content = await file.read()
    
    if not content.strip():
        raise HTTPException(400, "File is empty")

    dest.write_bytes(content)
    
    # Trigger RAG Indexing
    from langchain_community.document_loaders import TextLoader
    loader = TextLoader(str(dest))
    docs = loader.load()
    
    for d in docs:
        d.metadata.update({"source_file": file.filename, "file_type": "txt"})

    chunks = rag.split_documents(docs, 1000, 200)
    texts = [c.page_content for c in chunks]
    emb = rag.embedding_manager.generate_embeddings(texts)
    rag.vectorstore.add_documents(chunks, emb)

    return {"filename": file.filename, "chunks_added": len(chunks)}

@app.get("/healthz")
def healthz():
    return {"status": "ok"} 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

