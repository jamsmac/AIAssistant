# 🚂 Railway Variables Setup - Step by Step

## Railway CLI не может добавить переменные автоматически

Railway CLI требует интерактивный выбор сервиса, что невозможно в скриптах.

**Решение**: Используйте веб-интерфейс Railway (2 минуты)

---

## ✅ Пошаговая инструкция:

### Шаг 1: Откройте Railway Dashboard

**Ссылка**: https://railway.app/dashboard

Или через терминал:
```bash
open https://railway.app/dashboard
```

### Шаг 2: Выберите проект

1. Найдите проект **"AIAssistant"**
2. Кликните на него

### Шаг 3: Выберите сервис

Вы увидите ваш сервис (backend). Кликните на него.

**URL сервиса**: `aiassistant-production-7a4d.up.railway.app`

### Шаг 4: Откройте вкладку Variables

В меню сервиса найдите:
- **Variables** (или **Environment Variables**)
- Кликните на эту вкладку

### Шаг 5: Добавьте 3 переменные

Нажмите кнопку **"New Variable"** (или "Add Variable") **3 раза**:

#### Переменная 1:
```
Name:  GOOGLE_CLIENT_ID
Value: YOUR_GOOGLE_CLIENT_ID_FROM_CLOUD_CONSOLE
```

#### Переменная 2:
```
Name:  GOOGLE_CLIENT_SECRET
Value: YOUR_GOOGLE_CLIENT_SECRET_FROM_CLOUD_CONSOLE
```

#### Переменная 3:
```
Name:  GOOGLE_REDIRECT_URI
Value: https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback
```

### Шаг 6: Сохраните и задеплойте

1. После добавления всех 3 переменных
2. Railway автоматически предложит **"Redeploy"**
3. Нажмите **"Deploy"** или **"Save"**

---

## 📋 Копируйте значения отсюда:

### GOOGLE_CLIENT_ID:
```
YOUR_GOOGLE_CLIENT_ID_FROM_CLOUD_CONSOLE
```

### GOOGLE_CLIENT_SECRET:
```
YOUR_GOOGLE_CLIENT_SECRET_FROM_CLOUD_CONSOLE
```

### GOOGLE_REDIRECT_URI:
```
https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback
```

---

## ✅ Проверка

После деплоя проверьте переменные:

```bash
railway variables --environment production
```

Должны увидеть:
```
GOOGLE_CLIENT_ID=548806729861-lm...
GOOGLE_CLIENT_SECRET=GOCSPX-n1b1...
GOOGLE_REDIRECT_URI=https://aiassistant...
```

---

## 🔗 Что делать дальше:

### 1. Enable APIs в Google Cloud Console ☁️

**Gmail API**:
```bash
open "https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=aiassistant-os-platform"
```
Нажмите **"ENABLE"**

**Drive API**:
```bash
open "https://console.cloud.google.com/apis/library/drive.googleapis.com?project=aiassistant-os-platform"
```
Нажмите **"ENABLE"**

### 2. Deploy код 🚀

```bash
git add .
git commit -m "feat: Complete Module 4 & 5 - OAuth + Visual improvements"
git push
```

Railway автоматически задеплоит изменения.

---

## 🎯 Альтернатива: Railway CLI с интерактивным выбором

Если хотите использовать CLI:

```bash
# 1. Link сервис интерактивно
railway service

# Выберите ваш сервис из списка

# 2. Добавьте переменные
railway variables --set "GOOGLE_CLIENT_ID=YOUR_CLIENT_ID"
railway variables --set "GOOGLE_CLIENT_SECRET=YOUR_CLIENT_SECRET"
railway variables --set "GOOGLE_REDIRECT_URI=https://aiassistant-production-7a4d.up.railway.app/api/integrations/callback"
```

**Примечание**: Это требует интерактивного ввода в терминале.

---

## 📞 Помощь

Если возникли проблемы:

1. **Не могу найти проект**:
   - Проверьте что вы залогинены: `railway whoami`
   - Список проектов: `railway list`

2. **Переменные не сохраняются**:
   - Проверьте что нажали "Deploy" после добавления
   - Обновите страницу в браузере

3. **Не вижу сервис**:
   - Убедитесь что выбрали правильный проект
   - Проверьте environment (должен быть production)

---

**Время выполнения**: 2-3 минуты через веб-интерфейс

**Статус после**: ✅ Готово к деплою
