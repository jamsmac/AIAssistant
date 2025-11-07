# 💳 Кредитная Система с Автоматическим Выбором Моделей

**Концепция**: Пользователи работают за кредиты, система автоматически выбирает лучшие модели

---

## 🎯 Как Это Работает

### Поток Работы:

```
1. Пользователь покупает кредиты (например, $10 = 1000 кредитов)
   ↓
2. Пользователь делает запрос (без выбора модели)
   ↓
3. Система анализирует запрос и выбирает лучшую модель
   - Смотрит на рейтинг моделей
   - Учитывает сложность задачи
   - Оценивает стоимость
   ↓
4. Выбранная модель обрабатывает запрос
   ↓
5. Списываются кредиты (зависит от стоимости модели)
   ↓
6. Пользователь видит потраченные кредиты
```

### Пример:

```
Пользователь: "Напиши код для сортировки массива"
↓
Система анализирует: Простая задача → выбирает GPT-3.5-turbo
↓
Стоимость: 2 кредита
↓
Баланс: 1000 → 998 кредитов
```

```
Пользователь: "Создай сложную архитектуру микросервисов"
↓
Система анализирует: Сложная задача → выбирает Claude-3-opus
↓
Стоимость: 15 кредитов
↓
Баланс: 998 → 983 кредита
```

---

## 🏗️ Архитектура Базы Данных

### 1. Таблица Кредитов Пользователей

```sql
CREATE TABLE user_credits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    balance INTEGER NOT NULL DEFAULT 0,        -- Текущий баланс кредитов
    total_purchased INTEGER DEFAULT 0,         -- Всего куплено кредитов
    total_spent INTEGER DEFAULT 0,             -- Всего потрачено кредитов
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Индекс для быстрого доступа
CREATE INDEX idx_user_credits_user ON user_credits(user_id);
```

### 2. Таблица Транзакций Кредитов

```sql
CREATE TABLE credit_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,                        -- 'purchase', 'spend', 'refund', 'bonus'
    amount INTEGER NOT NULL,                   -- Положительное для purchase, отрицательное для spend
    balance_before INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    description TEXT,                          -- Например: "Used GPT-4 for code generation"
    request_id INTEGER,                        -- Ссылка на requests (если это расход)
    payment_id INTEGER,                        -- Ссылка на payments (если это покупка)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (request_id) REFERENCES requests(id),
    FOREIGN KEY (payment_id) REFERENCES payments(id)
);

-- Индексы
CREATE INDEX idx_credit_trans_user ON credit_transactions(user_id);
CREATE INDEX idx_credit_trans_type ON credit_transactions(type);
CREATE INDEX idx_credit_trans_created ON credit_transactions(created_at);
```

### 3. Таблица Пакетов Кредитов (Credit Packages)

```sql
CREATE TABLE credit_packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,                        -- "Starter", "Professional", "Enterprise"
    credits INTEGER NOT NULL,                  -- Количество кредитов
    price_usd REAL NOT NULL,                   -- Цена в USD
    bonus_credits INTEGER DEFAULT 0,           -- Бонусные кредиты
    discount_percentage REAL DEFAULT 0,        -- Скидка (%)
    is_active INTEGER DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Примеры пакетов:
INSERT INTO credit_packages (name, credits, price_usd, bonus_credits, discount_percentage, display_order) VALUES
('Starter', 100, 10, 0, 0, 1),              -- $10 = 100 кредитов ($0.10 за кредит)
('Basic', 500, 45, 25, 10, 2),              -- $45 = 500+25 кредитов, скидка 10%
('Professional', 1000, 80, 100, 20, 3),     -- $80 = 1000+100 кредитов, скидка 20%
('Enterprise', 5000, 350, 750, 30, 4);      -- $350 = 5000+750 кредитов, скидка 30%
```

### 4. Таблица Стоимости Моделей в Кредитах

```sql
CREATE TABLE model_credit_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    credits_per_1k_tokens INTEGER NOT NULL,    -- Стоимость в кредитах
    base_cost_usd REAL NOT NULL,               -- Базовая стоимость в USD (для справки)
    markup_percentage REAL NOT NULL,           -- Наценка (%)
    is_active INTEGER DEFAULT 1,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider, model)
);

-- Примеры стоимости:
INSERT INTO model_credit_costs (provider, model, credits_per_1k_tokens, base_cost_usd, markup_percentage) VALUES
-- Дешевые модели (для простых задач)
('openai', 'gpt-3.5-turbo', 2, 0.002, 20),           -- 2 кредита за 1K токенов
('google', 'gemini-pro', 1, 0.00025, 20),            -- 1 кредит за 1K токенов
('anthropic', 'claude-3-haiku', 3, 0.0025, 20),      -- 3 кредита за 1K токенов

-- Средние модели (для обычных задач)
('openai', 'gpt-4-turbo', 10, 0.01, 20),             -- 10 кредитов за 1K токенов
('anthropic', 'claude-3-sonnet', 4, 0.003, 20),      -- 4 кредита за 1K токенов

-- Дорогие модели (для сложных задач)
('openai', 'gpt-4', 30, 0.03, 20),                   -- 30 кредитов за 1K токенов
('anthropic', 'claude-3-opus', 18, 0.015, 20),       -- 18 кредитов за 1K токенов
('openai', 'o1-preview', 150, 0.15, 20);             -- 150 кредитов за 1K токенов
```

### 5. Таблица Рейтингов Моделей (уже есть)

```sql
-- Расширяем существующую таблицу
ALTER TABLE ai_model_rankings ADD COLUMN use_case TEXT;  -- 'coding', 'writing', 'analysis', 'general'
ALTER TABLE ai_model_rankings ADD COLUMN complexity TEXT; -- 'simple', 'medium', 'complex'
ALTER TABLE ai_model_rankings ADD COLUMN cost_tier TEXT;  -- 'cheap', 'medium', 'expensive'

-- Примеры данных:
UPDATE ai_model_rankings SET 
    use_case = 'coding',
    complexity = 'simple',
    cost_tier = 'cheap'
WHERE model_name = 'gpt-3.5-turbo' AND category = 'code_generation';

UPDATE ai_model_rankings SET 
    use_case = 'coding',
    complexity = 'complex',
    cost_tier = 'expensive'
WHERE model_name = 'gpt-4' AND category = 'code_generation';
```

---

## 🤖 Система Автоматического Выбора Моделей

### Backend: Model Selector

```python
# agents/model_selector.py
from typing import Dict, Optional, List
from agents.database import HistoryDatabase
import re

class ModelSelector:
    """
    Автоматический выбор модели на основе:
    - Типа задачи
    - Сложности запроса
    - Рейтинга моделей
    - Бюджета пользователя
    """
    
    def __init__(self, db: HistoryDatabase):
        self.db = db
        
        # Ключевые слова для определения типа задачи
        self.task_keywords = {
            'coding': ['код', 'code', 'программ', 'function', 'class', 'debug', 'ошибка'],
            'writing': ['напиши', 'write', 'статья', 'article', 'текст', 'essay'],
            'analysis': ['анализ', 'analyze', 'compare', 'evaluate', 'review'],
            'translation': ['перевед', 'translate', 'translation'],
            'math': ['вычисли', 'calculate', 'формула', 'equation', 'math'],
        }
        
        # Определение сложности по длине и ключевым словам
        self.complexity_indicators = {
            'simple': ['простой', 'simple', 'quick', 'быстро'],
            'complex': ['сложный', 'complex', 'detailed', 'comprehensive', 'архитектура']
        }
    
    def analyze_prompt(self, prompt: str) -> Dict:
        """
        Анализирует запрос и определяет параметры
        """
        prompt_lower = prompt.lower()
        
        # Определить тип задачи
        task_type = 'general'
        for task, keywords in self.task_keywords.items():
            if any(keyword in prompt_lower for keyword in keywords):
                task_type = task
                break
        
        # Определить сложность
        complexity = 'medium'
        
        # Простая задача: короткий запрос или ключевые слова простоты
        if len(prompt) < 100 or any(kw in prompt_lower for kw in self.complexity_indicators['simple']):
            complexity = 'simple'
        
        # Сложная задача: длинный запрос или ключевые слова сложности
        if len(prompt) > 500 or any(kw in prompt_lower for kw in self.complexity_indicators['complex']):
            complexity = 'complex'
        
        # Оценить примерную длину ответа (токены)
        estimated_tokens = self._estimate_tokens(prompt)
        
        return {
            'task_type': task_type,
            'complexity': complexity,
            'estimated_tokens': estimated_tokens,
            'prompt_length': len(prompt)
        }
    
    def select_model(self, prompt: str, user_credits: int, 
                     prefer_cheap: bool = False) -> Dict:
        """
        Выбирает лучшую модель для запроса
        
        Returns:
            {
                'provider': str,
                'model': str,
                'estimated_cost_credits': int,
                'reason': str
            }
        """
        # Анализировать запрос
        analysis = self.analyze_prompt(prompt)
        
        # Получить доступные модели из рейтинга
        models = self.db.get_top_models_for_task(
            task_type=analysis['task_type'],
            complexity=analysis['complexity']
        )
        
        # Если нет специализированных моделей, взять общие
        if not models:
            models = self.db.get_top_models_for_task(
                task_type='general',
                complexity=analysis['complexity']
            )
        
        # Получить стоимость каждой модели в кредитах
        models_with_cost = []
        for model in models:
            cost_info = self.db.get_model_cost_credits(
                provider=model['provider'],
                model=model['model_name']
            )
            if cost_info:
                estimated_cost = self._estimate_request_cost(
                    analysis['estimated_tokens'],
                    cost_info['credits_per_1k_tokens']
                )
                
                # Проверить, хватит ли кредитов
                if estimated_cost <= user_credits:
                    models_with_cost.append({
                        'provider': model['provider'],
                        'model': model['model_name'],
                        'rank': model['rank'],
                        'score': model['score'],
                        'estimated_cost': estimated_cost,
                        'cost_tier': cost_info['cost_tier']
                    })
        
        if not models_with_cost:
            raise Exception("Insufficient credits for any available model")
        
        # Выбрать модель
        if prefer_cheap:
            # Выбрать самую дешевую с хорошим рейтингом
            selected = min(models_with_cost, 
                         key=lambda x: (x['estimated_cost'], -x['score']))
        else:
            # Выбрать лучшую по рейтингу с учетом стоимости
            # Баланс между качеством и ценой
            for model in sorted(models_with_cost, key=lambda x: x['rank']):
                # Если модель в топ-3 и доступна по цене, выбираем её
                if model['rank'] <= 3:
                    selected = model
                    break
            else:
                # Если нет топовых, выбрать лучшую доступную
                selected = models_with_cost[0]
        
        return {
            'provider': selected['provider'],
            'model': selected['model'],
            'estimated_cost_credits': selected['estimated_cost'],
            'reason': f"Selected {selected['model']} (rank #{selected['rank']}) for {analysis['task_type']} task",
            'analysis': analysis
        }
    
    def _estimate_tokens(self, text: str) -> int:
        """Оценивает количество токенов (примерно 1 токен = 4 символа)"""
        return len(text) // 4 + 500  # +500 для ответа
    
    def _estimate_request_cost(self, estimated_tokens: int, 
                               credits_per_1k: int) -> int:
        """Вычисляет стоимость запроса в кредитах"""
        return int((estimated_tokens / 1000) * credits_per_1k) + 1
```

### Интеграция в AI Router

```python
# agents/ai_router.py
from agents.model_selector import ModelSelector
from agents.credit_manager import CreditManager

class AIRouter:
    def __init__(self):
        self.model_selector = ModelSelector(db)
        self.credit_manager = CreditManager(db)
    
    async def route_request(self, user_id: int, prompt: str, 
                           prefer_cheap: bool = False):
        """
        Маршрутизирует запрос с автоматическим выбором модели
        """
        
        # 1. Получить баланс кредитов пользователя
        user_credits = self.credit_manager.get_balance(user_id)
        
        if user_credits <= 0:
            raise Exception("Insufficient credits. Please purchase more.")
        
        # 2. Выбрать модель автоматически
        selection = self.model_selector.select_model(
            prompt=prompt,
            user_credits=user_credits,
            prefer_cheap=prefer_cheap
        )
        
        # 3. Зарезервировать кредиты (оптимистичная блокировка)
        self.credit_manager.reserve_credits(
            user_id=user_id,
            amount=selection['estimated_cost_credits']
        )
        
        try:
            # 4. Отправить запрос к выбранной модели
            response, actual_tokens = await self._call_ai_api(
                provider=selection['provider'],
                model=selection['model'],
                prompt=prompt
            )
            
            # 5. Рассчитать фактическую стоимость
            actual_cost = self._calculate_actual_cost(
                provider=selection['provider'],
                model=selection['model'],
                tokens=actual_tokens
            )
            
            # 6. Списать кредиты (фактическая стоимость)
            self.credit_manager.charge_credits(
                user_id=user_id,
                amount=actual_cost,
                description=f"Used {selection['model']} - {selection['analysis']['task_type']} task",
                request_id=request_id
            )
            
            # 7. Вернуть ответ с информацией
            return {
                'response': response,
                'model_used': selection['model'],
                'credits_spent': actual_cost,
                'remaining_credits': user_credits - actual_cost,
                'tokens_used': actual_tokens,
                'selection_reason': selection['reason']
            }
            
        except Exception as e:
            # Откатить резервирование при ошибке
            self.credit_manager.release_reserved_credits(user_id)
            raise e
```

### Credit Manager

```python
# agents/credit_manager.py
class CreditManager:
    """
    Управление кредитами пользователей
    """
    
    def __init__(self, db: HistoryDatabase):
        self.db = db
    
    def get_balance(self, user_id: int) -> int:
        """Получить текущий баланс кредитов"""
        credits = self.db.get_user_credits(user_id)
        return credits['balance'] if credits else 0
    
    def add_credits(self, user_id: int, amount: int, 
                   transaction_type: str = 'purchase',
                   description: str = None, payment_id: int = None):
        """Добавить кредиты пользователю"""
        
        current_balance = self.get_balance(user_id)
        new_balance = current_balance + amount
        
        # Обновить баланс
        self.db.update_user_credits(user_id, new_balance)
        
        # Записать транзакцию
        self.db.record_credit_transaction(
            user_id=user_id,
            type=transaction_type,
            amount=amount,
            balance_before=current_balance,
            balance_after=new_balance,
            description=description or f"Added {amount} credits",
            payment_id=payment_id
        )
        
        return new_balance
    
    def charge_credits(self, user_id: int, amount: int,
                      description: str = None, request_id: int = None):
        """Списать кредиты у пользователя"""
        
        current_balance = self.get_balance(user_id)
        
        if current_balance < amount:
            raise Exception(f"Insufficient credits. Have: {current_balance}, Need: {amount}")
        
        new_balance = current_balance - amount
        
        # Обновить баланс
        self.db.update_user_credits(user_id, new_balance)
        
        # Записать транзакцию
        self.db.record_credit_transaction(
            user_id=user_id,
            type='spend',
            amount=-amount,  # Отрицательное значение
            balance_before=current_balance,
            balance_after=new_balance,
            description=description or f"Spent {amount} credits",
            request_id=request_id
        )
        
        return new_balance
    
    def reserve_credits(self, user_id: int, amount: int):
        """
        Зарезервировать кредиты перед запросом
        (временная блокировка для предотвращения overdraft)
        """
        # Можно использовать Redis для временной резервации
        # Или добавить поле 'reserved_credits' в user_credits
        pass
    
    def get_transaction_history(self, user_id: int, 
                                limit: int = 50) -> List[Dict]:
        """Получить историю транзакций"""
        return self.db.get_credit_transactions(user_id, limit)
```

---

## 🎨 UI Компоненты

### 1. Покупка Кредитов

```typescript
// web-ui/app/credits/buy/page.tsx
export default function BuyCredits() {
  const [packages, setPackages] = useState<CreditPackage[]>([]);
  
  return (
    <div className="p-6">
      <h1>Купить Кредиты</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {packages.map(pkg => (
          <CreditPackageCard
            key={pkg.id}
            name={pkg.name}
            credits={pkg.credits}
            bonus={pkg.bonus_credits}
            price={pkg.price_usd}
            discount={pkg.discount_percentage}
            onSelect={() => handlePurchase(pkg)}
          />
        ))}
      </div>
      
      {/* Кастомная сумма */}
      <CustomAmountForm />
    </div>
  );
}

function CreditPackageCard({ name, credits, bonus, price, discount, onSelect }) {
  const totalCredits = credits + bonus;
  const pricePerCredit = (price / totalCredits).toFixed(3);
  
  return (
    <div className="border rounded-lg p-6 hover:shadow-lg transition">
      <h3 className="text-xl font-bold">{name}</h3>
      
      <div className="my-4">
        <p className="text-3xl font-bold">{credits}</p>
        <p className="text-sm text-gray-500">кредитов</p>
        {bonus > 0 && (
          <p className="text-green-500">+{bonus} бонус!</p>
        )}
      </div>
      
      <div className="mb-4">
        <p className="text-2xl font-bold">${price}</p>
        <p className="text-sm text-gray-500">
          ${pricePerCredit} за кредит
        </p>
        {discount > 0 && (
          <span className="bg-red-500 text-white px-2 py-1 rounded text-sm">
            -{discount}%
          </span>
        )}
      </div>
      
      <button onClick={onSelect} className="w-full btn-primary">
        Купить
      </button>
    </div>
  );
}
```

### 2. Dashboard Кредитов

```typescript
// web-ui/app/dashboard/credits/page.tsx
export default function CreditsDashboard() {
  const { balance, history, stats } = useCredits();
  
  return (
    <div className="p-6">
      {/* Текущий баланс */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg p-6 text-white mb-6">
        <h2 className="text-xl mb-2">Ваш Баланс</h2>
        <p className="text-5xl font-bold">{balance}</p>
        <p className="text-sm">кредитов</p>
        
        <button className="mt-4 bg-white text-blue-500 px-4 py-2 rounded">
          Купить Еще
        </button>
      </div>
      
      {/* Статистика */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <StatCard title="Потрачено сегодня" value={stats.spentToday} />
        <StatCard title="Всего потрачено" value={stats.totalSpent} />
        <StatCard title="Всего куплено" value={stats.totalPurchased} />
      </div>
      
      {/* История транзакций */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-bold mb-4">История Транзакций</h3>
        <table className="w-full">
          <thead>
            <tr>
              <th>Дата</th>
              <th>Тип</th>
              <th>Описание</th>
              <th>Кредиты</th>
              <th>Баланс</th>
            </tr>
          </thead>
          <tbody>
            {history.map(tx => (
              <tr key={tx.id}>
                <td>{formatDate(tx.created_at)}</td>
                <td>
                  <TransactionTypeBadge type={tx.type} />
                </td>
                <td>{tx.description}</td>
                <td className={tx.amount > 0 ? 'text-green-500' : 'text-red-500'}>
                  {tx.amount > 0 ? '+' : ''}{tx.amount}
                </td>
                <td>{tx.balance_after}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

### 3. Индикатор Стоимости в Чате

```typescript
// web-ui/components/ChatInput.tsx
export default function ChatInput({ onSend }) {
  const [message, setMessage] = useState('');
  const [estimatedCost, setEstimatedCost] = useState(0);
  const { balance } = useCredits();
  
  // Оценивать стоимость по мере ввода
  useEffect(() => {
    if (message.length > 10) {
      const cost = estimateMessageCost(message);
      setEstimatedCost(cost);
    }
  }, [message]);
  
  return (
    <div className="chat-input">
      <textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Введите ваш запрос..."
      />
      
      {/* Индикатор стоимости */}
      <div className="flex justify-between items-center mt-2">
        <div className="text-sm text-gray-500">
          Примерная стоимость: ~{estimatedCost} кредитов
        </div>
        <div className="text-sm">
          Баланс: {balance} кредитов
        </div>
      </div>
      
      <button 
        onClick={() => onSend(message)}
        disabled={balance < estimatedCost}
      >
        Отправить
      </button>
    </div>
  );
}
```

---

## 🎯 Админ-Панель для Суперадмина

### 1. Управление Пакетами Кредитов

```typescript
// web-ui/app/admin/credit-packages/page.tsx
export default function CreditPackagesAdmin() {
  return (
    <div>
      <h1>Управление Пакетами Кредитов</h1>
      
      <table>
        <thead>
          <tr>
            <th>Название</th>
            <th>Кредиты</th>
            <th>Бонус</th>
            <th>Цена</th>
            <th>Скидка</th>
            <th>$/кредит</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {packages.map(pkg => (
            <tr key={pkg.id}>
              <td><input value={pkg.name} onChange={...} /></td>
              <td><input type="number" value={pkg.credits} /></td>
              <td><input type="number" value={pkg.bonus_credits} /></td>
              <td><input type="number" value={pkg.price_usd} /></td>
              <td><input type="number" value={pkg.discount_percentage} />%</td>
              <td>${(pkg.price_usd / (pkg.credits + pkg.bonus_credits)).toFixed(3)}</td>
              <td>
                <button onClick={() => save(pkg)}>Сохранить</button>
                <button onClick={() => delete(pkg)}>Удалить</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      
      <button onClick={addNew}>+ Новый Пакет</button>
    </div>
  );
}
```

### 2. Настройка Стоимости Моделей

```typescript
// web-ui/app/admin/model-costs/page.tsx
export default function ModelCostsAdmin() {
  return (
    <div>
      <h1>Стоимость Моделей в Кредитах</h1>
      
      <table>
        <thead>
          <tr>
            <th>Провайдер</th>
            <th>Модель</th>
            <th>Кредитов/1K токенов</th>
            <th>Базовая стоимость USD</th>
            <th>Наценка %</th>
            <th>Активна</th>
          </tr>
        </thead>
        <tbody>
          {models.map(model => (
            <tr key={model.id}>
              <td>{model.provider}</td>
              <td>{model.model}</td>
              <td>
                <input 
                  type="number" 
                  value={model.credits_per_1k_tokens}
                  onChange={(e) => updateCost(model.id, e.target.value)}
                />
              </td>
              <td>${model.base_cost_usd}</td>
              <td>{model.markup_percentage}%</td>
              <td>
                <Toggle 
                  checked={model.is_active}
                  onChange={(v) => toggleActive(model.id, v)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

---

## 📊 Аналитика для Суперадмина

```typescript
// web-ui/app/admin/analytics/credits/page.tsx
export default function CreditsAnalytics() {
  return (
    <div>
      <h1>Аналитика Кредитов</h1>
      
      {/* Ключевые метрики */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard 
          title="Продано кредитов (сегодня)"
          value={metrics.creditsСoldToday}
          revenue={`$${metrics.revenueToday}`}
        />
        <MetricCard 
          title="Использовано кредитов"
          value={metrics.creditsSpentToday}
        />
        <MetricCard 
          title="Активных пользователей"
          value={metrics.activeUsers}
        />
        <MetricCard 
          title="Средний чек"
          value={`$${metrics.averagePurchase}`}
        />
      </div>
      
      {/* График продаж кредитов */}
      <CreditSalesChart data={salesData} />
      
      {/* Популярные пакеты */}
      <PopularPackagesChart packages={packageStats} />
      
      {/* Топ пользователей по расходам */}
      <TopSpendersTable users={topSpenders} />
    </div>
  );
}
```

---

## 🚀 План Внедрения

### Фаза 1: База Данных (1 час)
- [ ] Создать таблицу `user_credits`
- [ ] Создать таблицу `credit_transactions`
- [ ] Создать таблицу `credit_packages`
- [ ] Создать таблицу `model_credit_costs`
- [ ] Расширить `ai_model_rankings`

### Фаза 2: Backend - Credit System (2 часа)
- [ ] Создать `CreditManager`
- [ ] API для покупки кредитов (`/api/credits/purchase`)
- [ ] API для получения баланса (`/api/credits/balance`)
- [ ] API истории транзакций (`/api/credits/history`)
- [ ] Webhook для платежей (Stripe/PayPal)

### Фаза 3: Backend - Model Selector (2 часа)
- [ ] Создать `ModelSelector`
- [ ] Интегрировать в `AIRouter`
- [ ] API для оценки стоимости (`/api/estimate-cost`)
- [ ] Система резервации кредитов

### Фаза 4: Frontend - User (2 часа)
- [ ] Страница покупки кредитов (`/credits/buy`)
- [ ] Dashboard кредитов (`/dashboard/credits`)
- [ ] Индикатор баланса в навигации
- [ ] Индикатор стоимости в чате

### Фаза 5: Frontend - Admin (2 часа)
- [ ] Управление пакетами кредитов
- [ ] Настройка стоимости моделей
- [ ] Аналитика продаж кредитов
- [ ] Управление балансами пользователей

### Фаза 6: Тестирование (1 час)
- [ ] Тесты расчета стоимости
- [ ] Тесты списания кредитов
- [ ] Тесты выбора моделей
- [ ] E2E тесты покупки

**Общее время**: ~10 часов полная система

---

## 🎯 Быстрый Старт (3 часа)

### Минимальная версия:

1. **База** (30 мин):
```sql
CREATE TABLE user_credits (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
);

ALTER TABLE requests ADD COLUMN credits_spent INTEGER DEFAULT 0;
```

2. **Backend** (1.5 часа):
```python
# Простой credit manager
class SimpleCreditManager:
    def charge(user_id, credits):
        # Списать кредиты
        pass
    
    def get_balance(user_id):
        # Получить баланс
        pass
```

3. **Frontend** (1 час):
```typescript
// Показать баланс и историю
function CreditsWidget() {
  return <div>Баланс: {balance} кредитов</div>
}
```

---

**Готовы начать внедрение?** 🚀
