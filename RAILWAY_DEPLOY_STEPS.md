# 🚀 Railway Deployment - Пошаговая инструкция

## ✅ Подготовка завершена!

Procfile уже создан и готов к использованию.

---

## 📋 Шаги для деплоя

### Шаг 1: Войти в Railway

```bash
railway login
```

**Что произойдет:**
- Откроется браузер с формой авторизации
- Войди через GitHub/Google/Email
- После входа вернись в терминал

---

### Шаг 2: Инициализировать проект

```bash
railway init
```

**Выбери:**
- "Create a new project"
- Название: `autopilot-production` (или любое другое)

---

### Шаг 3: Настроить переменные окружения

Скопируй и выполни эти команды по очереди:

```bash
# JWT Secret (уже настроен в .env)
railway variables set SECRET_KEY="your-secret-key-here"

# JWT Expiration
railway variables set JWT_EXPIRATION_HOURS="24"

# API Keys (замени на свои)
railway variables set GEMINI_API_KEY="your-gemini-api-key"
railway variables set OPENROUTER_API_KEY="your-openrouter-api-key"
railway variables set ANTHROPIC_API_KEY="your-anthropic-api-key"
railway variables set OPENAI_API_KEY="your-openai-api-key"

# Optional: GROK (если есть)
# railway variables set GROK_API_KEY="your-key"

# Database path
railway variables set DATABASE_PATH="./data/history.db"
```

**Проверь переменные:**
```bash
railway variables
```

---

### Шаг 4: Деплой!

```bash
railway up
```

**Что произойдет:**
- Railway загрузит твой код
- Установит зависимости из requirements.txt
- Запустит сервер через Procfile
- Примерно 2-3 минуты

---

### Шаг 5: Получить URL

```bash
railway domain
```

**Пример вывода:**
```
autopilot-production.up.railway.app
```

Если домен еще не создан, создай его:
```bash
railway domain create
```

---

### Шаг 6: Тест deployment

Замени `YOUR_URL` на твой домен:

```bash
# Health check
curl https://YOUR_URL.up.railway.app/api/health

# Test registration
curl -X POST https://YOUR_URL.up.railway.app/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@production.com","password":"testpass123"}'

# Open in browser
open https://YOUR_URL.up.railway.app/docs
```

---

## 🎯 Быстрая команда (всё сразу)

Если хочешь выполнить всё одной командой после railway login:

```bash
railway login && \
railway init && \
railway variables set SECRET_KEY="your-secret-key-here" && \
railway variables set JWT_EXPIRATION_HOURS="24" && \
railway variables set GEMINI_API_KEY="your-gemini-api-key" && \
railway variables set OPENROUTER_API_KEY="your-openrouter-api-key" && \
railway variables set ANTHROPIC_API_KEY="your-anthropic-api-key" && \
railway variables set OPENAI_API_KEY="your-openai-api-key" && \
railway variables set DATABASE_PATH="./data/history.db" && \
railway up && \
railway domain
```

---

## 📊 Мониторинг

### Просмотр логов
```bash
railway logs
```

### Просмотр статуса
```bash
railway status
```

### Открыть в браузере
```bash
railway open
```

---

## 🔄 Обновление после изменений

После любых изменений в коде:

```bash
railway up
```

Railway автоматически обновит deployment.

---

## 🆘 Troubleshooting

### Deployment failed

```bash
# Проверь логи
railway logs

# Проверь переменные
railway variables

# Попробуй заново
railway up --detach
```

### Domain не работает

```bash
# Создай новый домен
railway domain create

# Проверь статус
railway status
```

### База данных не создается

```bash
# Убедись что директория data/ существует
railway run bash
mkdir -p data
exit

# Redeploy
railway up
```

---

## 💰 Лимиты бесплатного плана

- ✅ 500 часов работы в месяц (бесплатно навсегда)
- ✅ $5 бесплатных кредитов каждый месяц
- ✅ Автоматический sleep после 15 минут неактивности
- ✅ Автоматический wake up при запросе

**Этого более чем достаточно для развития и тестирования!**

---

## ✅ Финальный чеклист

После деплоя проверь:

- [ ] `curl https://YOUR_URL/api/health` возвращает `{"status":"healthy"}`
- [ ] `curl https://YOUR_URL/api/models` возвращает список моделей
- [ ] `/docs` открывается в браузере
- [ ] Регистрация работает
- [ ] Login работает
- [ ] JWT токены валидируются

---

## 🎉 Готово!

Твоя AI Development System теперь в production на Railway!

**Полезные ссылки:**
- Railway Dashboard: https://railway.app/dashboard
- Your Project: `railway open`
- Logs: `railway logs`
- Variables: `railway variables`

---

**Следующие шаги:**
1. Обнови frontend URL в `web-ui/.env.local`
2. Деплой frontend на Vercel
3. Настрой custom domain (опционально)
4. Настрой monitoring (опционально)

Enjoy your production AI system! 🚀
