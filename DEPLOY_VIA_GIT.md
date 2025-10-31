# 🚀 Railway Deployment via Git

## 🎯 Самый надежный способ при проблемах с CLI

Railway CLI испытывает timeout? Используй Git!

---

## 📋 Шаги (5 минут):

### 1. Инициализируй Git (если еще нет)

```bash
# Проверь есть ли .git
ls -la | grep .git

# Если нет - инициализируй
git init
```

### 2. Создай .gitignore

```bash
cat > .gitignore << 'IGNORE'
venv/
__pycache__/
*.pyc
.env
.DS_Store
data/history.db
node_modules/
.next/
IGNORE
```

### 3. Добавь все файлы

```bash
git add .
git commit -m "Initial deployment to Railway"
```

### 4. Настрой Railway remote

Railway автоматически создал remote при `railway link`:

```bash
# Проверь remotes
git remote -v

# Если нет railway remote, добавь:
railway link
```

### 5. Push на Railway

```bash
git push railway main
```

Если ветка называется иначе (master):
```bash
git push railway master:main
```

---

## ✅ После Push

Railway автоматически:
1. Обнаружит push
2. Запустит build
3. Установит зависимости из requirements.txt
4. Запустит через Procfile
5. Создаст URL

---

## 📊 Отслеживай прогресс

### В терминале:
```bash
railway logs --follow
```

### В браузере:
```bash
railway open
```

---

## 🔧 Настрой переменные

После успешного deploy:

```bash
railway variables --set "SECRET_KEY=Zm5Y8QxE9vKL3wRt6DpN2hJ4Gc7Ua0Sf1Mb8Xe5Wq9Vr" \
  --set "JWT_EXPIRATION_HOURS=24" \
  --set "DATABASE_PATH=./data/history.db"
```

Или через Dashboard: Settings → Variables

---

## 🌐 Получи URL

```bash
railway domain
```

Или в Dashboard: Settings → Domains → Generate Domain

---

## 🔄 Будущие обновления

После изменений в коде:

```bash
git add .
git commit -m "Update description"
git push railway main
```

Railway автоматически redeploy!

---

## 🆘 Troubleshooting

### Git remote не настроен
```bash
railway link
git remote -v
```

### Push rejected
```bash
git pull railway main --rebase
git push railway main
```

### Нужна другая ветка
```bash
git branch -M main
git push railway main
```

---

## 💡 Преимущества Git deploy

- ✅ Надежнее при плохом интернете
- ✅ Автоматический redeploy при push
- ✅ История изменений
- ✅ Rollback к предыдущим версиям
- ✅ Интеграция с GitHub/GitLab

---

## 🎉 Готов? Начинай!

```bash
git init
git add .
git commit -m "Deploy to Railway"
git push railway main
```

Жду результата! 🚀
