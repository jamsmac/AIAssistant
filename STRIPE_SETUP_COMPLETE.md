# ✅ Stripe Setup Complete

## Step 1: Railway Variables - COMPLETED ✅

Все переменные успешно установлены в Railway:

```
✅ STRIPE_SECRET_KEY = sk_test_51SJZ0IBk4MbPWMlr...
✅ STRIPE_PUBLISHABLE_KEY = pk_test_51SJZ0IBk4MbPWMlr...
✅ STRIPE_WEBHOOK_SECRET = whsec_7JYAcvsvhsCcHZjS7cNTfkzPxA2Y0vbB
✅ FRONTEND_URL = https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app
```

## Step 2: Update Webhook URL in Stripe (Manual - 1 минута) ⚠️ ВАЖНО!

**Действия:**

1. Откройте: https://dashboard.stripe.com/test/webhooks

2. Найдите webhook: `we_1SR4zwBk4MbPWMlrQLAtGDgw`

3. Нажмите на него

4. В разделе "Endpoint URL" нажмите "Update details"

5. Введите **ПРАВИЛЬНЫЙ** URL (обратите внимание на `/api/credits/webhook`):
   ```
   https://aiassistant-production-7a4d.up.railway.app/api/credits/webhook
   ```
   
   ⚠️ **НЕ `/api/webhook`**, а `/api/credits/webhook`!

6. Убедитесь, что выбран event: `checkout.session.completed`

7. Нажмите "Update endpoint"

8. **Протестируйте webhook:**
   - Перейдите на вкладку "Testing"
   - Выберите event `checkout.session.completed`
   - Нажмите "Send test webhook"
   - Должен вернуться статус `200 OK` ✅

## Step 3: Test Payment (Manual - 2 минуты)

**Действия:**

1. Откройте ваш сайт: https://aiassistant-4h266kq8h-vendhubs-projects.vercel.app

2. Зарегистрируйте новый аккаунт или войдите

3. Перейдите в раздел покупки кредитов

4. Выберите пакет "Starter" ($10)

5. Используйте тестовую карту:
   - Номер: `4242 4242 4242 4242`
   - CVC: любые 3 цифры
   - Expiry: любая будущая дата

6. Проверьте:
   - ✅ Платеж прошел успешно
   - ✅ 1,000 кредитов добавлено на аккаунт
   - ✅ В Stripe Dashboard появилась транзакция

## Railway Backend URL

Ваш backend работает на:
```
https://aiassistant-production-7a4d.up.railway.app
```

## Endpoints для проверки

- Webhook endpoint: `/api/credits/webhook`
- Create checkout: `/api/credits/create-checkout-session`
- Credit history: `/api/credits/history`
- Current balance: `/api/credits/balance`

## Проверка логов (если нужно)

```bash
railway logs --service a356894b-78b6-4746-8cf4-69103f40b474
```

## Если что-то не работает

1. Проверьте логи в Railway:
   ```bash
   railway logs
   ```

2. Проверьте webhook в Stripe:
   - Stripe Dashboard → Webhooks → Выберите webhook → Events

3. Убедитесь, что FRONTEND_URL совпадает с реальным URL вашего сайта

---

**Дата:** 08.11.2025
**Статус:** Railway variables настроены ✅
**Следующий шаг:** Обновить webhook URL в Stripe Dashboard
