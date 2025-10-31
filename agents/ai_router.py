"""
AI Router - умный маршрутизатор запросов к разным AI моделям
Автоматически выбирает оптимальную модель по типу задачи, сложности и бюджету
"""
import os
from typing import Literal, Optional, Dict, Any, List
import logging
from dotenv import load_dotenv
from threading import Lock
from collections import defaultdict, deque
from time import time
import anthropic
from openai import OpenAI
import google.generativeai as genai
try:
    from .database import get_db
except Exception:
    from database import get_db

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger(__name__)

# Метаданные доступных моделей для оценивания
MODELS: List[Dict[str, Any]] = [
    {
        'name': 'claude-sonnet-4-20250514',
        'best_for': ['architecture', 'research', 'code', 'chat'],
        'tier': 'premium'
    },
    {
        'name': 'gpt-4-turbo',
        'best_for': ['code', 'test', 'chat', 'general'],
        'tier': 'premium'
    },
    {
        'name': 'gpt-4o',
        'best_for': ['chat', 'vision', 'general'],
        'tier': 'premium'
    },
    {
        'name': 'deepseek/deepseek-chat',
        'best_for': ['code', 'devops', 'review'],
        'tier': 'advanced'
    },
    {
        'name': 'gemini-2.0-flash',
        'best_for': ['review', 'test', 'chat'],
        'tier': 'standard'
    },
    {
        'name': 'ollama',
        'best_for': ['chat', 'code'],
        'tier': 'basic'
    },
]

class AIRouter:
    """Центральный роутер для всех AI моделей"""
    
    def __init__(self):
        """Инициализация клиентов AI моделей"""
        # Anthropic (Claude)
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude = anthropic.Anthropic(api_key=anthropic_key) if anthropic_key else None
        
        # OpenAI (GPT)
        openai_key = os.getenv("OPENAI_API_KEY")
        self.openai = OpenAI(api_key=openai_key) if openai_key else None
        
        # OpenRouter (доступ ко многим моделям)
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=openrouter_key
        ) if openrouter_key else None
        
        # Google Gemini
        gemini_key = os.getenv("GOOGLE_AI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            self.gemini = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.gemini = None
        
        # Статистика использования
        self.stats = {
            'calls': 0,
            'tokens': 0,
            'cost': 0.0,
            'by_model': {}
        }
        
        # Модели и БД
        self.models = MODELS
        self.db = get_db()

        # Rate limiting
        self._rate_limits = defaultdict(lambda: deque())
        self._lock = Lock()
        # Лимиты по моделям (запросов в минуту)
        self._model_limits = {
            'gemini-2.0-flash': 60,
            'grok-beta': 30,
            'deepseek/deepseek-chat': 30,
            'anthropic/claude-3.5-sonnet': 50,
            'openai/gpt-4o': 50,
            'openai/gpt-4o-mini': 60,
            'ollama': 100
        }
        logger.info(f"AI Router initialized with {len(self.models)} models")

    def _check_rate_limit(self, model_name: str, wait: bool = True) -> bool:
        """
        Проверить rate limit для модели
        """
        with self._lock:
            current_time = time()
            limit = self._model_limits.get(model_name, 30)

            # Очистка старых отметок (старше 60с)
            queue = self._rate_limits[model_name]
            while queue and current_time - queue[0] > 60:
                queue.popleft()

            # Превышение лимита
            if len(queue) >= limit:
                if wait:
                    oldest = queue[0]
                    wait_time = 60 - (current_time - oldest)
                    if wait_time > 0:
                        logger.warning(f"⏱️ Rate limit hit for {model_name}, waiting {wait_time:.1f}s...")
                        import time as time_module
                        time_module.sleep(wait_time)
                        return self._check_rate_limit(model_name, wait=False)
                else:
                    logger.warning(f"🚫 Rate limit exceeded for {model_name}")
                    return False

            # Регистрируем текущий вызов
            queue.append(current_time)
            return True

    def get_rate_limit_stats(self) -> Dict:
        """Получить статистику rate limiting"""
        with self._lock:
            stats: Dict[str, Dict[str, float]] = {}
            current_time = time()
            for model_name, queue in self._rate_limits.items():
                while queue and current_time - queue[0] > 60:
                    queue.popleft()
                limit = self._model_limits.get(model_name, 30)
                used = len(queue)
                available = max(0, limit - used)
                stats[model_name] = {
                    'limit': limit,
                    'used': used,
                    'available': available,
                    'usage_percent': round((used / limit) * 100, 1) if limit else 0.0,
                }
            return stats

    def _get_model_performance(self, model: str, task_type: str = None) -> Dict:
        """
        Получить статистику производительности модели
        Returns dict: success_rate, avg_cost, avg_tokens, total_uses
        """
        try:
            import sqlite3
            
            query = """
                SELECT 
                    COUNT(*) as total_uses,
                    AVG(CASE WHEN error = 0 THEN 1 ELSE 0 END) as success_rate,
                    AVG(cost) as avg_cost,
                    AVG(tokens) as avg_tokens
                FROM requests
                WHERE model = ?
            """
            params: List[Any] = [model]
            
            if task_type:
                query += " AND task_type = ?"
                params.append(task_type)
            
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                result = dict(cursor.fetchone())
                
                if not result or result.get('total_uses', 0) == 0:
                    return {
                        'total_uses': 0,
                        'success_rate': 1.0,
                        'avg_cost': 0.0,
                        'avg_tokens': 0
                    }
                return result
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {
                'total_uses': 0,
                'success_rate': 1.0,
                'avg_cost': 0.0,
                'avg_tokens': 0
            }

    def _calculate_model_score(
        self,
        model: Dict,
        task_type: str,
        complexity: int,
        budget: str
    ) -> float:
        """
        Рассчитать score модели для данной задачи
        """
        score = 0.0
        
        # 1) Соответствие типу задачи (30)
        if task_type in model.get('best_for', []):
            score += 30
        elif task_type in ['chat', 'general']:
            score += 15
        
        # 2) История (25)
        perf = self._get_model_performance(model['name'], task_type)
        score += perf['success_rate'] * 25
        
        # 3) Бюджет (25)
        budget_match = {
            'free': ['ollama', 'gemini-2.0-flash'],
            'cheap': ['deepseek/deepseek-chat', 'gemini-2.0-flash', 'ollama'],
            'medium': ['gpt-4-turbo', 'deepseek/deepseek-chat'],
            'expensive': ['gpt-4o', 'claude-sonnet-4-20250514', 'gpt-4-turbo']
        }
        if model['name'] in budget_match.get(budget, []):
            score += 25
        elif budget == 'expensive':
            score += 15
        
        # 4) Сложность (20)
        model_tier = model.get('tier', 'medium')
        if complexity >= 8 and model_tier == 'premium':
            score += 20
        elif complexity >= 5 and model_tier in ['premium', 'advanced']:
            score += 20
        elif complexity < 5 and model_tier in ['basic', 'standard']:
            score += 20
        else:
            score += 10
        
        # Бонус за опыт (до 10)
        if perf['total_uses'] > 10:
            score += min(10, perf['total_uses'] / 10)
        
        logger.debug(f"Model {model['name']}: score={score:.1f}, perf={perf}")
        return score
    
    def route(
        self,
        prompt: str,
        task_type: str = 'chat',
        complexity: int = 5,
        budget: str = 'cheap',
        max_retries: int = 3,
        session_id: str = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Умный роутинг с кэшем, fallback и контекстом
        """
        try:
            # Проверяем кэш (только для простых запросов без сессии)
            if use_cache and not session_id:
                cached = self.db.get_cached_response(prompt, task_type)
                if cached:
                    return {
                        'response': cached['response'],
                        'model': cached['model'],
                        'tokens': len(prompt.split()) + len(cached['response'].split()),
                        'cost': 0.0,
                        'cached': True,
                        'cache_age_hours': self._get_cache_age(cached['created_at']),
                        'use_count': cached['use_count']
                    }
            
            # Контекст сессии (если указан session_id)
            context_messages: List[Dict[str, Any]] = []
            if session_id:
                context_messages = self.db.get_session_context(session_id, max_messages=10)
                logger.info(f"📚 Loaded {len(context_messages)} context messages from session {session_id}")
            
            logger.info(f"Smart routing: task={task_type}, complexity={complexity}, budget={budget}")
            
            # Рассчитываем score для каждой модели
            model_scores: List[Dict[str, Any]] = []
            for model in self.models:
                score = self._calculate_model_score(model, task_type, complexity, budget)
                model_scores.append({'model': model, 'score': score})
            model_scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Пробуем модели по очереди с fallback
            attempts: List[Dict[str, Any]] = []
            last_error: Optional[str] = None
            
            for attempt_num in range(min(max_retries, len(model_scores))):
                selected = model_scores[attempt_num]
                model = selected['model']
                try:
                    logger.info(f"🔄 Attempt {attempt_num + 1}/{max_retries}: {model['name']} (score: {selected['score']:.1f})")
                    # Формируем полный промпт с контекстом
                    full_prompt = self._build_prompt_with_context(context_messages, prompt) if context_messages else prompt
                    
                    # Проверяем rate limit
                    if not self._check_rate_limit(model['name'], wait=True):
                        raise Exception(f"Rate limit exceeded for {model['name']}")

                    # Отправляем запрос к модели через существующий исполнитель
                    result = self._execute(model['name'], full_prompt)
                    
                    # Если вызов вернулся с ошибкой — считаем как провал и пробуем следующую модель
                    if result.get('error'):
                        raise RuntimeError(result.get('response', 'Unknown model error'))
                    
                    # Успех: обновляем агрегированную статистику
                    self._update_stats(result)

                    # Сохраняем переписку в сессию (если указана)
                    if session_id:
                        try:
                            self.db.add_message_to_session(
                                session_id=session_id,
                                role='user',
                                content=prompt,
                                tokens=len(prompt.split())
                            )
                            self.db.add_message_to_session(
                                session_id=session_id,
                                role='assistant',
                                content=result.get('response', ''),
                                model=model['name'],
                                tokens=result.get('tokens', 0)
                            )
                        except Exception as persist_err:
                            logger.warning(f"Failed to persist session messages: {persist_err}")

                    # Кэшируем ответ (если нет сессии)
                    if use_cache and not session_id:
                        try:
                            self.db.cache_response(
                                prompt=prompt,
                                response=result.get('response', ''),
                                model=model['name'],
                                task_type=task_type,
                                ttl_hours=self._get_cache_ttl(task_type)
                            )
                        except Exception as cache_err:
                            logger.warning(f"Cache store failed: {cache_err}")

                    return {
                        **result,
                        'score': selected['score'],
                        'alternatives': [m['model']['name'] for m in model_scores[1:4]],
                        'attempts': attempt_num + 1,
                        'fallback_used': attempt_num > 0,
                        'failed_models': [a['model'] for a in attempts] if attempts else [],
                        'context_used': bool(context_messages),
                        'context_length': len(context_messages)
                    }
                except Exception as e:
                    logger.warning(f"⚠️ {model['name']} failed: {e}")
                    last_error = str(e)
                    attempts.append({'model': model['name'], 'error': str(e), 'score': selected['score']})
                    continue
            
            # Все модели провалились
            logger.error(f"❌ All {len(attempts)} models failed")
            return {
                'response': f"Error: All models failed. Last error: {last_error}",
                'model': 'none',
                'tokens': 0,
                'cost': 0.0,
                'error': True,
                'failed_models': [a['model'] for a in attempts],
                'attempts': len(attempts)
            }
        except Exception as e:
            logger.error(f"❌ Routing error: {e}")
            return {
                'response': f"Error: {str(e)}",
                'model': 'error',
                'tokens': 0,
                'cost': 0.0,
                'error': True
            }

    def _build_prompt_with_context(self, context_messages: List[Dict], current_prompt: str) -> str:
        """
        Построить промпт с учетом контекста
        """
        context_text = "Previous conversation:\n\n"
        for msg in context_messages[-6:]:  # последние 6 сообщений
            role = "User" if msg.get('role') == 'user' else "Assistant"
            content = msg.get('content', '')
            context_text += f"{role}: {content}\n\n"
        full_prompt = f"{context_text}User: {current_prompt}\n\nAssistant:"
        return full_prompt

    def _get_cache_age(self, created_at: str) -> float:
        """Вычислить возраст кэша в часах"""
        from datetime import datetime
        try:
            created = datetime.fromisoformat(created_at)
            age = (datetime.now() - created).total_seconds() / 3600
            return round(age, 1)
        except Exception:
            return 0.0

    def _get_cache_ttl(self, task_type: str) -> int:
        """
        Определить TTL для кэша в зависимости от типа задачи
        """
        ttl_map = {
            'chat': 1,
            'general': 1,
            'code': 24,
            'review': 24,
            'architecture': 48,
            'test': 24,
            'devops': 12,
            'research': 168
        }
        return ttl_map.get(task_type, 24)
    
    def _select_model(
        self,
        task_type: str,
        complexity: int,
        budget: str
    ) -> str:
        """
        Матрица выбора модели по задаче
        
        Приоритеты:
        - architecture: всегда Claude (самый умный)
        - code: GPT-4 или DeepSeek по сложности
        - review: Gemini (быстро и бесплатно) или DeepSeek
        - test: GPT-4 или Gemini
        - devops: DeepSeek (специализированный)
        - research: Claude (лучшее мышление)
        """
        
        # Архитектура - всегда лучшая модель
        if task_type == 'architecture':
            if self.claude:
                return 'claude-sonnet-4-20250514'
            elif self.openai:
                return 'gpt-4-turbo'
            else:
                return 'ollama'
        
        # Генерация кода - по сложности
        if task_type == 'code':
            if budget == 'free':
                if self.gemini:
                    return 'gemini-2.0-flash'
                else:
                    return 'ollama'
            elif complexity <= 6:
                if self.openrouter:
                    return 'deepseek/deepseek-chat'
                elif self.openai:
                    return 'gpt-4-turbo'
                else:
                    return 'ollama'
            else:
                if self.openai:
                    return 'gpt-4-turbo'
                elif self.claude:
                    return 'claude-sonnet-4-20250514'
                else:
                    return 'ollama'
        
        # Ревью кода - быстрые модели
        if task_type == 'review':
            if budget == 'free':
                if self.gemini:
                    return 'gemini-2.0-flash'
                else:
                    return 'ollama'
            else:
                if self.openrouter:
                    return 'deepseek/deepseek-chat'
                elif self.gemini:
                    return 'gemini-2.0-flash'
                else:
                    return 'ollama'
        
        # Тесты - средние модели
        if task_type == 'test':
            if budget != 'free' and self.openai:
                return 'gpt-4-turbo'
            elif self.gemini:
                return 'gemini-2.0-flash'
            else:
                return 'ollama'
        
        # DevOps - специализированные
        if task_type == 'devops':
            if self.openrouter:
                return 'deepseek/deepseek-chat'
            elif self.openai:
                return 'gpt-4-turbo'
            else:
                return 'ollama'
        
        # Исследования - лучшее мышление
        if task_type == 'research':
            if self.claude:
                return 'claude-sonnet-4-20250514'
            elif self.openai:
                return 'gpt-4-turbo'
            else:
                return 'ollama'
        
        # Дефолт
        return 'ollama'
    
    def _execute(self, model: str, prompt: str) -> Dict:
        """Выполнение запроса к выбранной модели"""
        
        if 'claude' in model and self.claude:
            return self._call_claude(model, prompt)
        elif 'gpt' in model and self.openai:
            return self._call_openai(model, prompt)
        elif 'deepseek' in model and self.openrouter:
            return self._call_openrouter(model, prompt)
        elif 'gemini' in model and self.gemini:
            return self._call_gemini(prompt)
        elif model == 'ollama':
            return self._call_ollama(prompt)
        else:
            raise ValueError(f"Model {model} not available or not configured")
    
    def _call_claude(self, model: str, prompt: str) -> Dict:
        """Вызов Claude API"""
        try:
            response = self.claude.messages.create(
                model=model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'response': response.content[0].text,
                'model': model,
                'tokens': response.usage.input_tokens + response.usage.output_tokens,
                'cost': self._calculate_cost(model, {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens
                }),
                'error': False
            }
        except Exception as e:
            return {
                'response': f"Claude Error: {str(e)}",
                'model': model,
                'tokens': 0,
                'cost': 0.0,
                'error': True
            }
    
    def _call_openai(self, model: str, prompt: str) -> Dict:
        """Вызов OpenAI API"""
        try:
            response = self.openai.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'response': response.choices[0].message.content,
                'model': model,
                'tokens': response.usage.total_tokens,
                'cost': self._calculate_cost(model, {
                    'input_tokens': response.usage.prompt_tokens,
                    'output_tokens': response.usage.completion_tokens
                }),
                'error': False
            }
        except Exception as e:
            return {
                'response': f"OpenAI Error: {str(e)}",
                'model': model,
                'tokens': 0,
                'cost': 0.0,
                'error': True
            }
    
    def _call_openrouter(self, model: str, prompt: str) -> Dict:
        """Вызов через OpenRouter"""
        try:
            response = self.openrouter.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'response': response.choices[0].message.content,
                'model': model,
                'tokens': response.usage.total_tokens if response.usage else 0,
                'cost': self._calculate_cost(model, {
                    'input_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'output_tokens': response.usage.completion_tokens if response.usage else 0
                }),
                'error': False
            }
        except Exception as e:
            return {
                'response': f"OpenRouter Error: {str(e)}",
                'model': model,
                'tokens': 0,
                'cost': 0.0,
                'error': True
            }
    
    def _call_gemini(self, prompt: str) -> Dict:
        """Вызов Google Gemini"""
        try:
            response = self.gemini.generate_content(prompt)
            
            return {
                'response': response.text,
                'model': 'gemini-2.0-flash',
                'tokens': int(len(prompt.split()) * 1.3),  # приблизительно
                'cost': 0.0,  # Бесплатно до лимита
                'error': False
            }
        except Exception as e:
            return {
                'response': f"Gemini Error: {str(e)}",
                'model': 'gemini-2.0-flash',
                'tokens': 0,
                'cost': 0.0,
                'error': True
            }
    
    def _call_ollama(self, prompt: str) -> Dict:
        """Локальный запрос через Ollama"""
        try:
            import subprocess
            import json
            
            # Вызов Ollama CLI
            result = subprocess.run(
                ['ollama', 'run', 'qwen2.5-coder:14b', prompt],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    'response': result.stdout.strip(),
                    'model': 'ollama-qwen2.5-coder:14b',
                    'tokens': int(len(prompt.split()) * 1.5),
                    'cost': 0.0,  # Локально бесплатно
                    'error': False
                }
            else:
                return {
                    'response': f"Ollama Error: {result.stderr}",
                    'model': 'ollama',
                    'tokens': 0,
                    'cost': 0.0,
                    'error': True
                }
        except Exception as e:
            return {
                'response': f"Ollama Error: {str(e)}. Make sure Ollama is running.",
                'model': 'ollama',
                'tokens': 0,
                'cost': 0.0,
                'error': True
            }
    
    def _calculate_cost(self, model: str, usage: Dict) -> float:
        """Расчет стоимости запроса в USD"""
        # Цены за 1M токенов (input, output)
        costs = {
            'claude-sonnet-4-20250514': (3.0, 15.0),
            'gpt-4-turbo': (10.0, 30.0),
            'gpt-4o': (5.0, 15.0),
            'deepseek/deepseek-chat': (0.27, 1.1),
            'gemini-2.0-flash': (0.0, 0.0),
            'ollama': (0.0, 0.0)
        }
        
        if model not in costs:
            return 0.0
        
        input_cost, output_cost = costs[model]
        
        total = (
            usage.get('input_tokens', 0) / 1_000_000 * input_cost +
            usage.get('output_tokens', 0) / 1_000_000 * output_cost
        )
        
        return round(total, 6)
    
    def _update_stats(self, result: Dict):
        """Обновление статистики использования"""
        if result.get('error'):
            return
        
        self.stats['calls'] += 1
        self.stats['tokens'] += result.get('tokens', 0)
        self.stats['cost'] += result.get('cost', 0.0)
        
        model = result.get('model', 'unknown')
        if model not in self.stats['by_model']:
            self.stats['by_model'][model] = {
                'calls': 0,
                'tokens': 0,
                'cost': 0.0
            }
        
        self.stats['by_model'][model]['calls'] += 1
        self.stats['by_model'][model]['tokens'] += result.get('tokens', 0)
        self.stats['by_model'][model]['cost'] += result.get('cost', 0.0)
    
    def get_stats(self) -> Dict:
        """Получить статистику использования"""
        return {
            **self.stats,
            'avg_cost_per_call': self.stats['cost'] / max(self.stats['calls'], 1),
            'available_models': self._get_available_models()
        }
    
    def _get_available_models(self) -> Dict[str, bool]:
        """Проверка доступности моделей"""
        return {
            'claude': self.claude is not None,
            'openai': self.openai is not None,
            'openrouter': self.openrouter is not None,
            'gemini': self.gemini is not None,
            'ollama': True  # Всегда доступен локально
        }

# Тестирование при прямом запуске
if __name__ == "__main__":
    print("🤖 AI Router Test\n")
    
    router = AIRouter()
    
    # Проверка доступности моделей
    print("📊 Available Models:")
    for model, available in router._get_available_models().items():
        status = "✅" if available else "❌"
        print(f"  {status} {model}")
    
    print("\n" + "="*50 + "\n")
    
    # Тест простого запроса
    print("🧪 Testing simple code generation...")
    result = router.route(
        "Write a Python function to calculate fibonacci numbers",
        task_type='code',
        complexity=3,
        budget='free'
    )
    
    print(f"Model used: {result['model']}")
    print(f"Cost: ${result['cost']:.6f}")
    print(f"Tokens: {result['tokens']}")
    print(f"\nResponse preview:\n{result['response'][:200]}...")
    
    print("\n" + "="*50 + "\n")
    
    # Статистика
    stats = router.get_stats()
    print("📈 Statistics:")
    print(f"  Total calls: {stats['calls']}")
    print(f"  Total tokens: {stats['tokens']}")
    print(f"  Total cost: ${stats['cost']:.6f}")
    print(f"  Avg cost/call: ${stats['avg_cost_per_call']:.6f}")