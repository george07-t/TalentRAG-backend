# TalentRAG Backend - Django REST API

AI-powered resume screening system with RAG (Retrieval-Augmented Generation) using OpenAI embeddings.

## Features
- JWT Authentication
- PDF/TXT Resume Parsing
- OpenAI Embeddings & RAG
- PostgreSQL Database
- REST API with Django REST Framework

## Local Development

### Prerequisites
- Python 3.9+
- PostgreSQL (or use SQLite for development)

### Setup

1. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Variables**

Create `.env` file:
```env
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_CHAT_MODEL=gpt-4o-mini
DATABASE_URL=postgresql://user:password@localhost:5432/talentrag_db
SECRET_KEY=your-django-secret-key
DEBUG=True
```

4. **Run Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create Superuser (Optional)**
```bash
python manage.py createsuperuser
```

6. **Run Server**
```bash
python manage.py runserver
```

API available at: `http://localhost:8000/api/`

## Deployment to Render

### Step 1: Prepare Repository
1. Push your code to GitHub
2. Ensure `.env` is in `.gitignore`
3. Commit `requirements.txt`, `build.sh`, and `render.yaml`

### Step 2: Setup Render PostgreSQL
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `talentrag-db`
   - **Database**: `talentrag_db`
   - **User**: (auto-generated)
   - **Region**: Choose closest to you
   - **Plan**: Free
4. Click **Create Database**
5. Copy the **Internal Database URL** (starts with `postgresql://`)

### Step 3: Deploy Backend
1. In Render Dashboard, click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `talentrag-backend`
   - **Root Directory**: `backend` (if in subdirectory)
   - **Environment**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: Free

### Step 4: Environment Variables
In Render Web Service settings, add these environment variables:

```
DATABASE_URL = <paste your Internal Database URL from PostgreSQL instance>
OPENAI_API_KEY = sk-proj-your-openai-api-key
OPENAI_CHAT_MODEL = gpt-4o-mini
SECRET_KEY = <generate a long random string>
DEBUG = False
ALLOWED_HOSTS = .render.com
PYTHON_VERSION = 3.9.0
```

### Step 5: Deploy
1. Click **Create Web Service**
2. Render will automatically:
   - Run `build.sh` (install deps, collectstatic, migrate)
   - Start gunicorn server
3. Wait 5-10 minutes for first deployment
4. Your API will be live at: `https://talentrag-backend.onrender.com`

### Step 6: Verify Deployment
Test endpoints:
- Health: `https://your-app.onrender.com/api/`
- Register: `POST https://your-app.onrender.com/api/auth/register/`
- Login: `POST https://your-app.onrender.com/api/auth/token/`

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Create account
- `POST /api/auth/token/` - Login (get JWT)
- `POST /api/auth/token/refresh/` - Refresh JWT

### Resume Analysis
- `POST /api/upload/` - Upload resume + job description (requires auth)
- `GET /api/session/<id>/analysis/` - Get analysis results
- `POST /api/session/<id>/chat/` - Ask questions (RAG)
- `GET /api/session/<id>/chat/` - Get chat history

## Troubleshooting

### Cold Start (Free Tier)
Render free tier spins down after 15 minutes of inactivity. First request may take 50-60 seconds.

### Database Connection Issues
- Verify `DATABASE_URL` is the **Internal** URL (not External)
- Check PostgreSQL instance is running
- Ensure database exists and migrations ran

### OpenAI Errors
- Verify `OPENAI_API_KEY` is set correctly
- Check API key has credits/billing enabled
- Model must be `gpt-4o-mini` or `gpt-3.5-turbo`

### Static Files Not Loading
- Run `python manage.py collectstatic` locally to verify
- Check `build.sh` runs collectstatic
- Verify `whitenoise` is in `MIDDLEWARE`

## Tech Stack
- Django 5.2.8
- Django REST Framework 3.16.1
- PostgreSQL + psycopg2-binary
- OpenAI API (embeddings + chat)
- JWT Authentication (simplejwt)
- WhiteNoise (static files)
- Gunicorn (WSGI server)

## License
MIT
