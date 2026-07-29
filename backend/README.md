# Recruitment Assistant Chatbot

An AI-powered recruitment chatbot that helps recruiters analyze resumes, job descriptions, and answer HR-related questions using RAG (Retrieval Augmented Generation) architecture.

---

## Features

- Upload resumes, job descriptions, PDFs, CSVs, DOCX files
- AI-powered answers based on uploaded document content
- Smart routing between policy questions and resume questions
- Clean Blue and White corporate UI
- Real-time chat with timestamps
- Quick action buttons (Summarize, Match Resume, List Candidates)
- Background company data loaded silently at startup
- File upload with drag and drop support

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | FastAPI (Python) |
| AI Model | Groq API (Llama 3.1-8b-instant) |
| Embeddings | HuggingFace (BAAI/bge-small-en-v1.5) |
| Document Engine | LlamaIndex |
| Server | Uvicorn |

---

## Project Structure

```
chatbot/
├── backend/
│   ├── data/               ← background company documents
│   │   ├── hr_policy/
│   │   ├── it_policy/
│   │   ├── leave_policy/
│   │   └── code_of_conduct/
│   ├── uploads/            ← user uploaded files (auto created)
│   ├── main.py             ← FastAPI backend
│   ├── requirements.txt    ← Python dependencies
│   └── Procfile            ← deployment config
├── frontend/
│   └── index.html          ← complete UI
└── .gitignore
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- pip
- A free Groq API key from https://console.groq.com

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/Dinesh0205-code/Chatbot_intern.git
cd Chatbot_intern
```

**2. Create virtual environment**
```bash
cd backend
python -m venv .venv
```

**3. Activate virtual environment**
```bash
# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

**4. Install dependencies**
```bash
pip install -r requirements.txt
```

**5. Create `.env` file inside `backend/` folder**
```
GROQ_API_KEY=your_groq_api_key_here
```

**6. Get free Groq API key**
- Go to → https://console.groq.com
- Sign up → Create API Key → Copy it
- Paste into `backend/.env`

---

## Running the Project

**Start the backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO: Uvicorn running on http://127.0.0.1:8000
Background data loaded.
```

**Open the frontend:**
- Open `frontend/index.html` in your browser
- Top right should show **Ready** in green

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/status` | GET | Check server and index status |
| `/api/upload` | POST | Upload and index documents |
| `/api/chat` | POST | Send message and get AI response |
| `/api/clear` | DELETE | Clear chat history |
| `/api/uploads` | DELETE | Remove uploaded files |

---

## How It Works

```
User uploads document
        ↓
Document split into chunks (512 tokens)
        ↓
HuggingFace converts chunks to vectors
        ↓
Vectors stored in VectorStoreIndex
        ↓
User asks a question
        ↓
Smart router detects question type
        ↓
Policy question → searches ./data folder
Resume question → searches uploaded file
        ↓
Relevant chunks sent to Groq AI
        ↓
AI generates accurate answer
        ↓
Answer shown in chat UI
```

---

## Supported File Types

| Format | Extension |
|--------|-----------|
| PDF | .pdf |
| Word Document | .docx |
| Text File | .txt |
| CSV | .csv |
| Excel | .xlsx |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key from console.groq.com |

---

## Common Errors

| Error | Fix |
|-------|-----|
| `API key not configured` | Add `GROQ_API_KEY` to `backend/.env` |
| `Backend Offline` | Make sure uvicorn is running |
| `Module not found` | Run `pip install -r requirements.txt` |
| `.venv not found` | Run `python -m venv .venv` |

---

## Security

- API keys stored in `.env` file — never committed to GitHub
- `.gitignore` configured to exclude `.env`, `.venv`, `__pycache__`, `uploads/`
- File type validation on every upload

---

## Deployment

### Backend — Koyeb (Free)
- Go to → https://koyeb.com
- Connect GitHub repo
- Root directory → `backend`
- Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Add `GROQ_API_KEY` in environment variables

### Frontend — Netlify (Free)
- Go to → https://netlify.com
- Drag and drop `frontend/` folder
- Done

---

## License

This project was built during an internship at ProEduvate.

---

## Author

**Dinesh** — Developer Intern, ProEduvate  
GitHub: [@Dinesh0205-code](https://github.com/Dinesh0205-code)