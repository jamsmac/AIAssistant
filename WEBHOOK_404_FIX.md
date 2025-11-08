# ✅ Webhook 404 - ИСПРАВЛЕНИЕ

## Проблема
Ошибка `404: NOT_FOUND` при попытке доступа к webhook endpoint `/api/credits/webhook`.

## Причины (найдено 2 проблемы)

### 1. ❌ Отсутствие библиотеки `stripe` в requirements.txt
**Проблема:** `credit_router` импортирует `payment_service`, который использует `stripe`, но библиотека не была в `requirements.txt`.

**Решение:** Добавлена `stripe==10.1.0` в `requirements.txt`

### 2. ❌ Неправильный импорт в auth_router.py
**Проблема:** `auth_router.py` пытался импортировать несуществующую функцию `create_access_token`.

**Решение:** Заменено на `create_jwt_token` (уже исправлено в коммите 64c6d45)

## Исправления

### Файл: `requirements.txt`
Добавлена строка:
```python
# Payment Processing
stripe==10.1.0
```

### Файл: `api/routers/auth_router.py` (уже исправлено)
```python
# Было:
from agents.auth import get_current_user, create_access_token

# Стало:
from agents.auth import get_current_user, create_jwt_token
```

## Что нужно сделать

### 1. Закоммитьте изменения
```bash
git add requirements.txt
git commit -m "Fix: Add stripe library to requirements.txt to fix webhook 404"
git push
```

### 2. Дождитесь деплоя на Railway
Railway автоматически перезапустит сервис после push (обычно 1-2 минуты).

### 3. Проверьте, что endpoint работает
```bash
curl -X POST "https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook" \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

**Ожидаемый результат:**
- ✅ `400 Bad Request` (endpoint существует, но нужна подпись Stripe)
- ❌ `404 Not Found` (если все еще не работает)

### 4. Проверьте логи Railway
```bash
railway logs | grep -i "credit\|error\|import"
```

Должны увидеть:
```
INFO: Credit router loaded successfully
```

Если видите ошибки импорта - проверьте, что все зависимости установлены.

## Правильный URL Webhook

```
https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
```

**Важно:** Путь должен быть `/api/credits/webhook`, а не `/api/webhook`!

## Проверка после деплоя

### 1. Проверьте, что router загружается
```bash
railway logs | grep "Credit router"
```
Должно быть: `INFO: Credit router loaded successfully`

### 2. Проверьте endpoint
```bash
./diagnose_webhook_404.sh
```

### 3. Проверьте API документацию
Откройте: https://aiassistant-production-7a4d.up.railway.app/docs

Должен быть виден endpoint: `POST /api/credits/webhook`

## Тестирование полного процесса оплаты

После того как endpoint заработает:

1. Откройте: https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
2. Зарегистрируйтесь или войдите
3. Перейдите в раздел Credits/Pricing
4. Выберите пакет (например, Starter $10)
5. Используйте тестовую карту:
   - Номер: `4242 4242 4242 4242`
   - CVC: `123`
   - Дата: `12/25`
   - Почтовый код: `12345`
6. Подтвердите оплату
7. Проверьте, что кредиты добавлены

## Переменные окружения (уже установлены)

✅ Все переменные Stripe уже настроены в Railway:
- `STRIPE_SECRET_KEY`
- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `FRONTEND_URL`

## Troubleshooting

### Если все еще 404 после деплоя

1. **Проверьте логи Railway:**
   ```bash
   railway logs --tail 100
   ```

2. **Проверьте, что изменения задеплоены:**
   ```bash
   git log --oneline -3
   ```
   Должны быть коммиты:
   - `Fix: Add stripe library to requirements.txt...`
   - `Fix: Replace create_access_token...`

3. **Проверьте, что stripe установлен:**
   В логах Railway не должно быть ошибок типа `ModuleNotFoundError: No module named 'stripe'`

### Если webhook возвращает 400 (Bad Request)

Это нормально! Это означает, что endpoint работает, но нужна правильная подпись Stripe. Проверьте:
- `STRIPE_WEBHOOK_SECRET` в Railway совпадает с секретом в Stripe Dashboard
- Webhook URL в Stripe Dashboard правильный

### Если webhook возвращает 500 (Server Error)

Проверьте логи Railway на наличие ошибок обработки webhook.

## Дополнительные ресурсы

- [Stripe Python SDK](https://github.com/stripe/stripe-python)
- [Stripe Webhooks Documentation](https://stripe.com/docs/webhooks)
- [Railway Logs](https://railway.app/dashboard)

---

**Дата:** 08.11.2025  
**Проблема:** 404 NOT_FOUND  
**Причина:** Отсутствие библиотеки `stripe` в requirements.txt  
**Решение:** Добавлена `stripe==10.1.0` в requirements.txt  
**Статус:** Готово к деплою
