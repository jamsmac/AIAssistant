"""
CSRF Protection для FastAPI
Защита от межсайтовой подделки запросов
"""

import secrets
import hmac
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta


class CSRFProtection:
    """Защита от CSRF атак с использованием токенов"""

    def __init__(self, secret_key: str, token_lifetime: int = 3600):
        """
        Args:
            secret_key: Секретный ключ для подписи токенов
            token_lifetime: Время жизни токена в секундах (по умолчанию 1 час)
        """
        self.secret_key = secret_key
        self.token_lifetime = token_lifetime
        # Хранилище токенов: {token: expiry_time}
        self.tokens: Dict[str, datetime] = {}

    def generate_token(self, user_id: Optional[str] = None) -> str:
        """
        Генерирует новый CSRF токен

        Args:
            user_id: ID пользователя (опционально, для привязки токена)

        Returns:
            CSRF токен
        """
        # Генерируем случайный токен
        token = secrets.token_urlsafe(32)

        # Если указан user_id, добавляем его к токену
        if user_id:
            token = f"{user_id}:{token}"

        # Подписываем токен
        signature = self._sign_token(token)
        signed_token = f"{token}.{signature}"

        # Сохраняем токен с временем истечения
        expiry = datetime.utcnow() + timedelta(seconds=self.token_lifetime)
        self.tokens[signed_token] = expiry

        # Очищаем устаревшие токены
        self._cleanup_expired_tokens()

        return signed_token

    def verify_token(self, token: str, user_id: Optional[str] = None) -> bool:
        """
        Проверяет валидность CSRF токена

        Args:
            token: CSRF токен для проверки
            user_id: ID пользователя (если токен привязан к пользователю)

        Returns:
            True если токен валидный, False иначе
        """
        if not token:
            return False

        # Проверяем наличие токена в хранилище
        if token not in self.tokens:
            return False

        # Проверяем срок действия
        if datetime.utcnow() > self.tokens[token]:
            del self.tokens[token]
            return False

        # Проверяем подпись
        try:
            token_part, signature = token.rsplit('.', 1)
            expected_signature = self._sign_token(token_part)

            if not hmac.compare_digest(signature, expected_signature):
                return False

            # Если токен привязан к пользователю, проверяем соответствие
            if user_id and ':' in token_part:
                token_user_id, _ = token_part.split(':', 1)
                if token_user_id != str(user_id):
                    return False

        except (ValueError, AttributeError):
            return False

        # Удаляем одноразовый токен после использования
        # (опционально - можно оставить для повторного использования)
        # del self.tokens[token]

        return True

    def _sign_token(self, token: str) -> str:
        """Подписывает токен используя HMAC"""
        return hmac.new(
            self.secret_key.encode(),
            token.encode(),
            hashlib.sha256
        ).hexdigest()

    def _cleanup_expired_tokens(self):
        """Удаляет истекшие токены из хранилища"""
        current_time = datetime.utcnow()
        expired = [
            token for token, expiry in self.tokens.items()
            if current_time > expiry
        ]
        for token in expired:
            del self.tokens[token]

    def get_token_from_header(self, csrf_header: Optional[str]) -> Optional[str]:
        """
        Извлекает CSRF токен из заголовка

        Args:
            csrf_header: Значение заголовка X-CSRF-Token

        Returns:
            CSRF токен или None
        """
        if not csrf_header:
            return None

        # Убираем префикс если есть
        if csrf_header.startswith("Bearer "):
            return csrf_header[7:]

        return csrf_header


# Глобальный экземпляр для использования в приложении
_csrf_protection = None


def get_csrf_protection(secret_key: Optional[str] = None) -> CSRFProtection:
    """Получить экземпляр CSRF Protection"""
    global _csrf_protection

    if _csrf_protection is None:
        if not secret_key:
            import os
            secret_key = os.getenv('SECRET_KEY', 'default-secret-key-change-in-production')
        _csrf_protection = CSRFProtection(secret_key)

    return _csrf_protection