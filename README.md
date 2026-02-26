# 🎓 College Chatbot — Setup & Run Guide

A full-stack AI-powered college information chatbot built with Django (backend) and Next.js (frontend).

---

## 📋 Prerequisites

Make sure you have the following installed:

- **Python 3.10**
- **Node.js 18+**
- **npm** (comes with Node.js)

---

## 🔧 Backend Setup

### 1. Navigate to the backend folder
```cmd
cd D:\projects\college_chat\backend
```

### 2. Create a virtual environment
```cmd
python -m venv venv310
```

### 3. Activate the virtual environment
```cmd
venv310\Scripts\activate
```

### 4. Install Python dependencies
```cmd
pip install django djangorestframework django-channels daphne djangorestframework-simplejwt django-cors-headers groq sentence-transformers
```

### 5. Fix the migration history (run only once)
```cmd
python -c "import sqlite3; conn = sqlite3.connect('db.sqlite3'); cursor = conn.cursor(); cursor.execute(\"DELETE FROM django_migrations WHERE app='chatbot'\"); conn.commit(); conn.close(); print('Done')"
```

### 6. Run database migrations
```cmd
python manage.py migrate chatbot
python manage.py migrate
```

### 7. (Optional) Create an admin user
```cmd
python manage.py createsuperuser
```

### 8. Start the backend server
```cmd
python manage.py runserver
```

> ✅ Backend is running at: **http://127.0.0.1:8000**

---

## ⚛️ Frontend Setup

Open a **new terminal window**:

### 1. Navigate to the frontend folder
```cmd
cd D:\projects\college_chat\frontend
```

### 2. Install Node.js dependencies
```cmd
npm install
```

### 3. Start the development server
```cmd
npm run dev
```

> ✅ Frontend is running at: **http://localhost:3000**

---

## 🌐 Access the Application

| URL | Description |
|-----|-------------|
| `http://localhost:3000` | Main application |
| `http://localhost:3000/signup` | Register a new account |
| `http://localhost:3000/login` | Login to your account |
| `http://127.0.0.1:8000/api/` | Backend REST API |
| `http://127.0.0.1:8000/admin/` | Django Admin Panel |

---

## ⚡ Quick Start (All Commands)

```cmd
:: ── BACKEND ─────────────────────────────────────────────
cd D:\projects\college_chat\backend
python -m venv venv310
venv310\Scripts\activate
pip install django djangorestframework django-channels daphne djangorestframework-simplejwt django-cors-headers groq sentence-transformers
python -c "import sqlite3; conn = sqlite3.connect('db.sqlite3'); cursor = conn.cursor(); cursor.execute(\"DELETE FROM django_migrations WHERE app='chatbot'\"); conn.commit(); conn.close()"
python manage.py migrate chatbot
python manage.py migrate
python manage.py runserver

:: ── FRONTEND (open new terminal) ─────────────────────────
cd D:\projects\college_chat\frontend
npm install
npm run dev
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django, Django REST Framework, Daphne (ASGI) |
| Auth | JWT (djangorestframework-simplejwt) |
| AI / Chat | Groq LLM API, Sentence Transformers (BERT) |
| Database | SQLite |
| Frontend | Next.js 14, React 18 |
| Realtime | Django Channels (WebSocket) |

---

## 📁 Project Structure

```
college_chat/
├── backend/
│   ├── chatbot/          # Django app (models, views, engine)
│   ├── data/             # College JSON data files
│   ├── college_chat_backend/  # Django settings & URLs
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages (page.tsx, login, signup, chat)
│   │   └── hooks/        # Auth & WebSocket hooks
│   └── package.json
└── README.md
```

---

## ❓ Troubleshooting

| Problem | Fix |
|---------|-----|
| `no such table: chatbot_user` | Run Step 5 (fix migration history) then Step 6 again |
| `Module not found` error | Make sure `venv310` is activated |
| Frontend can't connect to backend | Make sure backend is running on port 8000 |
| `CORS error` in browser | Backend is already configured to allow `localhost:3000` |
