# 🚀 Продолжение Railway Deployment

## ✅ Что уже сделано:

1. ✅ Railway CLI установлен
2. ✅ Авторизация выполнена (jamshidsmac@gmail.com)
3. ✅ Проект создан: **AIAssistant**
4. ✅ Project URL: https://railway.com/project/07ede5cc-5fbf-4317-9bb1-1bd1acd56dd5

---

## 🎯 Что осталось (2 минуты):

### Вариант 1: Автоматический (Рекомендуется)

```bash
./deploy_railway_v2.sh
```

Скрипт настроит все переменные и задеплоит приложение.

---

### Вариант 2: Вручную (3 команды)

```bash
# 1. Установить основные переменные
railway variables --set "SECRET_KEY=Zm5Y8QxE9vKL3wRt6DpN2hJ4Gc7Ua0Sf1Mb8Xe5Wq9Vr" \
  --set "JWT_EXPIRATION_HOURS=24" \
  --set "DATABASE_PATH=./data/history.db"

# 2. Деплой
railway up

# 3. Получить URL
railway domain
```

---

## 📊 После деплоя:

```bash
# Проверь что работает
DEPLOY_URL=$(railway domain 2>&1 | grep -o 'https://[^ ]*')
curl $DEPLOY_URL/api/health

# Открой в браузере
railway open
```

---

## 🔧 Полезные команды:

```bash
railway logs          # Просмотр логов в реальном времени
railway status        # Статус deployment
railway variables     # Список переменных
railway open          # Открыть dashboard
```

---

## 🆘 Если ошибки:

```bash
# Проверь логи
railway logs

# Проверь переменные
railway variables

# Попробуй заново
railway up
```

---

## 📝 Примечание:

Старый скрипт `deploy_railway.sh` использовал устаревший синтаксис.
Используй новый: `deploy_railway_v2.sh`

**Разница:**
- ❌ Старый: `railway variables set KEY="value"`
- ✅ Новый: `railway variables --set "KEY=value"`

---

## 🚀 Готов? Запускай!

```bash
./deploy_railway_v2.sh
```

Или вручную через 3 команды выше ⬆️

---

**Время до production:** ~2-3 минуты 🎉
