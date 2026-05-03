import os
import shutil
from pathlib import Path
from typing import List

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.llms import ChatMessage
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# ---------- Load API Key ----------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ---------- LlamaIndex Settings ----------
Settings.llm = Groq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY
)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

# ---------- FastAPI App ----------
app = FastAPI(title="Recruitment Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Constants ----------
BACKEND_DATA_FOLDER = "./data"
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------- In-memory state ----------
state = {
    "base_index": None,   # silent background data
    "user_index": None,   # user uploaded files
    "chat_history": [],
    "loaded_files": [],
}


# ---------- Request/Response Models ----------
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]


# ---------- Helper: Load index from folder ----------
def load_index_from_folder(folder: str) -> VectorStoreIndex:
    reader = SimpleDirectoryReader(input_dir=folder, recursive=True)
    documents = reader.load_data()
    return VectorStoreIndex.from_documents(documents)


# ---------- Helper: Get best query engine ----------
def get_query_engine(user_only: bool = False):
    # If user uploaded files exist and question is about them
    if user_only and state["user_index"] is not None:
        return state["user_index"].as_query_engine(similarity_top_k=5)

    # If both exist, use user files (more relevant for recruitment)
    if state["user_index"] is not None:
        return state["user_index"].as_query_engine(similarity_top_k=5)

    # Fall back to background data silently
    if state["base_index"] is not None:
        return state["base_index"].as_query_engine(similarity_top_k=3)

    return None


# ---------- Startup: silently load background data ----------
@app.on_event("startup")
async def startup_event():
    try:
        if os.path.exists(BACKEND_DATA_FOLDER):
            state["base_index"] = load_index_from_folder(BACKEND_DATA_FOLDER)
            print("Background data loaded.")
        else:
            print("No background data folder found.")
    except Exception as e:
        print(f"Background data load failed: {e}")


# ══════════════════════════════════════
#               API ROUTES
# ══════════════════════════════════════

@app.get("/api/status")
def get_status():
    return {
        "loaded_files": state["loaded_files"],
        "index_ready": state["base_index"] is not None or state["user_index"] is not None,
    }


@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    allowed_extensions = [".pdf", ".docx", ".txt", ".csv", ".xlsx"]
    saved_files = []

    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{ext}' not allowed. Supported: {', '.join(allowed_extensions)}"
            )
        dest = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(dest, "wb") as f:
            f.write(await file.read())
        saved_files.append(file.filename)

    try:
        state["user_index"] = load_index_from_folder(UPLOAD_FOLDER)
        state["loaded_files"] = saved_files
        state["chat_history"] = []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index files: {str(e)}")

    return {
        "message": f"{len(saved_files)} file(s) indexed successfully.",
        "files": saved_files
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="API key not configured.")

    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    sources = []

    try:
        # Detect if question is about uploaded files
        upload_keywords = [
            "resume", "cv", "candidate", "applicant", "upload",
            "file", "match", "summarize", "profile", "document",
            "experience", "skills", "qualification", "job"
        ]
        is_upload_query = (
            any(word in user_message.lower() for word in upload_keywords)
            and state["user_index"] is not None
        )

        query_engine = get_query_engine(user_only=is_upload_query)

        if query_engine:
            response = query_engine.query(user_message)
            answer = str(response)

            if hasattr(response, "source_nodes"):
                seen = set()
                for node in response.source_nodes:
                    fname = node.metadata.get("file_name", "Document")
                    if fname not in seen:
                        sources.append(fname)
                        seen.add(fname)
        else:
            # No data at all — answer from LLM
            messages = [
                ChatMessage(role="system", content=(
                    "You are a professional recruitment assistant. "
                    "Answer questions accurately and concisely. "
                    "If you are unsure, say so clearly."
                )),
                ChatMessage(role="user", content=user_message),
            ]
            response = Settings.llm.chat(messages)
            answer = str(response.message.content)

        state["chat_history"].append({"role": "user", "content": user_message})
        state["chat_history"].append({"role": "assistant", "content": answer})

        return ChatResponse(answer=answer, sources=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.delete("/api/clear")
def clear_chat():
    state["chat_history"] = []
    return {"message": "Chat cleared."}


@app.delete("/api/uploads")
def clear_uploads():
    state["user_index"] = None
    state["loaded_files"] = []
    state["chat_history"] = []
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    return {"message": "Uploads cleared."}


# ---------- Serve frontend ----------
frontend_path = Path("../frontend")
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
