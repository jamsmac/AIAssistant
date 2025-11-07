# 💼 Бизнес-Модель: AI-as-a-Service с Наценкой

**Модель**: Пользователи используют ваши API ключи с наценкой 10-20%  
**Роль**: Вы суперадмин, настраиваете все через админ-панель

---

## 🎯 Как Это Работает

### Концепция:

```
Пользователь → Ваша Платформа → AI API (OpenAI, Anthropic, etc)
             ↓
    Запрос стоит $0.01
             ↓
    Наценка 20% → Пользователь платит $0.012
             ↓
    Ваша прибыль: $0.002
```

### Ваши Обязанности (Суперадмин):
1. ✅ Настраиваете **свои API ключи** для всех AI провайдеров
2. ✅ Устанавливаете **процент наценки** (10%, 15%, 20%)
3. ✅ Мониторите **расходы и доходы**
4. ✅ Управляете **лимитами пользователей**
5. ✅ Смотрите **аналитику использования**

### Пользователи:
- ❌ **НЕ используют свои API ключи**
- ✅ Платят вам за каждый запрос с наценкой
- ✅ Видят свою стоимость использования
- ✅ Имеют лимиты (daily/monthly)

---

## 🏗️ Архитектура Системы

### 1. Таблица Настроек Цен (Pricing Config)

```sql
CREATE TABLE pricing_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,              -- 'openai', 'anthropic', 'google'
    model TEXT NOT NULL,                 -- 'gpt-4', 'claude-3-opus'
    cost_per_1k_tokens REAL NOT NULL,    -- Себестоимость (от провайдера)
    markup_percentage REAL NOT NULL,     -- Наценка (10, 15, 20)
    price_per_1k_tokens REAL NOT NULL,   -- Цена для пользователя (вычисляется)
    updated_by INTEGER,                  -- user_id суперадмина
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, model)
);

-- Пример данных:
INSERT INTO pricing_config (provider, model, cost_per_1k_tokens, markup_percentage, price_per_1k_tokens) VALUES
('openai', 'gpt-4-turbo', 0.01, 20, 0.012),      -- OpenAI GPT-4 Turbo
('openai', 'gpt-3.5-turbo', 0.002, 20, 0.0024),  -- OpenAI GPT-3.5
('anthropic', 'claude-3-opus', 0.015, 15, 0.01725), -- Anthropic Claude 3 Opus
('anthropic', 'claude-3-sonnet', 0.003, 15, 0.00345), -- Anthropic Claude 3 Sonnet
('google', 'gemini-pro', 0.00025, 20, 0.0003);   -- Google Gemini Pro
```

### 2. Таблица Использования (Usage Tracking)

```sql
CREATE TABLE user_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    request_id INTEGER,                  -- Ссылка на requests
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    cost_to_platform REAL NOT NULL,      -- Ваши расходы
    charged_to_user REAL NOT NULL,       -- Заработано с пользователя
    profit REAL NOT NULL,                -- Ваша прибыль
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (request_id) REFERENCES requests(id)
);

-- Индексы для быстрой аналитики
CREATE INDEX idx_user_usage_user ON user_usage(user_id);
CREATE INDEX idx_user_usage_timestamp ON user_usage(timestamp);
CREATE INDEX idx_user_usage_provider ON user_usage(provider);
```

### 3. Таблица Лимитов Пользователей

```sql
CREATE TABLE user_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    daily_limit_usd REAL DEFAULT 10.0,   -- Лимит в день
    monthly_limit_usd REAL DEFAULT 100.0, -- Лимит в месяц
    current_daily_spend REAL DEFAULT 0,
    current_monthly_spend REAL DEFAULT 0,
    last_reset_daily TEXT,
    last_reset_monthly TEXT,
    is_unlimited INTEGER DEFAULT 0,      -- Для VIP пользователей
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 4. Таблица Платежей (Payments)

```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_usd REAL NOT NULL,
    payment_method TEXT,                 -- 'stripe', 'paypal', 'crypto'
    transaction_id TEXT UNIQUE,
    status TEXT DEFAULT 'pending',       -- 'pending', 'completed', 'failed'
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 🎨 Админ-Панель (Суперадмин)

### Раздел 1: Управление Ценами

**Путь**: `/admin/pricing`

**Функции**:
- ✅ Просмотр текущих цен всех моделей
- ✅ Изменение наценки (%)
- ✅ Обновление себестоимости (когда провайдеры меняют цены)
- ✅ История изменений цен

**UI Компонент**:
```typescript
// web-ui/app/admin/pricing/page.tsx
export default function PricingAdmin() {
  const [models, setModels] = useState<Model[]>([]);
  
  return (
    <div className="p-6">
      <h1>Управление Ценами</h1>
      
      <table>
        <thead>
          <tr>
            <th>Провайдер</th>
            <th>Модель</th>
            <th>Себестоимость</th>
            <th>Наценка (%)</th>
            <th>Цена для пользователя</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {models.map(model => (
            <tr key={model.id}>
              <td>{model.provider}</td>
              <td>{model.model}</td>
              <td>${model.cost_per_1k_tokens}</td>
              <td>
                <input 
                  type="number" 
                  value={model.markup_percentage}
                  onChange={(e) => updateMarkup(model.id, e.target.value)}
                />%
              </td>
              <td>${model.price_per_1k_tokens}</td>
              <td>
                <button onClick={() => saveChanges(model.id)}>
                  Сохранить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      {/* Быстрое изменение наценки для всех */}
      <div className="mt-4">
        <label>Применить наценку ко всем моделям:</label>
        <input type="number" placeholder="20" />%
        <button onClick={applyToAll}>Применить</button>
      </div>
    </div>
  );
}
```

### Раздел 2: Аналитика Доходов

**Путь**: `/admin/analytics`

**Метрики**:
```typescript
interface RevenueMetrics {
  today: {
    totalRequests: number;
    totalTokens: number;
    platformCost: number;      // Ваши расходы
    userCharges: number;       // Заработано с пользователей
    profit: number;            // Ваша прибыль
    profitMargin: number;      // % прибыли
  };
  
  thisMonth: {
    // Те же метрики
  };
  
  topUsers: Array<{
    userId: number;
    email: string;
    spent: number;
    requests: number;
  }>;
  
  topModels: Array<{
    provider: string;
    model: string;
    usage: number;
    revenue: number;
  }>;
}
```

**Dashboard**:
```typescript
// web-ui/app/admin/analytics/page.tsx
export default function Analytics() {
  return (
    <div className="p-6">
      <h1>Аналитика Доходов</h1>
      
      {/* Карточки с ключевыми метриками */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <MetricCard 
          title="Прибыль сегодня"
          value={`$${metrics.today.profit.toFixed(2)}`}
          change="+12%"
          color="green"
        />
        <MetricCard 
          title="Всего запросов"
          value={metrics.today.totalRequests}
          change="+5%"
        />
        <MetricCard 
          title="Расходы на API"
          value={`$${metrics.today.platformCost.toFixed(2)}`}
          color="red"
        />
        <MetricCard 
          title="Маржа прибыли"
          value={`${metrics.today.profitMargin.toFixed(1)}%`}
        />
      </div>
      
      {/* График доходов по дням */}
      <RevenueChart data={revenueData} />
      
      {/* Топ пользователей по расходам */}
      <TopUsersTable users={metrics.topUsers} />
      
      {/* Использование моделей */}
      <ModelUsageChart models={metrics.topModels} />
    </div>
  );
}
```

### Раздел 3: Управление Лимитами

**Путь**: `/admin/limits`

**Функции**:
- Установка дневных/месячных лимитов для пользователей
- Создание VIP аккаунтов (без лимитов)
- Просмотр текущего использования
- Уведомления при превышении лимитов

### Раздел 4: API Ключи

**Путь**: `/admin/api-keys`

**Функции**:
- Настройка ваших API ключей (OpenAI, Anthropic, Google)
- Ротация ключей
- Мониторинг квот провайдеров
- Автоматическое переключение на backup ключи

```typescript
interface APIKeyConfig {
  provider: 'openai' | 'anthropic' | 'google';
  keyName: string;
  apiKey: string;              // Зашифровано
  isPrimary: boolean;
  quotaLimit?: number;
  currentUsage: number;
  lastUsed: Date;
  status: 'active' | 'exhausted' | 'error';
}
```

---

## 🔄 Логика Тарификации

### Backend: Расчет Стоимости

```python
# api/billing/calculator.py
from agents.database import HistoryDatabase

class BillingCalculator:
    def __init__(self, db: HistoryDatabase):
        self.db = db
    
    def calculate_cost(self, provider: str, model: str, tokens: int) -> dict:
        """
        Рассчитывает стоимость запроса
        
        Returns:
            {
                'cost_to_platform': float,    # Ваши расходы
                'charged_to_user': float,     # Цена для пользователя
                'profit': float,              # Ваша прибыль
                'markup_percentage': float    # Примененная наценка
            }
        """
        # Получить настройки цен из БД
        pricing = self.db.get_pricing_config(provider, model)
        
        if not pricing:
            raise ValueError(f"Pricing not configured for {provider}/{model}")
        
        # Рассчитать стоимость
        cost_to_platform = (tokens / 1000) * pricing['cost_per_1k_tokens']
        charged_to_user = (tokens / 1000) * pricing['price_per_1k_tokens']
        profit = charged_to_user - cost_to_platform
        
        return {
            'cost_to_platform': round(cost_to_platform, 6),
            'charged_to_user': round(charged_to_user, 6),
            'profit': round(profit, 6),
            'markup_percentage': pricing['markup_percentage']
        }
    
    def check_user_limit(self, user_id: int, amount: float) -> bool:
        """Проверяет, не превышен ли лимит пользователя"""
        limits = self.db.get_user_limits(user_id)
        
        if limits['is_unlimited']:
            return True
        
        # Проверить дневной лимит
        if limits['current_daily_spend'] + amount > limits['daily_limit_usd']:
            return False
        
        # Проверить месячный лимит
        if limits['current_monthly_spend'] + amount > limits['monthly_limit_usd']:
            return False
        
        return True
    
    def record_usage(self, user_id: int, request_id: int, 
                     provider: str, model: str, tokens: int):
        """Записывает использование и обновляет балансы"""
        
        # Рассчитать стоимость
        costs = self.calculate_cost(provider, model, tokens)
        
        # Проверить лимит
        if not self.check_user_limit(user_id, costs['charged_to_user']):
            raise Exception("User limit exceeded")
        
        # Записать в user_usage
        self.db.record_user_usage(
            user_id=user_id,
            request_id=request_id,
            provider=provider,
            model=model,
            tokens_used=tokens,
            cost_to_platform=costs['cost_to_platform'],
            charged_to_user=costs['charged_to_user'],
            profit=costs['profit']
        )
        
        # Обновить лимиты пользователя
        self.db.update_user_spend(user_id, costs['charged_to_user'])
        
        return costs
```

### Интеграция в AI Router

```python
# agents/ai_router.py
from api.billing.calculator import BillingCalculator

class AIRouter:
    def __init__(self):
        self.billing = BillingCalculator(db)
    
    async def route_request(self, user_id: int, prompt: str, 
                           model: str, **kwargs):
        """
        Маршрутизирует запрос с учетом биллинга
        """
        
        # 1. Определить провайдера и модель
        provider, model_name = self._parse_model(model)
        
        # 2. Отправить запрос к AI
        response, tokens = await self._call_ai_api(
            provider, model_name, prompt, **kwargs
        )
        
        # 3. Записать использование и рассчитать стоимость
        costs = self.billing.record_usage(
            user_id=user_id,
            request_id=request_id,
            provider=provider,
            model=model_name,
            tokens=tokens
        )
        
        # 4. Вернуть ответ с информацией о стоимости
        return {
            'response': response,
            'tokens': tokens,
            'cost': costs['charged_to_user'],
            'model': model
        }
```

---

## 💰 Пользовательская Панель (Usage Dashboard)

**Путь**: `/dashboard/usage`

**Что видит пользователь**:

```typescript
// web-ui/app/dashboard/usage/page.tsx
export default function UsageDashboard() {
  const { usage, limits } = useUsage();
  
  return (
    <div>
      <h1>Мое Использование</h1>
      
      {/* Текущий баланс и лимиты */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <h3>Потрачено сегодня</h3>
          <p className="text-2xl">${usage.today.toFixed(2)}</p>
          <Progress value={usage.today / limits.daily * 100} />
          <p className="text-sm">Лимит: ${limits.daily}</p>
        </Card>
        
        <Card>
          <h3>Потрачено в этом месяце</h3>
          <p className="text-2xl">${usage.month.toFixed(2)}</p>
          <Progress value={usage.month / limits.monthly * 100} />
          <p className="text-sm">Лимит: ${limits.monthly}</p>
        </Card>
      </div>
      
      {/* История запросов */}
      <RequestsHistory requests={usage.history} />
      
      {/* Пополнить баланс */}
      <Button onClick={() => router.push('/billing')}>
        Пополнить Баланс
      </Button>
    </div>
  );
}
```

---

## 📋 План Внедрения

### Фаза 1: База Данных (1 час)
- [ ] Создать таблицу `pricing_config`
- [ ] Создать таблицу `user_usage`
- [ ] Создать таблицу `user_limits`
- [ ] Создать таблицу `payments`
- [ ] Добавить колонку `role` в `users`
- [ ] Миграция данных

### Фаза 2: Backend Биллинг (2 часа)
- [ ] Создать `BillingCalculator`
- [ ] Интегрировать в `AIRouter`
- [ ] API для управления ценами (`/api/admin/pricing`)
- [ ] API для аналитики (`/api/admin/analytics`)
- [ ] API для управления лимитами (`/api/admin/limits`)

### Фаза 3: Админ-Панель (3 часа)
- [ ] Страница `/admin/pricing` - управление ценами
- [ ] Страница `/admin/analytics` - аналитика доходов
- [ ] Страница `/admin/limits` - управление лимитами
- [ ] Страница `/admin/api-keys` - управление ключами
- [ ] Страница `/admin/users` - управление пользователями

### Фаза 4: Пользовательский Dashboard (2 часа)
- [ ] Страница `/dashboard/usage` - использование и расходы
- [ ] Страница `/billing` - пополнение баланса
- [ ] Уведомления о лимитах
- [ ] История транзакций

### Фаза 5: Тестирование (1 час)
- [ ] Тесты расчета стоимости
- [ ] Тесты лимитов
- [ ] E2E тесты биллинга
- [ ] Тесты админ-панели

**Общее время**: ~9 часов полная система

---

## 🎯 Быстрый Старт (Минимальная Версия - 2 часа)

### 1. Добавить базовый биллинг:
```sql
-- Минимальная версия: одна таблица
ALTER TABLE requests ADD COLUMN cost_usd REAL DEFAULT 0;
ALTER TABLE requests ADD COLUMN profit_usd REAL DEFAULT 0;

-- Добавить роль суперадмина
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';
UPDATE users SET role = 'superadmin' WHERE email = 'demo@example.com';
```

### 2. Хардкод наценки (временно):
```python
# В ai_router.py
MARKUP_PERCENTAGE = 20  # 20% наценка

def calculate_cost(tokens, base_cost_per_1k):
    base_cost = (tokens / 1000) * base_cost_per_1k
    user_cost = base_cost * (1 + MARKUP_PERCENTAGE / 100)
    profit = user_cost - base_cost
    return base_cost, user_cost, profit
```

### 3. Простой dashboard:
```typescript
// Показать только общую сумму
export default function SimpleDashboard() {
  const totalSpent = useTotalSpent();
  return <div>Потрачено: ${totalSpent}</div>;
}
```

---

**Готовы начать?** Скажите, какой вариант:
1. 🚀 **Быстрый старт** (2 часа) - базовый биллинг
2. 💎 **Полная система** (9 часов) - все функции
3. 🎯 **По фазам** - внедряем постепенно
