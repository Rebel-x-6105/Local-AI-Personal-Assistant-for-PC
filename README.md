# J.A.R.V.I.S. (Just A Rather Very Intelligent System)

Welcome to J.A.R.V.I.S., an Iron Man-inspired desktop assistant. The project is designed using clean architecture principles and is built incrementally in layers.

---

## 🌟 Project Layers Overview

### ✔ Layer 1: AI Brain
Operates as a modular, swappable LLM core (supporting OpenAI, Gemini, Groq) with context retention and dynamic context budgeting.

### ✔ Layer 2: Voice Input & Output
Enables vocal interactivity:
*   **Speech-to-Text (STT)**: Capture via `sounddevice` input streams with dynamic Root Mean Square (RMS) Voice Activity Detection (VAD). Transcribes using Google Web Speech API.
*   **Text-to-Speech (TTS)**: High-quality natural voice synthesis via Microsoft Edge natural voices (`edge-tts`). Audio playback uses Windows MCI (`winmm.dll`) for thread-blocking sync. Offline SAPI5 speaker fallback via `pyttsx3`.
*   **Real-time Streaming TTS**: Parses sentence boundaries during LLM streaming and plays them in real-time, reducing vocal latency to less than 1.0 second.

### ✔ Layer 3: Persistent Memory
Provides long-term memory across session restarts:
*   **Relational Storage**: SQLite + SQLAlchemy ORM for structured profile facts, preferences, projects, goals, and tasks.
*   **Vector Database**: ChromaDB + local `SentenceTransformers` (`all-MiniLM-L6-v2`) for semantic similarity retrieval and cosine-distance ranking.
*   **REST API**: FastAPI application exposing endpoints for complete CRUD operations on JARVIS's memory.

### ✔ Layer 4: Web Search & Knowledge Retrieval (Current)
Equips J.A.R.V.I.S. with real-time access to the internet:
*   **Intent Routing**: Dynamically classifies user statements to see if search is needed, chooses the appropriate category, and optimizes keywords using the LLM.
*   **Relational Caching**: Stores query MD5 hashes and results in the SQLite `search_cache` table. Records automatically expire after a configurable TTL (default 1 hour) to limit API usage.
*   **Web Scrapers**: Crawls webpages asynchronously using `httpx` and extracts clean, readable content using `trafilatura` (falling back to `BeautifulSoup4`). Large page contents are automatically summarized using the LLM.
*   **Diverse Search Providers**:
    *   *General & News*: Tavily Search REST API (requires key).
    *   *GitHub*: Keyless public GitHub repositories API.
    *   *Research Papers*: Keyless public arXiv XML API.
    *   *Weather*: Keyless OSM Nominatim geocoding + WMO Open-Meteo forecast.
    *   *Finance*: Keyless Yahoo Finance ticker suggestions + charts quote API.
    *   *YouTube*: Restricted Tavily search to `site:youtube.com` for watch URLs.

---

## 📂 Folder Structure

```text
Jarvis/
├── main.py                # Console IO loop & Voice Controller entry point
├── requirements.txt      # Project dependencies
├── README.md             # Project documentation
├── .env.example          # Environment variables template
├── .gitignore            # Version control exclusions
│
├── app/
│   ├── __init__.py       # Package initializer
│   ├── assistant.py      # Core orchestrator integrating Brain, Memory, and Search
│   ├── config.py         # App configurations validator (Pydantic v2)
│   ├── prompts.py        # System instruction sets and personality prompts
│   ├── llm.py            # decoupled LLM Client and provider bindings
│   ├── conversation.py   # Active session log manager and context pruner
│   ├── logger.py         # Standardized file logging configurations
│   ├── startup.py        # Simulated diagnostics startup sequences
│   ├── api.py            # FastAPI REST API controller
│   │
│   ├── memory/           # Memory Package (Layer 3)
│   │   ├── __init__.py   # Exposes package managers
│   │   ├── database.py   # SQLAlchemy Engine and connection setups
│   │   ├── models.py     # SQLAlchemy ORM models (users, summaries, cache, etc.)
│   │   ├── vector_store.py# ChromaDB client & SentenceTransformers embeddings
│   │   ├── manager.py    # Operations manager & LLM interaction evaluator
│   │   ├── retriever.py  # Semantic context RAG selector & formatter
│   │   └── summarizer.py # Conversational session compressor
│   │
│   └── search/           # Web Search Package (Layer 4)
│       ├── __init__.py   # Exposes retrieval manager
│       ├── manager.py    # Intent router, crawlers, and context formattings
│       ├── cache.py      # SQLite cache CRUD manager
│       ├── parser.py     # Web content extractor (trafilatura + BeautifulSoup4)
│       └── providers/    # Specific query search connectors
│           ├── tavily.py # Tavily Web search (requires API key)
│           ├── github.py # GitHub REST API (keyless)
│           ├── papers.py # arXiv XML API (keyless)
│           ├── weather.py# Nominatim + Open-Meteo forecast (keyless)
│           ├── finance.py# Yahoo Finance stock quotes (keyless)
│           └── youtube.py# Site-restricted watch links selector
│
├── memory/               # Databases output directory
│   ├── jarvis.db         # SQLite persistent database file
│   ├── chroma_db/        # ChromaDB persistent collection files
│   └── history.json      # Last session raw serialization output
│
├── logs/                 # Folder for runtime log files
├── tests/                # Automated unit tests (conversation, memory, search)
└── venv/                 # Python local virtual environment
```

---

## 💾 SQLite Database Schemas

The relational engine operates in `memory/jarvis.db` containing the following schemas:

*   **`users`**: User profile parameters (`name`, `occupation`, `college`, `degree`, `skills`, `interests`, `location`).
*   **`preferences`**: System and user key-value preference flags (`voice`, `dark_mode`, etc.).
*   **`projects`**: Software development projects progress and tech stacks (`name`, `status`, `completed_modules`, `pending_modules`, `tech_stack`, `architecture`, `goals`, `progress`).
*   **`goals`**: Long-term objectives (`title`, `description`, `status`, `target_date`).
*   **`tasks`**: Short-term todo lists (`title`, `status`, `deadline`, `notes`).
*   **`memories`**: Miscellaneous facts and learned insights (`content`, `category`, `created_at`).
*   **`conversation_summaries`**: History of session summaries (`summary`, `timestamp`).
*   **`search_cache`**: Web search caches (`query_key`, `results_json`, `created_at`).

---

## 🚀 Installation & Setup

### 1. Set Up Environment
Activate your virtual environment and install the required modules:
```powershell
# Activate .venv
.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Verify your `.env` contains:
```env
# API Keys config
GEMINI_API_KEY=your-gemini-api-key
TAVILY_API_KEY=your-tavily-api-key

# Memory Configurations (Layer 3)
DB_PATH=memory/jarvis.db
CHROMA_DB_PATH=memory/chroma_db
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2

# Web Search Configurations (Layer 4)
SEARCH_CACHE_TTL_SEC=3600
SEARCH_TIMEOUT_SEC=10
MAX_SEARCH_RESULTS=5
```

---

## 🏃 Running the Application

### Option A: Speak with JARVIS (Terminal Loop)
Run the console dialogue loop:
```bash
python main.py
```
JARVIS will analyze your input. If you ask for current weather, stocks, repositories, research papers, or current news, JARVIS will execute the search pipeline in the background and reply using cited details!

### Option B: Memory Management (FastAPI REST API)
Expose the FastAPI REST server in the background:
```bash
uvicorn app.api:app --port 8000 --reload
```
Open your browser at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to access the Swagger UI.

---

## 🧪 Testing

To run the automated tests verifying conversation prunings, SQLite database CRUD, ChromaDB semantic search, conversation summaries, intent routing, keyless search API calls, and search caching:
```bash
python -m pytest
```
