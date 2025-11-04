# 🔧 Troubleshooting Railway Deployment

## ❌ Ошибка: "Failed to fetch"

Если вы видите эту ошибку в браузере - не волнуйтесь! API работает.

### Причины:

1. **Временная проблема сети** - просто обновите страницу
2. **CORS настройки** - если запрос идёт из браузера с другого домена
3. **Браузер кэширует старую версию** - очистите кэш (Cmd+Shift+R)

### ✅ Как проверить что API работает:

#### 1. Через Terminal/командную строку:
```bash
curl https://aiassistant-production-7a4d.up.railway.app/
```

**Ожидаемый результат:**
```json
{
  "status": "running",
  "message": "AI Development System API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

#### 2. Проверка Health:
```bash
curl https://aiassistant-production-7a4d.up.railway.app/api/health
```

**Ожидаемый результат:**
```json
{
  "status": "healthy",
  "services": {
    "anthropic": true,
    "openai": true,
    "openrouter": true,
    "gemini": true,
    "ollama": true
  },
  "router_stats": {
    "total_calls": 0,
    "total_cost": 0.0
  }
}
```

#### 3. Проверка в браузере:
Откройте эти ссылки напрямую:
- https://aiassistant-production-7a4d.up.railway.app/
- https://aiassistant-production-7a4d.up.railway.app/api/health
- https://aiassistant-production-7a4d.up.railway.app/docs (Swagger UI)

---

## 🔍 Диагностика проблем

### Проблема: API не отвечает

**Шаг 1:** Проверьте статус в Railway Dashboard
```
https://railway.app/dashboard → AIAssistant → Deployments
```

**Шаг 2:** Посмотрите логи
```bash
railway logs
```

**Шаг 3:** Проверьте переменные окружения
```
Railway Dashboard → Variables → должно быть 18 переменных
```

### Проблема: 404 Not Found

Проверьте что используете правильный URL:
- ✅ https://aiassistant-production-7a4d.up.railway.app
- ❌ https://aiassistant-production.up.railway.app (старый)

### Проблема: 500 Internal Server Error

**Причина:** Скорее всего отсутствуют переменные окружения

**Решение:**
1. Проверьте что все 18 переменных добавлены в Railway
2. Откройте [ALL_18_VARIABLES.txt](ALL_18_VARIABLES.txt)
3. Скопируйте содержимое
4. Вставьте в Railway Dashboard → Variables → Raw Editor
5. Save Changes

---

## ✅ Быстрая проверка работоспособности

Выполните эту команду в терминале:

```bash
# Проверка что всё работает
echo "🔍 Checking Railway deployment..."
echo ""

echo "1. Root endpoint:"
curl -s https://aiassistant-production-7a4d.up.railway.app/ | python3 -m json.tool
echo ""

echo "2. Health check:"
curl -s https://aiassistant-production-7a4d.up.railway.app/api/health | python3 -m json.tool
echo ""

echo "3. Available models:"
curl -s https://aiassistant-production-7a4d.up.railway.app/api/models | python3 -m json.tool
echo ""

echo "✅ If you see JSON responses above, everything is working!"
```

---

## 🚀 API Endpoints для тестирования

### Публичные (без авторизации):
```bash
# Root
curl https://aiassistant-production-7a4d.up.railway.app/

# Health
curl https://aiassistant-production-7a4d.up.railway.app/api/health

# Models list
curl https://aiassistant-production-7a4d.up.railway.app/api/models

# Register
curl -X POST https://aiassistant-production-7a4d.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Login
curl -X POST https://aiassistant-production-7a4d.up.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### Защищённые (требуют JWT токен):
```bash
# Сначала получите токен при логине, затем:
TOKEN="your-jwt-token-here"

curl -H "Authorization: Bearer $TOKEN" \
  https://aiassistant-production-7a4d.up.railway.app/api/protected-example
```

---

## 📞 Нужна помощь?

1. **Проверьте логи Railway:**
   ```bash
   railway logs
   ```

2. **Проверьте переменные:**
   ```bash
   railway variables
   ```

3. **Перезапустите деплой:**
   ```bash
   railway up
   ```

4. **Проверьте полный отчёт тестирования:**
   Откройте файл [RAILWAY_TEST_RESULTS.md](RAILWAY_TEST_RESULTS.md)

---

## ✅ Всё работает если:

- ✅ `curl` команды возвращают JSON ответы
- ✅ Health check показывает все сервисы как `true`
- ✅ Swagger docs доступны по адресу `/docs`
- ✅ Регистрация и логин возвращают JWT токены

Ошибка "Failed to fetch" в браузере обычно временная - API работает корректно! 🎉
