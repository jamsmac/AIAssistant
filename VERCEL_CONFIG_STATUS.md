# ✅ Vercel Configuration - Статус и инструкции

## 🔍 Текущий статус

### ✅ Vercel CLI
- **Установлен:** ✅ Vercel CLI 48.8.0
- **Авторизация:** ✅ jamshidsmac-6260
- **Проект:** ✅ web-ui (привязан)

### ⚠️ Переменные окружения
- **NEXT_PUBLIC_API_URL:** ❌ Не найдена

### ⚠️ Деплойменты
- **Деплойменты:** ❌ Не найдены

## 🚀 Настройка Vercel

### Шаг 1: Добавить переменную окружения

**Вариант A: Через Dashboard (Рекомендуется)**

1. Откройте: https://vercel.com/dashboard
2. Выберите проект **web-ui**
3. Перейдите в **Settings** → **Environment Variables**
4. Нажмите **Add New**
5. Заполните:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://aiassistant-production-7a4d.up.railway.app`
   - **Environment:** Выберите Production, Preview, Development (или все)
6. Нажмите **Save**

**Вариант B: Через CLI**

```bash
cd web-ui
vercel env add NEXT_PUBLIC_API_URL production
# При запросе введите: https://aiassistant-production-7a4d.up.railway.app
```

Также добавьте для других окружений:
```bash
vercel env add NEXT_PUBLIC_API_URL preview
vercel env add NEXT_PUBLIC_API_URL development
```

### Шаг 2: Проверить деплоймент

Если проект не задеплоен:

```bash
cd web-ui
npm install
npm run build
vercel --prod
```

Или проверьте через Dashboard:
- https://vercel.com/dashboard
- Найдите проект web-ui
- Проверьте раздел Deployments

### Шаг 3: Получить Vercel URL

После деплоя:
1. Откройте Dashboard
2. Найдите последний deployment
3. Скопируйте URL (например: `https://web-ui-xxx.vercel.app`)

Или через CLI:
```bash
cd web-ui
vercel ls
```

## 📋 Обязательные переменные окружения

### Критическая:
- ✅ `NEXT_PUBLIC_API_URL` = `https://aiassistant-production-7a4d.up.railway.app`

### Опциональные (для будущего):
- `NEXT_PUBLIC_ENVIRONMENT` = `production`
- `NEXT_PUBLIC_SENTRY_DSN` = ваш Sentry DSN
- `NEXT_PUBLIC_GA_MEASUREMENT_ID` = ваш Google Analytics ID

## 🔗 После настройки

### 1. Обновить Railway переменные

После получения Vercel URL:

```bash
./scripts/update_railway_vars.sh
```

Или вручную:
```bash
railway variables set CORS_ORIGINS="https://your-app.vercel.app"
railway variables set FRONTEND_URL="https://your-app.vercel.app"
```

### 2. Проверить конфигурацию

```bash
./scripts/check_production_config.sh
```

### 3. Обновить OAuth callback URLs

В провайдерах (Google, GitHub, Microsoft) обновите callback URLs:
- Google: `https://your-app.vercel.app/api/auth/callback/google`
- GitHub: `https://your-app.vercel.app/api/auth/callback/github`
- Microsoft: `https://your-app.vercel.app/api/auth/callback/microsoft`

## 🧪 Тестирование

### 1. Проверка переменных
```bash
cd web-ui
vercel env ls
```

### 2. Проверка деплоймента
```bash
cd web-ui
vercel ls
```

### 3. Проверка подключения к API
После деплоя откройте Vercel URL в браузере:
- Откройте DevTools (F12)
- Проверьте Network tab
- Убедитесь что запросы идут на Railway URL
- Проверьте что нет CORS ошибок

## 📝 Чеклист

- [ ] Добавить `NEXT_PUBLIC_API_URL` в Vercel
- [ ] Задеплоить проект (если не задеплоен)
- [ ] Получить Vercel URL
- [ ] Обновить `CORS_ORIGINS` в Railway
- [ ] Обновить `FRONTEND_URL` в Railway
- [ ] Протестировать подключение
- [ ] Обновить OAuth callback URLs

## 🔗 Полезные ссылки

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Railway API:** https://aiassistant-production-7a4d.up.railway.app
- **Railway API Docs:** https://aiassistant-production-7a4d.up.railway.app/docs

---

**Статус:** ⚠️ Требуется добавить переменные окружения и проверить деплоймент
**Обновлено:** 2025-01-04






