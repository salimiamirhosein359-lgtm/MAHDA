# AI Sentinel — ایجنت رصد و پژوهش هوش مصنوعی 🦅

رصد عقاب‌گونه همه‌چیز مرتبط با AI (مدیران، دولت‌مردان، نشریات معتبر، مقالات دانشگاهی، تقابل چین-آمریکا) + دستیار پژوهشی آنلاین با ساختار Perplexity.

## 🏗️ ساختار

```
مهدا/
├── backend/          # FastAPI + کالکتورها + پایپ‌لاین + پژوهش
├── docs/ARCHITECTURE.md
├── docker-compose.yml
└── .env.example
```

## 🚀 اجرا (Docker — پیشنهادی)

```bash
# ۱. تنظیمات را آماده کن
cp .env.example .env
# کلیدهای API خودت را در .env بگذار (OPENAI_API_KEY یا ...)

# ۲. بالا آوردن کل استک
docker compose up --build

# سرویس‌ها:
#   API:       http://localhost:8000        (مستندات: /docs)
#   SearXNG:   http://localhost:8080        (موتور جستجوی وب)
#   Postgres:  localhost:5432                (+ pgvector)
#   Worker:    زمان‌بند کالکتورها (هر ساعت)
```

## 🐍 اجرا بدون Docker (توسعه)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# نیاز به Postgres با pgvector:
#   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=x pgvector/pgvector:pg16

# تنظیم .env (از .env.example کپی کن، POSTGRES_HOST=localhost)
copy ..\.env.example .env

# ایجاد جداول + منابع اولیه + اجرای زمان‌بند:
python -m app.scheduler

# در ترمینال جدا — اجرای API:
uvicorn app.main:app --reload
```

## 📡 API اصلی

| Endpoint | کار |
|---|---|
| `GET /api/v1/items` | فید رصد — فیلتر: category, camp, min_score, days |
| `GET /api/v1/rivalry` | نمای تقابل چین-آمریکا (دو ستون) |
| `GET /api/v1/trends` | کلیدواژه‌های داغ + momentum |
| `GET /api/v1/bulletins` | بولتن‌های تولیدی |
| `GET /api/v1/alerts` | هشدارهای داشبورد |
| `POST /api/v1/ask` | سؤال → پاسخ از حافظه (RAG) با ارجاع [n] |
| `POST /api/v1/ask` `{online:true}` | سؤال → جستجوی زنده وب (Perplexity-style) |
| `POST /api/v1/research` | پژوهش عمیق تکراری (background) |
| `POST /api/v1/files` | آپلود PDF/Word/عکس/صوت |
| `POST /api/v1/watch` | افزودن موضوع/شخص به پایش |
| `GET /api/v1/library` | کتابخانه شخصی |

مستندات کامل تعاملی: `http://localhost:8000/docs`

## 🧪 تست

```bash
cd backend
pytest
```

## ⚙️ LLM

از طریق LiteLLM — در `.env`:
- ابری: `LLM_MODEL=gpt-4o-mini` + کلید API
- محلی: `LLM_MODEL=ollama/qwen2.5` (Ollama روی `localhost:11434`)
- fallback خودکار: اگر مدل اصلی خطا داد، مدل دوم امتحان می‌شود

## 🔍 موتور جستجوی وب

پیش‌فرض SearXNG (رایگان، داخل docker-compose). جایگزین: `WEB_SEARCH_PROVIDER=tavily` یا `brave` + کلید.
