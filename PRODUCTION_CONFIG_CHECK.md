# ✅ Production Configuration Check & Update Guide

## 🔍 Проверка текущей конфигурации

### Railway URL (Backend)
```
https://aiassistant-production-7a4d.up.railway.app
```

### Vercel URL (Frontend)
```
⚠️ Нужно получить из Vercel Dashboard
```

## 🚀 Быстрая проверка конфигурации

### Автоматическая проверка:
```bash
./scripts/check_production_config.sh
```

### Ручная проверка:

#### 1. Проверка Railway API
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
    "database": "healthy"
  },
  "router_stats": {
    "total_calls": 0,
    "total_cost": 0.0,
    "api_version": "1.0.0"
  }
}
```

#### 2. Проверка API Headers
```bash
curl -I https://aiassistant-production-7a4d.up.railway.app/api/health
```

**Ожидаемые заголовки:**
```
X-API-Version: 1.0.0
X-API-Server: AI Assistant Platform
Content-Encoding: gzip  # если ответ > 1KB
```

#### 3. Проверка CORS
```bash
curl -H "Origin: https://your-app.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://aiassistant-production-7a4d.up.railway.app/api/health
```

**Ожидаемые заголовки:**
```
Access-Control-Allow-Origin: https://your-app.vercel.app
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Credentials: true
```

## 📋 Обязательные переменные окружения

### Railway (Backend)

#### ✅ Уже настроены (из RAILWAY_VARIABLES.md.backup):
- `ANTHROPIC_API_KEY`
- `DATABASE_PATH`
- `GOOGLE_AI_API_KEY`
- `JWT_EXPIRATION_HOURS`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `SECRET_KEY`
- `GROK_API_KEY`
- `GEMINI_API_KEY`
- `PERPLEXITY_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `LANGFUSE_SECRET_KEY`
- `HOST`
- `ENVIRONMENT`

#### ⚠️ Нужно добавить/обновить:
```bash
# После получения Vercel URL:
CORS_ORIGINS=https://your-app.vercel.app
FRONTEND_URL=https://your-app.vercel.app
```

### Vercel (Frontend)

#### ✅ Уже настроено:
```bash
NEXT_PUBLIC_API_URL=https://aiassistant-production-7a4d.up.railway.app
```

#### ⚠️ Опционально:
```bash
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_SENTRY_DSN=your-sentry-dsn
```

## 🔧 Обновление переменных окружения

### Railway (через Dashboard)

1. Откройте: https://railway.app/dashboard
2. Выберите проект "AI Assistant Platform"
3. Перейдите в **Variables** tab
4. Нажмите **Raw Editor**
5. Добавьте/обновите:
   ```bash
   CORS_ORIGINS=https://your-app.vercel.app
   FRONTEND_URL=https://your-app.vercel.app
   ```

### Railway (через CLI)

```bash
# После получения Vercel URL:
railway variables set CORS_ORIGINS="https://your-app.vercel.app"
railway variables set FRONTEND_URL="https://your-app.vercel.app"
railway variables set ENVIRONMENT=production
```

### Vercel (через Dashboard)

1. Откройте: https://vercel.com/dashboard
2. Выберите ваш проект
3. **Settings** → **Environment Variables**
4. Убедитесь что установлено:
   ```
   NEXT_PUBLIC_API_URL=https://aiassistant-production-7a4d.up.railway.app
   ```

### Vercel (через CLI)

```bash
cd web-ui
vercel env add NEXT_PUBLIC_API_URL production
# Введите: https://aiassistant-production-7a4d.up.railway.app
```

## ✅ Чеклист Production Ready

### Backend (Railway)
- [x] API работает (health check проходит)
- [x] Все API ключи настроены
- [x] SECRET_KEY настроен
- [x] ENVIRONMENT=production
- [ ] CORS_ORIGINS настроен (после получения Vercel URL)
- [ ] FRONTEND_URL настроен (после получения Vercel URL)

### Frontend (Vercel)
- [x] NEXT_PUBLIC_API_URL настроен
- [ ] Проект задеплоен
- [ ] Vercel URL получен

### Интеграции
- [x] OAuth провайдеры настроены (Gmail, GitHub, Microsoft)
- [ ] OAuth callback URLs обновлены в провайдерах (после получения Vercel URL)

## 🧪 Тестирование после настройки

### 1. Health Check
```bash
curl https://aiassistant-production-7a4d.up.railway.app/api/health
```

### 2. Token Refresh
```bash
curl -X POST https://aiassistant-production-7a4d.up.railway.app/api/auth/refresh \
  -H "Authorization: Bearer <your-token>"
```

### 3. CORS Test
```bash
# Замените на ваш Vercel URL:
curl -H "Origin: https://your-app.vercel.app" \
     -X OPTIONS \
     https://aiassistant-production-7a4d.up.railway.app/api/health
```

### 4. Frontend Test
1. Откройте ваш Vercel URL в браузере
2. Откройте DevTools (F12)
3. Проверьте Network tab
4. Убедитесь что API запросы идут на Railway URL
5. Проверьте что нет CORS ошибок

## 🔗 Важные ссылки

- **Railway Dashboard:** https://railway.app/dashboard
- **Railway API:** https://aiassistant-production-7a4d.up.railway.app
- **Railway API Docs:** https://aiassistant-production-7a4d.up.railway.app/docs
- **Railway API Health:** https://aiassistant-production-7a4d.up.railway.app/api/health
- **Vercel Dashboard:** https://vercel.com/dashboard

## 📝 Следующие шаги

1. ✅ Получить Vercel URL из Vercel Dashboard
2. ✅ Обновить CORS_ORIGINS в Railway с Vercel URL
3. ✅ Обновить FRONTEND_URL в Railway с Vercel URL
4. ✅ Обновить OAuth callback URLs в провайдерах (Google, GitHub, Microsoft)
5. ✅ Протестировать все endpoints
6. ✅ Проверить что frontend работает с backend

---

**Обновлено:** 2025-01-04
**Railway URL:** https://aiassistant-production-7a4d.up.railway.app
**Статус:** ⚠️ Ожидается Vercel URL для финальной настройки CORS


