# ⚡ AI Development System - Шпаргалка

## 🚀 Быстрый старт (30 секунд)

```bash
python3 scripts/smoke_test.py && python3 api/server.py
```

Открой: http://localhost:8000/docs

---

## 🔐 JWT Authentication

### Регистрация
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@test.com","password":"password123"}'
```

### Вход
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user@test.com","password":"password123"}'
```

### Использование токена
```bash
TOKEN="your-jwt-token-here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/auth/me
```

---

## 💬 Chat Endpoints

### Простой запрос
```bash
curl -X POST http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Напиши функцию для сортировки",
    "task_type": "code",
    "complexity": 5,
    "budget": "free"
  }'
```

### Streaming
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Объясни JWT",
    "task_type": "chat"
  }'
```

---

## 📊 Stats & Health

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Статистика
```bash
curl http://localhost:8000/api/stats
```

### Рейтинги моделей
```bash
curl http://localhost:8000/api/rankings
curl http://localhost:8000/api/rankings/coding
```

---

## 🗂️ Sessions

### Создать сессию
```bash
curl -X POST http://localhost:8000/api/sessions/create
```

### Получить сообщения
```bash
curl http://localhost:8000/api/sessions/{session_id}/messages
```

---

## 🔧 Управление

### Обновить рейтинги
```bash
python3 scripts/update_rankings.py --days 7
```

### Генерировать отчет
```bash
python3 scripts/generate_report.py --days 7
```

### Экспорт истории
```bash
curl http://localhost:8000/api/history/export?format=json -o history.json
```

---

## 🧪 Тестирование

### Smoke test
```bash
python3 scripts/smoke_test.py
```

### Тест всех auth endpoints
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"test123456"}'

# Login  
curl -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"test123456"}'

# Get user (замени TOKEN)
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/auth/me
```

---

## 🐛 Troubleshooting

### Сервер не стартует
```bash
lsof -ti:8000 | xargs kill -9
python3 api/server.py
```

### Database locked
```bash
pkill -f "python3 api/server.py"
rm -f data/history.db-journal
python3 api/server.py
```

### Проверить логи
```bash
tail -f /tmp/server.log
```

### Проверить environment
```bash
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); \
  print('SECRET_KEY:', 'SET' if os.getenv('SECRET_KEY') else 'NOT SET'); \
  print('GEMINI_API_KEY:', 'SET' if os.getenv('GEMINI_API_KEY') else 'NOT SET')"
```

---

## 📦 Environment Variables

```bash
SECRET_KEY=                    # Генерируй: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_EXPIRATION_HOURS=24        # Время жизни токена
GEMINI_API_KEY=                # https://ai.google.dev/
GROK_API_KEY=                  # https://x.ai/
OPENROUTER_API_KEY=            # https://openrouter.ai/
ANTHROPIC_API_KEY=             # https://console.anthropic.com/
OPENAI_API_KEY=                # https://platform.openai.com/
```

---

## 🎯 Task Types

- `architecture` - Проектирование систем
- `code` - Генерация кода
- `review` - Код-ревью
- `test` - Написание тестов
- `devops` - DevOps задачи
- `research` - Исследования
- `chat` - Обычный чат
- `general` - Общие вопросы

---

## 💰 Budget Options

- `free` - Бесплатные модели (Gemini, Ollama)
- `cheap` - Дешевые модели (DeepSeek, ~$0.0001/1K tokens)
- `medium` - Средние модели (GPT-4, ~$0.01/1K tokens)
- `expensive` - Топовые модели (Claude Opus, ~$0.03/1K tokens)

---

## 🔑 Полезные команды

```bash
# Узнать версию Python
python3 --version

# Установить зависимости
pip install -r requirements.txt --break-system-packages

# Проверить установленные пакеты
pip list | grep -E "fastapi|bcrypt|jwt|pydantic"

# Запустить в фоне
nohup python3 api/server.py > /tmp/server.log 2>&1 &

# Проверить процессы на порту 8000
lsof -ti:8000

# Убить все процессы Python
pkill -f python3
```

---

## 📚 Документация

- Full Docs: [README.md](README.md)
- Quick Start: [QUICKSTART.md](QUICKSTART.md)
- Deployment: [DEPLOY.md](DEPLOY.md)
- Completion: [FINAL_SUMMARY.md](FINAL_SUMMARY.md)
- API Docs: http://localhost:8000/docs

---

**Быстрая помощь:**
- Не работает? → `python3 scripts/smoke_test.py`
- Нужен токен? → `/api/auth/login`
- Документация API? → `/docs`
- Health check? → `/api/health`

