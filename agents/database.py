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

            # Таблица проектов
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_projects_user_id
                ON projects(user_id)
            """)

            # Таблица баз данных (пользовательских)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS databases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    schema_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_databases_project_id
                ON databases(project_id)
            """)

            # Таблица записей базы данных
            conn.execute("""
                CREATE TABLE IF NOT EXISTS database_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    database_id INTEGER NOT NULL,
                    data_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (database_id) REFERENCES databases(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_database_records_database_id
                ON database_records(database_id)
            """)

            # Таблица рабочих процессов (workflows)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    trigger_config TEXT,
                    actions_json TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflows_user_id
                ON workflows(user_id)
            """)

            # Таблица выполнений workflows
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    executed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id
                ON workflow_executions(workflow_id)
            """)

            # Таблица токенов интеграций
            conn.execute("""
                CREATE TABLE IF NOT EXISTS integration_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    integration_type TEXT NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expires_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_integration_tokens_user_integration
                ON integration_tokens(user_id, integration_type)
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

    def get_rankings_grouped_by_category(self) -> Dict[str, List[Dict]]:
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

    # ============================================
    # Projects
    # ============================================

    def create_project(self, user_id: int, name: str, description: Optional[str] = None) -> int:
        """
        Создать новый проект

        Args:
            user_id: ID пользователя
            name: Название проекта
            description: Описание проекта

        Returns:
            ID созданного проекта
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO projects (user_id, name, description)
                VALUES (?, ?, ?)
            """, (user_id, name, description))
            conn.commit()
            return cursor.lastrowid

    def get_projects(self, user_id: int) -> List[Dict]:
        """
        Получить список всех проектов пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Список проектов
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM projects
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_project(self, project_id: int, user_id: int) -> Optional[Dict]:
        """
        Получить конкретный проект

        Args:
            project_id: ID проекта
            user_id: ID пользователя (для проверки прав доступа)

        Returns:
            Dict с данными проекта или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM projects
                WHERE id = ? AND user_id = ?
                LIMIT 1
            """, (project_id, user_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_project(self, project_id: int, user_id: int, name: str, description: Optional[str] = None) -> bool:
        """
        Обновить проект

        Args:
            project_id: ID проекта
            user_id: ID пользователя (для проверки прав доступа)
            name: Новое название
            description: Новое описание

        Returns:
            True если обновлено, False если не найдено
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE projects
                SET name = ?, description = ?
                WHERE id = ? AND user_id = ?
            """, (name, description, project_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_project(self, project_id: int, user_id: int) -> bool:
        """
        Удалить проект

        Args:
            project_id: ID проекта
            user_id: ID пользователя (для проверки прав доступа)

        Returns:
            True если удалено, False если не найдено
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM projects
                WHERE id = ? AND user_id = ?
            """, (project_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    # ============================================
    # Databases
    # ============================================

    def create_database(self, project_id: int, name: str, schema_json: str) -> int:
        """
        Создать новую базу данных в проекте

        Args:
            project_id: ID проекта
            name: Название базы данных
            schema_json: JSON-строка со схемой (определения колонок)

        Returns:
            ID созданной базы данных
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO databases (project_id, name, schema_json)
                VALUES (?, ?, ?)
            """, (project_id, name, schema_json))
            conn.commit()
            return cursor.lastrowid

    def get_databases(self, project_id: int) -> List[Dict]:
        """
        Получить все базы данных проекта

        Args:
            project_id: ID проекта

        Returns:
            Список баз данных
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM databases
                WHERE project_id = ?
                ORDER BY created_at DESC
            """, (project_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_database(self, database_id: int) -> Optional[Dict]:
        """
        Получить конкретную базу данных

        Args:
            database_id: ID базы данных

        Returns:
            Dict с данными базы данных или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM databases
                WHERE id = ?
                LIMIT 1
            """, (database_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_database(self, database_id: int) -> bool:
        """
        Удалить базу данных

        Args:
            database_id: ID базы данных

        Returns:
            True если удалено, False если не найдено
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM databases
                WHERE id = ?
            """, (database_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ============================================
    # Database Records
    # ============================================

    def create_record(self, database_id: int, data_json: str) -> int:
        """
        Создать запись в базе данных

        Args:
            database_id: ID базы данных
            data_json: JSON-строка с данными записи

        Returns:
            ID созданной записи
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO database_records (database_id, data_json)
                VALUES (?, ?)
            """, (database_id, data_json))
            conn.commit()
            return cursor.lastrowid

    def get_records(self, database_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Получить записи из базы данных

        Args:
            database_id: ID базы данных
            limit: Количество записей
            offset: Смещение для пагинации

        Returns:
            Список записей
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM database_records
                WHERE database_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (database_id, limit, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_record(self, record_id: int) -> Optional[Dict]:
        """
        Получить конкретную запись

        Args:
            record_id: ID записи

        Returns:
            Dict с данными записи или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM database_records
                WHERE id = ?
                LIMIT 1
            """, (record_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_record(self, record_id: int, data_json: str) -> bool:
        """
        Обновить запись

        Args:
            record_id: ID записи
            data_json: Новые данные в формате JSON

        Returns:
            True если обновлено, False если не найдено
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE database_records
                SET data_json = ?, updated_at = ?
                WHERE id = ?
            """, (data_json, datetime.now().isoformat(), record_id))
            conn.commit()
            return cursor.rowcount > 0

    def delete_record(self, record_id: int) -> bool:
        """
        Удалить запись

        Args:
            record_id: ID записи

        Returns:
            True если удалено, False если не найдено
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM database_records
                WHERE id = ?
            """, (record_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ============================================
    # Workflows
    # ============================================

    def create_workflow(
        self,
        user_id: int,
        name: str,
        trigger_type: str,
        trigger_config: str,
        actions_json: str
    ) -> int:
        """
        Создать новый workflow

        Args:
            user_id: ID пользователя
            name: Название workflow
            trigger_type: Тип триггера (manual, schedule, webhook, etc.)
            trigger_config: Конфигурация триггера в формате JSON
            actions_json: Массив действий в формате JSON

        Returns:
            ID созданного workflow
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO workflows (user_id, name, trigger_type, trigger_config, actions_json)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, name, trigger_type, trigger_config, actions_json))
            conn.commit()
            return cursor.lastrowid

    def get_workflows(self, user_id: int) -> List[Dict]:
        """
        Получить все workflows пользователя

        Args:
            user_id: ID пользователя

        Returns:
            Список workflows
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_workflow(self, workflow_id: int, user_id: int) -> Optional[Dict]:
        """
        Получить конкретный workflow

        Args:
            workflow_id: ID workflow
            user_id: ID пользователя (для проверки прав доступа)

        Returns:
            Dict с данными workflow или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflows
                WHERE id = ? AND user_id = ?
                LIMIT 1
            """, (workflow_id, user_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_workflow(self, workflow_id: int, user_id: int, **kwargs) -> bool:
        """
        Обновить workflow

        Args:
            workflow_id: ID workflow
            user_id: ID пользователя (для проверки прав доступа)
            **kwargs: Поля для обновления (name, trigger_type, trigger_config, actions_json, enabled)

        Returns:
            True если обновлено, False если не найдено
        """
        allowed_fields = ['name', 'trigger_type', 'trigger_config', 'actions_json', 'enabled']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [workflow_id, user_id]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"""
                UPDATE workflows
                SET {set_clause}
                WHERE id = ? AND user_id = ?
            """, values)
            conn.commit()
            return cursor.rowcount > 0

    def delete_workflow(self, workflow_id: int, user_id: int) -> bool:
        """
        Удалить workflow

        Args:
            workflow_id: ID workflow
            user_id: ID пользователя (для проверки прав доступа)

        Returns:
            True если удалено, False если не найдено
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM workflows
                WHERE id = ? AND user_id = ?
            """, (workflow_id, user_id))
            conn.commit()
            return cursor.rowcount > 0

    # ============================================
    # Workflow Executions
    # ============================================

    def create_execution(
        self,
        workflow_id: int,
        status: str,
        result_json: str,
        error: Optional[str] = None
    ) -> int:
        """
        Создать запись о выполнении workflow

        Args:
            workflow_id: ID workflow
            status: Статус выполнения (success, failed, running)
            result_json: Результаты выполнения в формате JSON
            error: Текст ошибки (если есть)

        Returns:
            ID созданной записи
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO workflow_executions (workflow_id, status, result_json, error)
                VALUES (?, ?, ?, ?)
            """, (workflow_id, status, result_json, error))
            conn.commit()
            return cursor.lastrowid

    def get_executions(self, workflow_id: int, limit: int = 50) -> List[Dict]:
        """
        Получить историю выполнений workflow

        Args:
            workflow_id: ID workflow
            limit: Количество записей

        Returns:
            Список выполнений
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM workflow_executions
                WHERE workflow_id = ?
                ORDER BY executed_at DESC
                LIMIT ?
            """, (workflow_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ============================================
    # Integration Tokens
    # ============================================

    def save_integration_token(
        self,
        user_id: int,
        integration_type: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[str] = None
    ) -> int:
        """
        Сохранить или обновить токен интеграции

        Args:
            user_id: ID пользователя
            integration_type: Тип интеграции (gmail, google_drive, telegram)
            access_token: Access token
            refresh_token: Refresh token (опционально)
            expires_at: Время истечения токена

        Returns:
            ID записи
        """
        with sqlite3.connect(self.db_path) as conn:
            # Сначала проверяем, существует ли уже токен
            cursor = conn.execute("""
                SELECT id FROM integration_tokens
                WHERE user_id = ? AND integration_type = ?
            """, (user_id, integration_type))
            existing = cursor.fetchone()

            if existing:
                # Обновляем существующий
                cursor = conn.execute("""
                    UPDATE integration_tokens
                    SET access_token = ?, refresh_token = ?, expires_at = ?
                    WHERE user_id = ? AND integration_type = ?
                """, (access_token, refresh_token, expires_at, user_id, integration_type))
                conn.commit()
                return existing[0]
            else:
                # Создаём новый
                cursor = conn.execute("""
                    INSERT INTO integration_tokens
                    (user_id, integration_type, access_token, refresh_token, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, integration_type, access_token, refresh_token, expires_at))
                conn.commit()
                return cursor.lastrowid

    def get_integration_token(self, user_id: int, integration_type: str) -> Optional[Dict]:
        """
        Получить токен интеграции

        Args:
            user_id: ID пользователя
            integration_type: Тип интеграции

        Returns:
            Dict с данными токена или None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM integration_tokens
                WHERE user_id = ? AND integration_type = ?
                LIMIT 1
            """, (user_id, integration_type))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_integration_token(self, user_id: int, integration_type: str) -> bool:
        """
        Удалить токен интеграции

        Args:
            user_id: ID пользователя
            integration_type: Тип интеграции

        Returns:
            True если удалено, False если не найдено
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM integration_tokens
                WHERE user_id = ? AND integration_type = ?
            """, (user_id, integration_type))
            conn.commit()
            return cursor.rowcount > 0

    # ============================================
    # AI Model Rankings
    # ============================================

    def get_all_rankings(self) -> List[Dict]:
        """
        Получить агрегированные рейтинги всех AI моделей

        Returns:
            Список моделей с усредненными оценками по категориям
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT
                    model_name as model,
                    AVG(score) as avg_overall,
                    AVG(CASE WHEN category = 'reasoning' THEN score END) as avg_reasoning,
                    AVG(CASE WHEN category = 'coding' THEN score END) as avg_coding,
                    AVG(CASE WHEN category = 'vision' THEN score END) as avg_vision,
                    AVG(CASE WHEN category = 'chat' THEN score END) as avg_chat,
                    AVG(CASE WHEN category = 'agents' THEN score END) as avg_agents,
                    AVG(CASE WHEN category = 'translation' THEN score END) as avg_translation,
                    AVG(CASE WHEN category = 'local' THEN score END) as avg_local,
                    COUNT(*) as total_rankings
                FROM ai_model_rankings
                GROUP BY model_name
                ORDER BY avg_overall DESC
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