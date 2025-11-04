# ⚡ Быстрый Deploy на Vercel

## 🚀 3 Простых Шага

### 1. Перейдите в директорию web-ui
```bash
cd /Users/js/autopilot-core/web-ui
```

### 2. Запустите deploy
```bash
vercel --prod
```

### 3. Следуйте инструкциям в терминале

Vercel спросит:
- **Set up and deploy "web-ui"?** → `Y` (Yes)
- **Which scope?** → Выберите ваш account
- **Link to existing project?** → `N` (No, create new)
- **What's your project's name?** → `aiassistant-web` (или любое имя)
- **In which directory is your code located?** → `.` (текущая)

Vercel автоматически:
- ✅ Detect Next.js framework
- ✅ Install dependencies
- ✅ Build project
- ✅ Deploy to production

---

## 📊 После Deploy

Vercel покажет:
```
✅ Deployment Ready
🔗 Production: https://your-project.vercel.app
```

**Скопируйте этот URL!**

---

## ⚙️ Добавить Environment Variable

### Способ 1: Через Dashboard (Проще)
1. Откройте: https://vercel.com/dashboard
2. Выберите ваш проект
3. **Settings** → **Environment Variables**
4. Нажмите **Add**
5. Введите:
   ```
   Name: NEXT_PUBLIC_API_URL
   Value: https://aiassistant-production-7a4d.up.railway.app
   Environment: Production, Preview, Development
   ```
6. **Save**
7. **Redeploy** проект

### Способ 2: Через CLI
```bash
cd /Users/js/autopilot-core/web-ui
vercel env add NEXT_PUBLIC_API_URL production
# When prompted, paste: https://aiassistant-production-7a4d.up.railway.app

# Redeploy
vercel --prod
```

---

## ✅ Проверка

### 1. Откройте Vercel URL в браузере
### 2. Откройте DevTools (F12)
### 3. Проверьте Console - не должно быть ошибок
### 4. Проверьте Network - API запросы идут на Railway

---

## 🔗 Полезные Команды

```bash
# Посмотреть список deployments
vercel ls

# Открыть dashboard
vercel open

# Посмотреть логи
vercel logs

# Получить URL последнего deploy
vercel inspect

# Список environment variables
vercel env ls
```

---

## 🆘 Проблемы?

### Build Failed
```bash
cd /Users/js/autopilot-core/web-ui
npm install
npm run build
# Исправьте ошибки
vercel --prod
```

### API не подключается
1. Проверьте Railway API:
   ```bash
   curl https://aiassistant-production-7a4d.up.railway.app/api/health
   ```
2. Добавьте `NEXT_PUBLIC_API_URL` в Vercel
3. Redeploy

---

## 📝 Полная Документация

Для подробной информации смотрите:
- **[VERCEL_SETUP.md](VERCEL_SETUP.md)** - полная инструкция

---

**Время deploy:** 2-3 минуты
**Сложность:** ⭐ Очень просто

Просто запустите `vercel --prod` и следуйте инструкциям! 🚀
