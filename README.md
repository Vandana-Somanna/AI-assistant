#  AI Support Assistant with RAG + Tool Integration

##  Overview
This project is an AI-powered support assistant that can:
- Answer user queries using **RAG (Retrieval-Augmented Generation)**
- Fetch **order status**
- Create **support tickets**
- Maintain **session memory**
- Log **tool usage for debugging and monitoring**

The system combines:
- LLM (Groq - LLaMA 3.1)
- Custom tools (order + ticket system)
- Vector database (ChromaDB)
- FastAPI backend

---

##  Setup Instructions


### Clone the repository 
git clone <your-repo-link>
cd project

### Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows

### Install dependencies
pip install -r requirements.txt

### Set environment variables
Create a .env file:
API=your_groq_api_key

### Run the application
uvicorn main:app --reload --port 8000

## Project Structure
```
project/
│
├── data/
│   ├── orders.json        # Order database
│   ├── tickets.json       # Ticket storage
│
├── docs/                  # Knowledge base (RAG)
│   ├── faq.txt
│   ├── return_policy.txt
│   ├── shipping_info.txt
│
├── rag/                   # RAG pipeline
├── agent/                 # Chat logic + orchestration
├── tools/                 # Custom tools                  
│
└── main.py                # Entry point(FAST API)

```
## Architecture Explanation
```
1. User Interaction (FastAPI)
  User sends query via /chat endpoint
  Request is handled in main.py
  Logs are generated (query, response, tools used)

2. Agent Layer (Core Brain)
  Handled in agent.py
  Responsibilities:
    Intent detection (order / policy / ticket)
    Session memory management
    Tool orchestration
    RAG fallback
Flow:
User Query
   ↓
Intent Detection
   ↓
Route:
   → Tool (order/ticket)
   → RAG (docs)
   ↓
Final Response

3. Tools Layer
  Defined in mytools.py
  Tools:
    check_order_status
    create_ticket
  Features:
    Validates order ID
    Prevents duplicate tickets
    Reads/writes JSON data

4. RAG Pipeline
  Implemented in rag.py
  Steps:
    Load documents from /docs
    Split into chunks
    Generate embeddings (SentenceTransformer)
    Store in ChromaDB
    Retrieve relevant chunks during query
Retrieval Flow:
Query → Embedding → Vector Search → Top-K Docs → LLM Answer

5. LLM Layer
  Model: LLaMA 3.1 (Groq API)
  Used for:
    Answer generation (RAG)
    Context-based responses

6. Logging System
  Logs stored in server.log
  Tracks:
    User queries
    Responses
    Tools used
example:
[USER QUERY]: Where is my order ORD123?
[TOOLS USED]: ['check_order_status']
[RESPONSE]: Order is delivered
```
##Features:
```
-> Multi-turn conversation memory
-> Tool-based execution
-> RAG-based knowledge retrieval
-> Duplicate ticket prevention
-> Clean logging for debugging
-> FastAPI backend
