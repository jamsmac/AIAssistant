# ⚡ Railway Deploy - Quick Reference

## 🚀 Самый быстрый способ

```bash
./deploy_railway.sh
```

**Что делать:**
1. Откроется браузер → войди через GitHub/Google
2. В терминале выбери "Create new project"
3. Название: `autopilot-production`
4. Дождись окончания deployment (~2-3 мин)
5. Получишь URL: `https://your-app.up.railway.app`

---

## 📋 Или вручную (5 команд)

```bash
# 1. Login
railway login

# 2. Init
railway init

# 3. Set variables (одной командой)
railway variables set SECRET_KEY="Zm5Y8QxE9vKL3wRt6DpN2hJ4Gc7Ua0Sf1Mb8Xe5Wq9Vr" \
  JWT_EXPIRATION_HOURS="24" \
  DATABASE_PATH="./data/history.db"

# 4. Deploy
railway up

# 5. Get URL
railway domain
```

---

## ✅ После деплоя

```bash
# Проверь что работает
curl https://YOUR_URL/api/health

# Открой документацию
open https://YOUR_URL/docs

# Тест регистрации
curl -X POST https://YOUR_URL/api/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@prod.com","password":"testpass123"}'
```

---

## 🔧 Полезные команды

```bash
railway logs          # Логи
railway status        # Статус
railway open          # Открыть dashboard
railway variables     # Список переменных
railway up            # Redeploy
```

---

## 🆘 Проблемы?

**Deployment failed:**
```bash
railway logs  # Смотри ошибки
railway up    # Попробуй снова
```

**Нет домена:**
```bash
railway domain create
```

**Переменные не установлены:**
```bash
railway variables
railway variables set KEY="value"
```

---

## 💡 Tip

После любых изменений в коде просто:
```bash
railway up
```

Railway автоматически обновит!

---

**Подробная инструкция:** `cat RAILWAY_DEPLOY_STEPS.md`
