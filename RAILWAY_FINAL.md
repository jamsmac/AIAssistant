# 🚀 Railway Deployment - ФИНАЛЬНЫЕ ШАГИ

## ✅ Текущий статус:
- ✅ Проект AIAssistant создан
- ✅ Procfile готов
- ⏳ Осталось: деплой + переменные + URL

---

## 🎯 3 КОМАНДЫ ДО PRODUCTION:

### Команда 1: Деплой (2-3 минуты)
```bash
railway up
```
**Что происходит:**
- Railway создаст service автоматически
- Установит зависимости из requirements.txt
- Запустит через Procfile
- Покажет прогресс в реальном времени

**Дождись:** `✓ Build successful` и `✓ Deployed`

---

### Команда 2: Переменные окружения
```bash
railway variables --set "SECRET_KEY=Zm5Y8QxE9vKL3wRt6DpN2hJ4Gc7Ua0Sf1Mb8Xe5Wq9Vr" \
  --set "JWT_EXPIRATION_HOURS=24" \
  --set "DATABASE_PATH=./data/history.db"
```

**Опционально** (если хочешь добавить API ключи):
```bash
railway variables --set "GEMINI_API_KEY=твой-ключ" \
  --set "OPENROUTER_API_KEY=твой-ключ" \
  --set "ANTHROPIC_API_KEY=твой-ключ" \
  --set "OPENAI_API_KEY=твой-ключ"
```

---

### Команда 3: Получить URL
```bash
railway domain
```

Если домен не создан автоматически:
```bash
railway domain create
```

---

## ✅ Проверка работоспособности

После получения URL (например: `https://aiassistant-production.up.railway.app`):

```bash
# Health check
curl https://YOUR_URL/api/health

# Проверь API docs
open https://YOUR_URL/docs

# Тест регистрации
curl -X POST https://YOUR_URL/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@prod.com","password":"testpass123"}'
```

---

## 🔧 Полезные команды

```bash
railway logs          # Логи в реальном времени
railway status        # Статус deployment
railway variables     # Список переменных
railway open          # Открыть dashboard
railway restart       # Перезапустить
```

---

## 🆘 Troubleshooting

### Build failed
```bash
railway logs          # Проверь ошибки
railway up            # Попробуй снова
```

### Нет домена
```bash
railway domain create
```

### Проверить переменные
```bash
railway variables
```

---

## 📊 После успешного деплоя

У тебя будет:
- ✅ Production URL с HTTPS
- ✅ 19 API endpoints онлайн
- ✅ JWT authentication работает
- ✅ Swagger UI доступен
- ✅ Auto-scaling
- ✅ 500 часов/месяц бесплатно

---

## 🎉 Готов? Начинай!

```bash
railway up
```

Жду результата! 🚀
