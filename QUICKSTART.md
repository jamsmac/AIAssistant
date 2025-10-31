# ⚡ Quick Start Guide

## ⚙️ Первоначальная настройка

**Перед первым запуском выполни один раз:**

```bash
# 1. Создай .env файл
cp .env.example .env

# 2. Сгенерируй SECRET_KEY (скопируй вывод)
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 3. Добавь ключ в .env
# Открой .env и вставь:
# SECRET_KEY=твой-сгенерированный-ключ

# 4. Добавь API ключи в .env
# GEMINI_API_KEY=твой-ключ
# GROK_API_KEY=твой-ключ
# OPENROUTER_API_KEY=твой-ключ

# 5. Запусти тест
python scripts/smoke_test.py
```

**Где получить API ключи:**
- Gemini: https://ai.google.dev/
- Grok: https://x.ai/
- OpenRouter: https://openrouter.ai/

---

## 🚀 Запуск системы за 3 шага

### 1️⃣ Запустить инфраструктуру
```bash
cd ~/autopilot-core
./start.sh
```

### 2️⃣ Открыть 3 терминала и выполнить:

**Terminal 1 - API Server:**
```bash
cd ~/autopilot-core
source venv/bin/activate
python api/server.py
```

**Terminal 2 - Web UI:**
```bash
cd ~/autopilot-core/web-ui
npm run dev
```

**Terminal 3 - Telegram Bot (опционально):**
```bash
cd ~/autopilot-core
source venv/bin/activate
python scripts/telegram_bot.py
```

### 3️⃣ Открыть браузер
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

---

## 🔐 Аутентификация (JWT)

### Быстрый тест аутентификации

**1. Регистрация пользователя:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

**2. Вход и получение токена:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

**3. Проверка токена:**
```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Endpoints аутентификации
- `POST /api/auth/register` - Регистрация
- `POST /api/auth/login` - Вход (получить JWT)
- `GET /api/auth/me` - Текущий пользователь (требует токен)
- `GET /api/protected-example` - Пример защищенного endpoint

---

## 🛑 Остановка системы
```bash
cd ~/autopilot-core
./stop.sh
```

---

## 💾 Создать Backup
```bash
cd ~/autopilot-core
./scripts/backup.sh
```

Backup сохранится в: `~/autopilot-backups/`

---

## 📱 Telegram Бот

Найди бота в Telegram и отправь:
- `/start` - начало работы
- `/chat <вопрос>` - задать вопрос AI
- `/stats` - статистика
- `/models` - список моделей
- `/create <идея>` - создать проект

Или просто пиши сообщения напрямую!

---

## 📊 Структура проекта
```
~/autopilot-core/
├── start.sh              # Запуск системы
├── stop.sh               # Остановка системы
├── README.md             # Полная документация
├── QUICKSTART.md         # Этот файл
├── docker-compose.yml    # Docker контейнеры
├── .env                  # API ключи
├── agents/
│   └── ai_router.py      # AI роутер
├── api/
│   └── server.py         # FastAPI сервер
├── scripts/
│   ├── backup.sh         # Backup
│   ├── restore.sh        # Восстановление
│   └── telegram_bot.py   # Telegram бот
└── web-ui/
    └── app/              # Next.js страницы
        ├── page.tsx      # Dashboard
        ├── chat/         # AI Chat
        ├── project/      # Create Project
        └── agents/       # Manage Agents
```

---

## 🆘 Помощь

**Проблемы с Docker?**
```bash
docker-compose logs
docker-compose restart
```

**Проблемы с API?**
```bash
cat .env | grep API_KEY
source venv/bin/activate
pip install -r requirements.txt --break-system-packages
```

**Проблемы с Web UI?**
```bash
cd web-ui
rm -rf .next node_modules
npm install
npm run dev
```

---

**Создано**: 29.10.2025  
**Версия**: 1.0.0  
🚀 Enjoy!