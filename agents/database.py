"""
Database module для хранения истории запросов к AI
Использует SQLite для локального хранения
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = Path(__file__).parent.parent / "data" / "history.db"
DB_PATH.parent.mkdir(exist_ok=True)


class HistoryDatabase:
    """Управление историей запросов к AI"""
    
    def __init__(self, db_path: str = str(DB_PATH)):
        """Инициализация базы данных"""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Создание таблиц если их нет"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT NOT NULL,
                    task_type TEXT,
                    complexity INTEGER,
                    budget TEXT,
                    tokens INTEGER,
                    cost REAL,
                    error INTEGER DEFAULT 0,
                    user_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для быстрого поиска
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON requests(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model 
                ON requests(model)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_task_type 
                ON requests(task_type)
            """)
            
            # Таблица пользователей (для аутентификации)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TEXT,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Индекс на email (дополнительно к UNIQUE для планов запросов)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users(email)
            """)
            
            # Таблица рейтингов AI моделей
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_model_rankings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    rank INTEGER NOT NULL,
                    score REAL NOT NULL,
                    source_id INTEGER,
                    notes TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, model_name)
                )
            """)
            
            # Таблица доверенных источников
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trusted_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    data_type TEXT,
                    reliability TEXT,
                    format TEXT,
                    last_checked_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Индексы для рейтингов
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rankings_category 
                ON ai_model_rankings(category, rank)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def add_request(
        self,
        prompt: str,
        response: str,
        model: str,
        task_type: str = None,
        complexity: int = None,
        budget: str = None,
        tokens: int = 0,
        cost: float = 0.0,
        error: bool = False,
        user_id: str = None
    ) -> int:
        """
        Добавить запрос в историю
        
        Returns:
            ID созданной записи
        """
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO requests (
                    timestamp, prompt, response, model, task_type,
                    complexity, budget, tokens, cost, error, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, prompt, response, model, task_type,
                complexity, budget, tokens, cost, int(error), user_id
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        model: Optional[str] = None,
        task_type: Optional[str] = None,
        min_cost: Optional[float] = None,
        max_cost: Optional[float] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict]:
        """
        Получить историю запросов с фильтрами
        
        Args:
            limit: Количество записей
            offset: Смещение для пагинации
            model: Фильтр по модели
            task_type: Фильтр по типу задачи
            min_cost: Минимальная стоимость
            max_cost: Максимальная стоимость
            start_date: Начало периода (ISO format)
            end_date: Конец периода (ISO format)
            search: Поиск по тексту prompt
        
        Returns:
            Список записей
        """
        query = "SELECT * FROM requests WHERE 1=1"
        params = []
        
        # Фильтры
        if model:
            query += " AND model = ?"
            params.append(model)
        
        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)
        
        if min_cost is not None:
            query += " AND cost >= ?"
            params.append(min_cost)
        
        if max_cost is not None:
            query += " AND cost <= ?"
            params.append(max_cost)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        if search:
            query += " AND (prompt LIKE ? OR response LIKE ?)"
            search_pattern = f"%{search}%"
            params.extend([search_pattern, search_pattern])
        
        # Сортировка и лимит
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_stats(self) -> Dict:
        """Получить статистику по истории"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row  # Добавляем эту строку!
            
            # Общая статистика
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_requests,
                    SUM(tokens) as total_tokens,
                    SUM(cost) as total_cost,
                    AVG(cost) as avg_cost,
                    MIN(timestamp) as first_request,
                    MAX(timestamp) as last_request
                FROM requests
            """)
            general = dict(cursor.fetchone())
            
            # По моделям
            cursor = conn.execute("""
                SELECT 
                    model,
                    COUNT(*) as count,
                    SUM(tokens) as tokens,
                    SUM(cost) as cost
                FROM requests
                GROUP BY model
                ORDER BY count DESC
            """)
            by_model = [dict(row) for row in cursor.fetchall()]
            
            # По типам задач
            cursor = conn.execute("""
                SELECT 
                    task_type,
                    COUNT(*) as count,
                    AVG(cost) as avg_cost
                FROM requests
                WHERE task_type IS NOT NULL
                GROUP BY task_type
                ORDER BY count DESC
            """)
            by_task = [dict(row) for row in cursor.fetchall()]
            
            # По датам (последние 7 дней)
            cursor = conn.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as count,
                    SUM(cost) as cost
                FROM requests
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """)
            by_date = [dict(row) for row in cursor.fetchall()]
            
            return {
                'general': general,
                'by_model': by_model,
                'by_task': by_task,
                'by_date': by_date
            }
    
    def delete_old_records(self, days: int = 30) -> int:
        """
        Удалить записи старше указанного количества дней
        
        Returns:
            Количество удаленных записей
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM requests
                WHERE timestamp < datetime('now', '-' || ? || ' days')
            """, (days,))
            conn.commit()
            return cursor.rowcount
    
    def export_to_json(self, filepath: str, **filters):
        """Экспорт истории в JSON файл"""
        data = self.get_history(limit=10000, **filters)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return len(data)
    
    def export_to_csv(self, filepath: str, **filters):
        """Экспорт истории в CSV файл"""
        import csv
        
        data = self.get_history(limit=10000, **filters)
        if not data:
            return 0
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return len(data)

    # ============================================
    # Пользователи (JWT аутентификация)
    # ============================================

    def create_user(self, email: str, password_hash: str) -> int:
        """
        Создать нового пользователя.

        Args:
            email: Email пользователя (уникальный)
            password_hash: Хеш пароля (bcrypt/argon2)

        Returns:
            ID созданной записи пользователя
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
                """,
                (email.lower().strip(), password_hash)
            )
            conn.commit()
            return cursor.lastrowid

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """
        Получить пользователя по email.

        Args:
            email: Email пользователя

        Returns:
            Dict с полями пользователя или None, если не найден
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, email, password_hash, created_at, last_login_at, is_active
                FROM users
                WHERE email = ?
                LIMIT 1
                """,
                (email.lower().strip(),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_user_last_login(self, user_id: int) -> int:
        """
        Обновить время последнего входа пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Количество обновлённых строк (0 или 1)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE users
                SET last_login_at = ?, is_active = 1
                WHERE id = ?
                """,
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
            return cursor.rowcount

    # ============================================
    # AI Model Rankings
    # ============================================

    def add_ranking(
        self,
        category: str,
        model_name: str,
        rank: int,
        score: float,
        source_id: Optional[int] = None,
        notes: Optional[str] = None
    ) -> int:
        """
        Добавить или обновить рейтинг модели
        
        Args:
            category: Категория (reasoning, coding, vision, etc.)
            model_name: Название модели
            rank: Позиция в рейтинге
            score: Оценка/score модели
            source_id: ID источника данных
            notes: Дополнительные заметки
        
        Returns:
            ID записи
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO ai_model_rankings 
                (category, model_name, rank, score, source_id, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(category, model_name) 
                DO UPDATE SET 
                    rank = excluded.rank,
                    score = excluded.score,
                    source_id = excluded.source_id,
                    notes = excluded.notes,
                    updated_at = excluded.updated_at
            """, (
                category, model_name, rank, score, source_id, notes,
                datetime.now().isoformat()
            ))
            conn.commit()
            return cursor.lastrowid

    def get_all_rankings(self) -> Dict[str, List[Dict]]:
        """
        Получить все рейтинги, сгруппированные по категориям
        
        Returns:
            Dict с ключами-категориями и списками моделей
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM ai_model_rankings 
                ORDER BY category, rank
            """)
            rows = cursor.fetchall()
            
            rankings = {}
            for row in rows:
                category = row['category']
                if category not in rankings:
                    rankings[category] = []
                rankings[category].append(dict(row))
            
            return rankings

    def get_rankings_by_category(self, category: str, limit: int = 3) -> List[Dict]:
        """
        Получить рейтинги для конкретной категории
        
        Args:
            category: Категория (reasoning, coding, etc.)
            limit: Количество моделей (default: 3)
        
        Returns:
            Список моделей отсортированных по rank
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM ai_model_rankings 
                WHERE category = ?
                ORDER BY rank
                LIMIT ?
            """, (category, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_top_models(self, limit: int = 5) -> List[Dict]:
        """
        Получить топ модели по всем категориям
        
        Args:
            limit: Количество моделей на категорию
        
        Returns:
            Список моделей
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM ai_model_rankings 
                WHERE rank <= ?
                ORDER BY category, rank
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def add_trusted_source(
        self,
        name: str,
        url: str,
        data_type: Optional[str] = None,
        reliability: Optional[str] = None,
        format: Optional[str] = None
    ) -> int:
        """
        Добавить доверенный источник данных
        
        Returns:
            ID созданной записи
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO trusted_sources 
                (name, url, data_type, reliability, format)
                VALUES (?, ?, ?, ?, ?)
            """, (name, url, data_type, reliability, format))
            conn.commit()
            return cursor.lastrowid

    def update_source_check_time(self, source_id: int) -> int:
        """
        Обновить время последней проверки источника
        
        Returns:
            Количество обновлённых строк
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE trusted_sources
                SET last_checked_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), source_id))
            conn.commit()
            return cursor.rowcount

    def get_trusted_sources(self) -> List[Dict]:
        """
        Получить список всех доверенных источников
        
        Returns:
            Список источников
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM trusted_sources 
                ORDER BY name
            """)
            return [dict(row) for row in cursor.fetchall()]


# Singleton instance
_db_instance = None

def get_db() -> HistoryDatabase:
    """Получить singleton instance базы данных"""
    global _db_instance
    if _db_instance is None:
        _db_instance = HistoryDatabase()
    return _db_instance


# Тестирование при прямом запуске
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🗄️ Testing History Database\n")
    
    db = get_db()
    
    # Добавление тестовых записей
    print("Adding test records...")
    db.add_request(
        prompt="Test prompt 1",
        response="Test response 1",
        model="test-model",
        task_type="code",
        tokens=100,
        cost=0.001
    )
    
    db.add_request(
        prompt="Test prompt 2",
        response="Test response 2",
        model="gpt-4",
        task_type="architecture",
        tokens=500,
        cost=0.05
    )
    
    # Получение истории
    print("\nFetching history...")
    history = db.get_history(limit=5)
    print(f"Found {len(history)} records")
    
    for record in history:
        print(f"  - {record['timestamp']}: {record['model']} (${record['cost']})")
    
    # Статистика
    print("\nStatistics:")
    stats = db.get_stats()
    print(f"  Total requests: {stats['general']['total_requests']}")
    print(f"  Total cost: ${stats['general']['total_cost']:.6f}")
    print(f"  Average cost: ${stats['general']['avg_cost']:.6f}")
    
    print("\n✅ Database test completed!")