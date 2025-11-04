"""
Rate Limiter для защиты API endpoints от злоупотреблений

Поддерживает:
- Множественные уровни доступа (anonymous, authenticated, premium)
- Временные окна (sliding window)
- Хранение в памяти (можно заменить на Redis)
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import time


class RateLimiter:
    """Rate limiter с поддержкой различных тарифов"""

    def __init__(self):
        # Хранилище: {identifier: [(timestamp, count), ...]}
        self.requests: Dict[str, deque] = defaultdict(deque)

        # Лимиты: (requests_per_window, window_seconds)
        self.limits = {
            'anonymous': (10, 60),      # 10 запросов в минуту
            'authenticated': (100, 60),  # 100 запросов в минуту
            'premium': (1000, 60),      # 1000 запросов в минуту
            'health': (1000, 60),       # Health check - без лимита
        }

    def check_rate_limit(
        self,
        identifier: str,
        tier: str = 'anonymous'
    ) -> bool:
        """
        Проверяет, не превышен ли rate limit

        Args:
            identifier: Уникальный идентификатор (IP или user_id)
            tier: Уровень доступа (anonymous, authenticated, premium)

        Returns:
            True если запрос разрешён, False если лимит превышен
        """
        if tier not in self.limits:
            tier = 'anonymous'

        max_requests, window_seconds = self.limits[tier]

        # Получаем текущее время
        now = time.time()
        window_start = now - window_seconds

        # Получаем очередь запросов для данного identifier
        request_queue = self.requests[identifier]

        # Удаляем старые записи (за пределами окна)
        while request_queue and request_queue[0] < window_start:
            request_queue.popleft()

        # Проверяем лимит
        if len(request_queue) >= max_requests:
            return False

        # Добавляем новый запрос
        request_queue.append(now)

        return True

    def get_remaining(
        self,
        identifier: str,
        tier: str = 'anonymous'
    ) -> int:
        """
        Возвращает количество оставшихся запросов

        Args:
            identifier: Уникальный идентификатор
            tier: Уровень доступа

        Returns:
            Количество доступных запросов
        """
        if tier not in self.limits:
            tier = 'anonymous'

        max_requests, window_seconds = self.limits[tier]

        # Получаем текущее время
        now = time.time()
        window_start = now - window_seconds

        # Получаем очередь запросов
        request_queue = self.requests[identifier]

        # Удаляем старые записи
        while request_queue and request_queue[0] < window_start:
            request_queue.popleft()

        # Возвращаем оставшиеся запросы
        return max(0, max_requests - len(request_queue))

    def get_reset_time(
        self,
        identifier: str,
        tier: str = 'anonymous'
    ) -> int:
        """
        Возвращает время (в секундах) до сброса лимита

        Args:
            identifier: Уникальный идентификатор
            tier: Уровень доступа

        Returns:
            Секунды до сброса, или 0 если очередь пуста
        """
        if tier not in self.limits:
            tier = 'anonymous'

        _, window_seconds = self.limits[tier]

        # Получаем очередь запросов
        request_queue = self.requests[identifier]

        if not request_queue:
            return 0

        # Время до истечения самого старого запроса
        oldest_request = request_queue[0]
        now = time.time()
        reset_time = oldest_request + window_seconds - now

        return max(0, int(reset_time))

    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """
        Удаляет старые записи для экономии памяти

        Args:
            max_age_seconds: Максимальный возраст записей в секундах
        """
        now = time.time()
        cutoff = now - max_age_seconds

        # Удаляем пустые очереди и очень старые записи
        to_delete = []
        for identifier, request_queue in self.requests.items():
            # Удаляем старые записи
            while request_queue and request_queue[0] < cutoff:
                request_queue.popleft()

            # Если очередь пустая, помечаем на удаление
            if not request_queue:
                to_delete.append(identifier)

        # Удаляем пустые очереди
        for identifier in to_delete:
            del self.requests[identifier]


# Глобальный экземпляр rate limiter
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Получить глобальный экземпляр rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
