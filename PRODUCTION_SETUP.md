# 🚀 Production Setup Guide

## ✅ Критические блокеры (P0) - ИСПРАВЛЕНЫ

### 1. ✅ CORS Configuration для Production

**Исправлено:** `api/server.py` теперь читает production домены из переменной окружения.

**Настройка:**

Добавьте в `.env` или в настройки деплоя (Railway/Vercel):

```bash
# CORS Origins для production (через запятую)
CORS_ORIGINS=https://your-app.vercel.app,https://www.yourdomain.com,https://app.yourdomain.com
```

**Пример для Railway:**
```bash
railway variables set CORS_ORIGINS="https://your-app.vercel.app,https://www.yourdomain.com"
```

**Локальная разработка:**
- По умолчанию используются localhost домены
- Production домены добавляются автоматически если указан `CORS_ORIGINS`

### 2. ✅ OAuth Callback URLs для Production

**Исправлено:** `agents/oauth_providers.py` теперь использует `FRONTEND_URL` или `BASE_URL` для формирования callback URLs.

**Настройка:**

Добавьте в `.env` или в настройки деплоя:

```bash
# Базовый URL фронтенда (для OAuth callbacks)
FRONTEND_URL=https://your-app.vercel.app

# Или явно укажите callback URLs для каждого провайдера:
GOOGLE_REDIRECT_URI=https://your-app.vercel.app/api/auth/callback/google
GITHUB_REDIRECT_URI=https://your-app.vercel.app/api/auth/callback/github
MICROSOFT_REDIRECT_URI=https://your-app.vercel.app/api/auth/callback/microsoft
```

**Важно:** Убедитесь что эти URLs добавлены в настройках OAuth приложений:
- Google Cloud Console → Credentials → Authorized redirect URIs
- GitHub → Settings → Developer settings → OAuth Apps → Authorization callback URL
- Microsoft Azure → App registrations → Authentication → Redirect URIs

### 3. ✅ SECRET_KEY Валидация

**Исправлено:** `agents/auth.py` теперь валидирует длину SECRET_KEY.

**Требования:**
- Development: минимум 32 символа (с предупреждением)
- Production: минимум 64 символа (обязательно)

**Генерация сильного SECRET_KEY:**

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Или с использованием openssl
openssl rand -base64 64
```

**Настройка:**

```bash
SECRET_KEY=your-super-secret-key-minimum-64-characters-long-for-production
ENVIRONMENT=production  # Важно для строгой валидации
```

### 4. ✅ Token Refresh Endpoint

**Добавлено:** Новый endpoint `POST /api/auth/refresh` для обновления JWT токенов.

**Использование:**
```bash
curl -X POST https://your-api.railway.app/api/auth/refresh \
  -H "Authorization: Bearer <current_token>"
```

**Особенности:**
- Использует текущий токен для получения нового
- Проверяет существование и активность пользователя
- Автоматически обновляет cookie

### 5. ✅ Secure Cookies

**Исправлено:** Все cookies теперь автоматически используют `secure=True` в production.

**Настройка:**
- Автоматически определяется из `ENVIRONMENT=production`
- В development: `secure=False`
- В production: `secure=True`

## ✅ Исправленные ошибки кода

### 1. ✅ Health Check для базы данных
- Исправлено неправильное использование `get_db()`
- Правильная проверка соединения с БД

### 2. ✅ Logout Endpoint
- Исправлен конфликт имен переменной `response`

### 3. ✅ CSRF Token Generation
- Исправлено использование `payload.get('user_id')` → `payload.get('sub')`

### 4. ✅ User ID в Payload
- Все места исправлены на использование `sub` из JWT стандарта
- Затронуты все 2FA endpoints

## ✅ Quick Wins - РЕАЛИЗОВАНЫ

### 1. ✅ Health Check Endpoint

**Эндпоинт:** `GET /api/health`

**Проверяет:**
- Доступность всех AI моделей
- Статус базы данных
- Статистику использования
- Версию API

**Использование:**
```bash
curl https://your-api.railway.app/api/health
```

### 2. ✅ API Version Headers

**Добавлено:** Все ответы теперь содержат заголовки:
- `X-API-Version`: версия API (из `app.version`)
- `X-API-Server`: название сервера

**Пример:**
```bash
curl -I https://your-api.railway.app/api/health
# X-API-Version: 1.0.0
# X-API-Server: AI Assistant Platform
```

### 3. ✅ Gzip Compression

**Добавлено:** Автоматическое сжатие ответов > 1KB

**Эффект:**
- Уменьшение размера ответов на 60-80%
- Ускорение загрузки для клиентов
- Экономия трафика

## 📋 Полный список переменных окружения для Production

### Обязательные (P0)

```bash
# Безопасность
SECRET_KEY=<64+ символов, сгенерировать через secrets.token_urlsafe(64)>
ENVIRONMENT=production

# CORS
CORS_ORIGINS=https://your-app.vercel.app,https://www.yourdomain.com

# Frontend URL (для OAuth)
FRONTEND_URL=https://your-app.vercel.app

# OAuth Providers (если используете)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://your-app.vercel.app/api/auth/callback/google

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
```

### Опциональные (но рекомендуемые)

```bash
# AI Model API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...
GROK_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434

# Database
DATABASE_URL=sqlite:///./data/history.db  # или PostgreSQL для production

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
ENVIRONMENT=production
RELEASE_VERSION=1.0.0

# Email для алертов
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAILS=admin@yourdomain.com

# Webhook для алертов
WEBHOOK_URL=https://your-webhook-url
```

## 🚀 Deployment Checklist

### Railway (Backend)

- [x] Добавить `CORS_ORIGINS` переменную
- [x] Добавить `FRONTEND_URL` переменную
- [x] Добавить `SECRET_KEY` (64+ символов)
- [x] Установить `ENVIRONMENT=production`
- [x] Добавить все необходимые API ключи
- [ ] Протестировать health check endpoint
- [ ] Протестировать CORS с production frontend

### Vercel (Frontend)

- [ ] Настроить проект заново (если был удален)
- [ ] Добавить переменную `NEXT_PUBLIC_API_URL=https://your-api.railway.app`
- [ ] Убедиться что build проходит успешно
- [ ] Протестировать OAuth callbacks

### OAuth Providers

- [ ] Google Cloud Console: добавить redirect URI
- [ ] GitHub: добавить callback URL
- [ ] Microsoft Azure: добавить redirect URI
- [ ] Протестировать каждую интеграцию

## 🔍 Тестирование после деплоя

### 1. Health Check
```bash
curl https://your-api.railway.app/api/health
```

**Ожидаемый результат:**
```json
{
  "status": "healthy",
  "services": {
    "anthropic": true,
    "openai": true,
    "database": "healthy"
  },
  "router_stats": {
    "total_calls": 0,
    "total_cost": 0.0,
    "api_version": "1.0.0"
  }
}
```

### 2. CORS проверка
```bash
curl -H "Origin: https://your-app.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://your-api.railway.app/api/health
```

**Ожидаемые заголовки:**
```
Access-Control-Allow-Origin: https://your-app.vercel.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Credentials: true
```

### 3. API Version Headers
```bash
curl -I https://your-api.railway.app/api/health
```

**Ожидаемые заголовки:**
```
X-API-Version: 1.0.0
X-API-Server: AI Assistant Platform
Content-Encoding: gzip  # если ответ > 1KB
```

## 📊 Статус исправлений

### ✅ Завершено (P0 + Quick Wins)

- ✅ CORS для production доменов (через env переменную)
- ✅ OAuth callback URLs для production (через FRONTEND_URL)
- ✅ SECRET_KEY валидация (минимум 64 символа для production)
- ✅ Health check endpoint улучшен
- ✅ API version headers добавлены
- ✅ Gzip compression включен

### ⏳ Осталось (P1)

- [ ] Разбить server.py на модульные routers (4 часа)
- [ ] Протестировать все AI модели с реальными ключами (2 часа)
- [ ] Переконфигурировать Vercel deployment (1 час)
- [ ] Протестировать token refresh механизм (1 час)

## 💡 Следующие шаги

1. **Немедленно (P0):**
   - Настроить переменные окружения в Railway/Vercel
   - Протестировать CORS и OAuth callbacks

2. **На этой неделе (P1):**
   - Рефакторинг server.py
   - Полное тестирование интеграций

3. **Опционально (P2):**
   - Visual workflow builder
   - Больше тестов
   - Оптимизация bundle size

---

**Время до Production Ready:** ~1.5 часа (настройка переменных) + тестирование

**После выполнения всех P0 задач:** ✅ Проект готов к production деплою!

