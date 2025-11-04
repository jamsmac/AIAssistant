# 🚀 Vercel Deployment - Полная Настройка

## 📋 Предварительные Требования

- ✅ Vercel CLI установлен (v48.8.0)
- ✅ Залогинены в Vercel (jamshidsmac-6260)
- ✅ Next.js проект в `web-ui/`
- ✅ Railway API запущен

---

## 🎯 Быстрый Deploy

### Автоматический способ:
```bash
./deploy_vercel.sh
```

### Ручной способ:
```bash
cd web-ui
npm install
npm run build
vercel --prod --yes
```

---

## 🔧 Шаг 1: Обновление API URL

API URL уже обновлён в `web-ui/.env.local`:
```env
NEXT_PUBLIC_API_URL=https://aiassistant-production-7a4d.up.railway.app
```

---

## 🌐 Шаг 2: Настройка Environment Variables в Vercel

После деплоя, добавьте переменные через Vercel Dashboard:

### Способ 1: Через Dashboard
1. Откройте: https://vercel.com/dashboard
2. Выберите ваш проект
3. Settings → Environment Variables
4. Добавьте:

```
NEXT_PUBLIC_API_URL=https://aiassistant-production-7a4d.up.railway.app
```

### Способ 2: Через CLI
```bash
cd web-ui
vercel env add NEXT_PUBLIC_API_URL production
# Вставьте: https://aiassistant-production-7a4d.up.railway.app
```

---

## 📦 Шаг 3: Deploy

### Option A: Production Deploy
```bash
cd web-ui
vercel --prod
```

### Option B: Preview Deploy
```bash
cd web-ui
vercel
```

---

## ✅ После Deploy

### Получить URL:
```bash
cd web-ui
vercel ls
```

### Проверить deployment:
```bash
cd web-ui
vercel inspect
```

### Открыть в браузере:
```bash
cd web-ui
vercel open
```

---

## 🔍 Тестирование

После успешного деплоя:

1. **Откройте ваш Vercel URL**
2. **Проверьте главную страницу**
3. **Проверьте подключение к API:**
   - Откройте DevTools (F12)
   - Проверьте Network tab
   - API запросы должны идти на Railway URL

---

## ⚙️ Vercel Configuration

### vercel.json
```json
{
  "functions": {
    "app/**/*.ts": {
      "maxDuration": 30
    }
  },
  "framework": "nextjs"
}
```

### next.config.ts
Проверьте что настроено правильно:
```typescript
const nextConfig: NextConfig = {
  // Output standalone for Vercel
  output: 'standalone',

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL
  }
}
```

---

## 🐛 Troubleshooting

### Проблема: "Build failed"

**Решение:**
```bash
cd web-ui
npm install
npm run build

# Если ошибки TypeScript:
npx tsc --noEmit
```

### Проблема: "API connection failed"

**Проверьте:**
1. Railway API работает:
   ```bash
   curl https://aiassistant-production-7a4d.up.railway.app/api/health
   ```

2. Environment variable в Vercel:
   ```bash
   cd web-ui
   vercel env ls
   ```

3. CORS настроен в Railway API

### Проблема: "Vercel project not found"

**Решение:**
```bash
cd web-ui
rm -rf .vercel
vercel --prod
# Выберите "Create new project"
```

---

## 📊 Vercel Commands

```bash
# Deploy to production
vercel --prod

# Deploy preview
vercel

# List deployments
vercel ls

# Inspect last deployment
vercel inspect

# View logs
vercel logs

# Open dashboard
vercel open

# List environment variables
vercel env ls

# Add environment variable
vercel env add

# Remove environment variable
vercel env rm

# Pull environment variables
vercel env pull
```

---

## 🔗 Important URLs

- **Vercel Dashboard:** https://vercel.com/dashboard
- **Railway API:** https://aiassistant-production-7a4d.up.railway.app
- **Railway API Docs:** https://aiassistant-production-7a4d.up.railway.app/docs
- **Railway API Health:** https://aiassistant-production-7a4d.up.railway.app/api/health

---

## 📝 Deployment Checklist

- [ ] Vercel CLI установлен и залогинен
- [ ] `web-ui/.env.local` содержит правильный API URL
- [ ] Dependencies установлены (`npm install`)
- [ ] Build проходит успешно (`npm run build`)
- [ ] Environment variables добавлены в Vercel
- [ ] Deploy на production (`vercel --prod`)
- [ ] Протестирован frontend URL
- [ ] API подключение работает
- [ ] Нет CORS ошибок

---

## 🎯 Что дальше?

После успешного deploy:

1. ✅ Получите production URL
2. ✅ Добавьте custom domain (опционально)
3. ✅ Настройте analytics (опционально)
4. ✅ Подключите GitHub для auto-deploy (опционально)

---

## 💡 Полезные Ссылки

- **Vercel Docs:** https://vercel.com/docs
- **Next.js Deployment:** https://nextjs.org/docs/deployment
- **Vercel CLI:** https://vercel.com/docs/cli

---

**Готово к deploy! 🚀**

Используйте `./deploy_vercel.sh` для автоматического деплоя.
