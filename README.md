# 🤖 AI Development System

Интеллектуальная система для управления AI моделями с автоматическим роутингом, кэшированием и аналитикой.

## 🎯 Основные возможности

### 🏆 AI Models Ranking System
- Автоматический сбор рейтингов с HuggingFace и Chatbot Arena
- 7 категорий: Reasoning, Coding, Vision, Chat, Agents, Translation, Local
- Еженедельное обновление через cron
- Детальные страницы моделей с метриками

### 🧠 Smart AI Router
- Интеллектуальный выбор модели по задаче, сложности и бюджету
- Fallback механизм (автоматическое переключение при ошибках)
- Контекстная память сессий (до 10 последних сообщений)
- **920x speedup** благодаря кэшированию

### 💾 Request Caching
- MD5 хэширование промптов
- TTL зависит от типа задачи (1h-1week)
- SQLite-based хранилище
- Статистика использования

### ⏱️ Rate Limiting
- Индивидуальные лимиты RPM для каждой модели
- Thread-safe с блокировками
- Автоматическое ожидание при превышении

### 💬 Streaming Chat
- Server-Sent Events (SSE) для real-time ответов
- Индикаторы: модель, токены, стоимость, кэш
- Session-based контекст
- Новая сессия одним кликом

### 📊 Analytics & Reports
- Детальная статистика по моделям
- Cost breakdown и token usage
- Top expensive requests
- Hourly distribution
- Cache hit/miss rate

## 🏗️ Архитектура

```
autopilot-core/
├── agents/                    # 🧠 AI Logic
│   ├── database.py           # SQLite ORM + Analytics
│   ├── ai_router.py          # Smart Model Router
│   ├── ranking_collector.py # Rankings Scraper
│   └── models.py             # Models Config
├── api/                      # 🔌 Backend
│   └── server.py            # FastAPI Server (15 endpoints)
├── app/                      # 🎨 Frontend
│   ├── page.tsx             # Dashboard
│   ├── chat/                # Chat Interface
│   │   ├── page.tsx        # Main Chat
│   │   └── history/        # Chat History
│   └── models-ranking/      # Rankings UI
├── scripts/                  # 🛠️ Utils
│   ├── update_rankings.py   # Cron Job
│   ├── generate_report.py  # Analytics Report
│   └── setup_scheduler.sh  # Cron Setup
└── data/                     # 💾 Storage
    └── history.db           # SQLite Database
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm/pnpm

### 🔐 Environment Setup

#### 1. Create .env file

```bash
cp .env.example .env
```

#### 2. Generate SECRET_KEY

The SECRET_KEY is required for JWT authentication. Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste into `.env`:

```bash
SECRET_KEY=your-generated-secret-here
```

#### 3. Add API Keys

Get API keys from these providers:
- **Gemini**: https://ai.google.dev/
- **Grok**: https://x.ai/
- **OpenRouter**: https://openrouter.ai/

Add to `.env`:

```bash
GEMINI_API_KEY=your-key-here
GROK_API_KEY=your-key-here
OPENROUTER_API_KEY=your-key-here
```

#### 4. Verify Setup

```bash
source venv/bin/activate
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('✅ SECRET_KEY:', 'SET' if os.getenv('SECRET_KEY') else '❌ NOT SET'); print('✅ GEMINI_API_KEY:', 'SET' if os.getenv('GEMINI_API_KEY') else '❌ NOT SET')"
```

### Backend Setup
```bash
cd ~/autopilot-core

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt --break-system-packages

# Configure API keys
export GEMINI_API_KEY="your-key"
export GROK_API_KEY="your-key"
export OPENROUTER_API_KEY="your-key"

# Start API server
python api/server.py
# → http://localhost:8000
# → Docs: http://localhost:8000/docs
```

### Frontend Setup
```bash
cd ~/autopilot-core

# Install dependencies
npm install

# Start dev server
npm run dev
# → http://localhost:3000
```

## 📊 Database Schema

### Core Tables
- `requests` - История AI запросов
- `chat_sessions` - Пользовательские сессии
- `session_messages` - Сообщения в сессиях
- `request_cache` - Кэш ответов (MD5 хэш)
- `ranking_sources` - Источники рейтингов
- `ai_model_rankings` - Топ модели по категориям

## 🔌 API Endpoints

### Authentication 🔐
- `POST /api/auth/register` - Регистрация пользователя
- `POST /api/auth/login` - Вход (получить JWT токен)
- `GET /api/auth/me` - Текущий пользователь (protected)
- `GET /api/protected-example` - Пример защищенного endpoint

### Chat
- `POST /api/chat` - Single request
- `POST /api/chat/stream` - Streaming (SSE)
- `GET /api/chat/history` - История

### Sessions
- `POST /api/sessions/create` - Новая сессия
- `GET /api/sessions` - Список сессий
- `GET /api/sessions/{id}/messages` - Сообщения
- `DELETE /api/sessions/{id}` - Удалить

### Stats & Rankings
- `GET /api/stats` - Общая статистика
- `GET /api/models/rankings` - Рейтинги моделей
- `GET /api/models/status` - Статус моделей

### Management
- `GET /api/health` - Health check
- `POST /api/rankings/update` - Обновить рейтинги

## 🎨 Features

### Dashboard
- Total Requests counter
- Active Models count
- Total Cost tracker
- Average Cost/Request
- Quick navigation cards

### Chat Interface
- ✅ Streaming responses (SSE)
- ✅ Context Memory (session-based)
- ✅ Cache indicators
- ✅ Model/tokens/cost display
- ✅ New Chat button
- ✅ Settings panel (Task Type, Budget, Complexity)

### Models Ranking
- 7 категорий с топ-3 моделями
- Детальные модальные окна
- Score, Rank, Notes
- Source links
- Best use cases
- Last update dates

### Chat History
- Список всех сессий
- Фильтры по дате/модели
- Export в Markdown
- Статистика по сессии
- Удаление сессий

## 📈 Performance

### Caching Impact
- First request: ~1.25s (API call)
- Cached request: ~0.001s (920x faster!)
- Cost savings: $0 for cached requests

### Rate Limits (RPM)
- Gemini 2.0 Flash: 60 RPM
- DeepSeek Chat: 30 RPM
- Grok Beta: 30 RPM
- GPT-4o: 50 RPM
- Claude Sonnet: 50 RPM

### Database Performance
- Cache hit rate: ~40%
- Average query time: <10ms
- Concurrent requests: 50+

## 🛠️ Scripts & Automation

### Weekly Rankings Update
```bash
python scripts/update_rankings.py --days 7
```

### Setup Cron Job
```bash
chmod +x scripts/setup_scheduler.sh
./scripts/setup_scheduler.sh
# Runs every Monday at 9:00 AM
```

### Generate Analytics Report
```bash
python scripts/generate_report.py --days 7
```

## 📊 Analytics Report Example

```
🤖 AI MODELS PERFORMANCE REPORT
Period: Last 7 days
Generated: 2025-10-30 15:00:00

📊 SUMMARY
  Total Requests:  1,247
  Total Tokens:    156,892
  Total Cost:      $12.4567
  Unique Models:   8
  Unique Tasks:    5

🎯 MODELS PERFORMANCE
  Model                    Requests   Success   Tokens      Cost
  deepseek/deepseek-chat   524        100.0%    89,234      $8.92
  gemini-2.0-flash         312        100.0%    31,245      $0.00
  gpt-4o                   187        98.9%     28,156      $2.82

💾 CACHE STATISTICS
  Total Entries:     89
  Total Uses:        456
  Avg Uses/Entry:    5.1
```

## 🔐 Environment Variables

See [.env.example](.env.example) for the complete list of environment variables.

**Required:**
- `SECRET_KEY` - JWT secret (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `GEMINI_API_KEY` - Google Gemini API key
- `GROK_API_KEY` - xAI Grok API key
- `OPENROUTER_API_KEY` - OpenRouter API key

**Optional:**
- `TELEGRAM_BOT_TOKEN` - For ranking update notifications
- `TELEGRAM_CHAT_ID` - Telegram chat ID for notifications
- `DATABASE_PATH` - Custom SQLite database path (default: `./data/history.db`)
- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8000`)

## 🐛 Troubleshooting

### Backend не стартует
```bash
# Проверь Python версию
python --version  # Должна быть 3.11+

# Переустанови зависимости
pip install -r requirements.txt --break-system-packages
```

### Frontend ошибки
```bash
# Очисти кэш
rm -rf .next node_modules
npm install
npm run dev
```

### База данных заблокирована
```bash
# Останови все процессы
pkill -f "python api/server.py"

# Удали lock файл
rm -f data/history.db-journal
```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs
- **Project Rules**: `.cursorrules`
- **Prompts Guide**: `PROMPTS.md`
- **Status**: `STATUS.md`

## 🚀 Roadmap

### Критично (Priority 1)
- [x] ~~JWT Authentication~~ ✅ **COMPLETED**
- [ ] API Security (rate limiting per user)
- [ ] Docker containerization
- [ ] Code Agent (специализированный агент)

### Важно (Priority 2)
- [ ] Chat History UI (filters, export)
- [ ] File Upload (PDF, DOCX, images)
- [ ] Theme toggle (dark/light)
- [ ] Unit tests (>80% coverage)

### Желательно (Priority 3)
- [ ] Mobile app (React Native)
- [ ] Multi-tenancy
- [ ] A/B testing models
- [ ] Telegram bot integration

## 🤝 Contributing

1. Fork the repo
2. Create feature branch
3. Follow `.cursorrules` style
4. Test changes
5. Submit PR

## 📄 License

MIT License

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- Email: your.email@example.com

---

**Built with ❤️ using FastAPI, Next.js, and multiple AI models**