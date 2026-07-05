# ♻️ GreenBin Genius — AI Recycling Coordinator

GreenBin Genius is a state-of-the-art AI-powered recycling assistant and municipal rule coordinator. Built as a Capstone demonstration for the Kaggle Agentic AI course, the platform utilizes advanced LLM tool-calling, the Model Context Protocol (MCP), and human-in-the-loop security architectures to ensure safe, localized, and verifiable waste disposal.

---

## 🚀 Key Core Concepts Demonstrated

### 🤖 Concept 1: Agentic Orchestration (ADK)
The system leverages the official `google-genai` SDK with **Gemini 2.5 Flash** acting as an autonomous Coordinator. It dynamically processes multimodal user queries (text and images) to classify waste materials. Rather than replying with general web knowledge, the agent uses structured reasoning to decide when to call external local tools.

### 🔌 Concept 2: Model Context Protocol (MCP) Integration
A dedicated, local **FastMCP Server** (`mcp_server/server.py`) hosts municipal recycling regulations. 
- The coordinator agent acts as an **MCP Client**, initiating a standard JSON-RPC 2.0 stdio channel with the FastMCP Server.
- When a user asks about a material (e.g., plastics), the agent calls the `get_recycling_rules` tool.
- The server performs a fuzzy lookup in the local database (`municipal_rules.json`) and returns exact, local instructions—safely grounding the LLM in real-world facts.

### 🛡️ Concept 4: Human-in-the-Loop Triage & Security
Generative LLMs are prone to hallucinating or misclassifying hazardous waste. GreenBin Genius implements a strict **Zero-Trust Failsafe Pipeline**:
1. If the user asks about dangerous chemicals, battery disposals, or if the agent is uncertain, the model outputs `NEEDS_REVIEW`.
2. Additionally, if the Gemini API experiences network errors (e.g., `429 Rate Limit` or `503 Unavailable`), the system catches the exception immediately.
3. In either case, the query is quarantined inside a secure SQLite database (`greenbin_triage.db`).
4. The user is politely informed that the item is flagged, and administrators can review, edit, and resolve the item manually from the **Admin Triage Dashboard**.

---

## 🎨 Tech Stack & Visual Design

- **Backend**: FastAPI (Python) serving REST APIs and mounting static assets.
- **Database**: SQLite (SQLAlchemy ORM) for managing pending human-in-the-loop triage tasks.
- **AI Agent**: Gemini 2.5 Flash (`google-genai` SDK) + FastMCP Server (stdio transport).
- **Frontend**: A premium, modern, responsive glassmorphic SaaS interface built with vanilla HTML/CSS/JavaScript (utilizing Google Fonts `Inter` and Feather Icons).

---

## 📂 Project Structure

```text
greenbin_genius/
│
├── agents/
│   └── coordinator_agent.py   # Main agent logic (Gemini + MCP Client)
│
├── backend/
│   ├── main.py                # FastAPI Application Entrypoint
│   ├── database.py            # SQLite Connection and ORM Schemas
│   └── routers/
│       ├── chat.py            # Agent chat pipeline (handles ChatRequests)
│       └── admin.py           # Admin endpoints (fetch/resolve pending items)
│
├── mcp_server/
│   ├── server.py              # FastMCP Server exposing local tools
│   └── municipal_rules.json   # Local grounded database of municipal guidelines
│
├── frontend/                  # HTML, CSS, and JS web interfaces
│   ├── index.html             # Client-facing Chat Dashboard
│   ├── admin.html             # Admin Triage Dashboard
│   ├── styles.css             # Glassmorphic responsive design styles
│   ├── app.js                 # Chat event handling & Session storage persistence
│   └── admin.js               # Admin triage action handler
│
├── .env.example               # Example template for environmental variables
└── requirements.txt           # Main project dependency file
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API Key (Generate one [here](https://aistudio.google.com/))

### 2. Install Dependencies
Clone the repository and install the dependencies for the backend and the agents:
```bash
pip install -r backend/requirements.txt
pip install -r agents/requirements.txt
```

### 3. Configure Environments
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Start the Application
Run the FastAPI development server:
```bash
python -m backend.main
```
The server will boot up on `http://localhost:8000/`.

---

## 🖥️ How to Test & Demo

1. **Happy Path (Grounded MCP Advice)**:
   - Open `http://localhost:8000/` and send: *"How do I dispose of plastic containers?"*
   - The agent will trigger the MCP tool call, read `municipal_rules.json`, and tell you that *"Only plastics labeled #1 and #2 are accepted in the blue bin."*
2. **Persisted Sessions**:
   - Go to the **Admin Dashboard** via the sidebar, and click **Back to Chat**. Notice that your chat history is persisted using browser `sessionStorage`.
3. **Safety Fallback (Human Triage)**:
   - Ask: *"How do I throw away an old car battery?"*
   - The agent will flag it: *"This looks like it might be hazardous..."*
   - Visit the **Admin Triage Dashboard** at `http://localhost:8000/static/admin.html` to see the item, read the AI's draft notes, write a manual resolution, and click **Mark as Resolved**.
