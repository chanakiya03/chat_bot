# CollegeBot — Complete Setup Guide

## Project Structure
```
college_chat/
├── backend/          ← Django + Daphne (WebSocket server)
│   ├── data/         ← College JSON data files
│   ├── chatbot/      ← AI engine, models, consumers
│   └── manage.py
├── frontend/         ← Next.js 14 chat UI
├── requirements.txt  ← Python dependencies
└── run_all.bat       ← One-click start (Windows)
```

---

## Prerequisites

Install these on the new device before anything else:

| Tool | Version | Download |
|:---|:---|:---|
| **Python** | 3.10+ | https://python.org/downloads |
| **Node.js** | 18+ | https://nodejs.org |
| **Git** *(optional)* | any | https://git-scm.com |

> [!IMPORTANT]
> During Python install, check **"Add Python to PATH"**.

---

## Step 1 — Copy the Source Code

Copy the entire `college_chat/` folder to the new device.
Place it anywhere, e.g. `D:\projects\college_chat\`

---

## Step 2 — Set Up Python Virtual Environment (Backend)

Open **Command Prompt** inside the `college_chat/` folder:

```cmd
cd D:\projects\college_chat
```

Create and activate virtual environment:
```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of the prompt.

---

## Step 3 — Install Python Dependencies

```cmd
pip install -r requirements.txt
```

This installs:
- Django, Django REST Framework, CORS Headers
- Channels + Daphne (WebSocket)
- sentence-transformers (BERT AI model)
- scikit-learn, numpy
- groq, openai (AI API clients)

> [!NOTE]
> `sentence-transformers` will download the BERT model (~90MB) the first time the server starts. This is normal.

---

## Step 4 — Configure the API Key

Open `backend/college_chat_backend/settings.py` and find line 103:

```python
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', 'YOUR_KEY_HERE')
```

Replace `YOUR_KEY_HERE` with your Groq API key.

Get a free key at: https://console.groq.com

---

## Step 5 — Set Up the Database

```cmd
cd backend
python manage.py makemigrations
python manage.py migrate
```

Then load all college data into the database:
```cmd
python manage.py sync_data
```

Expected output:
```
✅ Synced: Madras Christian College (MCC)
✅ Synced: SSN College of Engineering
... (all colleges)
✅ Sync complete.
```

---

## Step 6 — Install Frontend Dependencies

Open a **new Command Prompt** (keep the backend one open):

```cmd
cd D:\projects\college_chat\frontend
npm install
```

---

## Step 7 — Run the Project

### Option A — One-Click Start (Recommended)

Double-click `run_all.bat` in the `college_chat/` folder.

This automatically:
1. Syncs database
2. Starts backend on http://localhost:8000
3. Starts frontend on http://localhost:3000

---

### Option B — Manual Start (Two Terminals)

**Terminal 1 — Backend:**
```cmd
cd D:\projects\college_chat\backend
..\venv\Scripts\python -m daphne -p 8000 college_chat_backend.asgi:application
```

**Terminal 2 — Frontend:**
```cmd
cd D:\projects\college_chat\frontend
npm run dev
```

---

## Step 8 — Open the App

Visit in your browser: **http://localhost:3000**

---

## Troubleshooting

| Problem | Fix |
|:---|:---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `No colleges in database` | Run `python manage.py sync_data` |
| `Port 8000 already in use` | Run `netstat -aon \| findstr :8000` then `taskkill /F /PID [number]` |
| `npm: command not found` | Install Node.js and restart terminal |
| `BERT model downloading...` | Wait ~2 min on first start, normal behavior |
| Slow first response | BERT loads on first request — subsequent responses are fast |

---

## What Files to Copy (Exclude These)

When copying to a new device, **exclude** these folders to save space:

```
college_chat/venv/          ← Recreate with pip install
college_chat/frontend/node_modules/   ← Recreate with npm install
college_chat/backend/db.sqlite3       ← Recreate with sync_data
college_chat/frontend/.next/          ← Auto-generated on npm run dev
```

Everything else must be copied.
