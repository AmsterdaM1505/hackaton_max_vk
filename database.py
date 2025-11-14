"""
Работа с базой данных PostgreSQL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import sql
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import DATABASE_URL, CATEGORIES


class Database:
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self.init_db()

    def get_connection(self):
        """Получить подключение к БД PostgreSQL"""
        conn = psycopg2.connect(self.database_url)
        return conn

    def init_db(self):
        """Инициализация таблиц БД"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    gender TEXT NOT NULL,
                    bio TEXT,
                    categories JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            ''')

            # Таблица лайков (взаимные нравятся)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS likes (
                    id SERIAL PRIMARY KEY,
                    user_from TEXT NOT NULL,
                    user_to TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_from, user_to),
                    FOREIGN KEY(user_from) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(user_to) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            # Таблица дизлайков (исключить из рекомендаций)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dislikes (
                    id SERIAL PRIMARY KEY,
                    user_from TEXT NOT NULL,
                    user_to TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user_from, user_to),
                    FOREIGN KEY(user_from) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(user_to) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            # Таблица сообщений (чат между пользователями)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    from_user TEXT NOT NULL,
                    to_user TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    is_read BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY(from_user) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(to_user) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            # Таблица для сохранения состояния FSM пользователя
            # Без FOREIGN KEY потому что состояние может быть у пользователя,
            # который еще не создал профиль (находится в процессе заполнения анкеты)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_states (
                    user_id TEXT PRIMARY KEY,
                    state TEXT,
                    other_id TEXT,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            ''')

            # Таблица уведомлений (лайки и мэтчи)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    from_user_id TEXT NOT NULL,
                    from_user_name TEXT NOT NULL,
                    from_user_username TEXT,
                    notification_type TEXT NOT NULL,
                    message TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(from_user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            # Таблица блокировок чатов (когда один из пользователей прервал беседу)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_chats (
                    id SERIAL PRIMARY KEY,
                    user1_id TEXT NOT NULL,
                    user2_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(user1_id, user2_id),
                    FOREIGN KEY(user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY(user2_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            # Создание индексов для оптимизации запросов
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_likes_user_from ON likes(user_from)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_likes_user_to ON likes(user_to)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_dislikes_user_from ON dislikes(user_from)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_from_to ON messages(from_user, to_user)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_blocked_chats ON blocked_chats(user1_id, user2_id)')

            conn.commit()
            print("✅ База данных инициализирована успешно")
        except Exception as e:
            print(f"❌ Ошибка при инициализации БД: {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    # ===== Методы работы с пользователями =====

    def user_exists(self, user_id: str) -> bool:
        """Проверить существование пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE user_id = %s', (user_id,))
            result = cursor.fetchone() is not None
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Error checking user existence: {e}")
            return False

    def create_user(self, user_id: str, username: str, name: str, age: int,
                   gender: str, bio: str, categories: List[str]) -> bool:
        """Создать нового пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO users
                (user_id, username, name, age, gender, bio, categories, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    name = EXCLUDED.name,
                    age = EXCLUDED.age,
                    gender = EXCLUDED.gender,
                    bio = EXCLUDED.bio,
                    categories = EXCLUDED.categories,
                    updated_at = NOW()
            ''', (user_id, username, name, age, gender, bio, json.dumps(categories)))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о пользователе"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM users WHERE user_id = %s', (user_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                user = dict(row)
                return user
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    def update_user(self, user_id: str, **kwargs) -> bool:
        """Обновить профиль пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Построение динамического запроса UPDATE
            set_clause = []
            values = []
            for key, value in kwargs.items():
                if key == 'categories' and isinstance(value, list):
                    set_clause.append(f'{key} = %s')
                    values.append(json.dumps(value))
                else:
                    set_clause.append(f'{key} = %s')
                    values.append(value)

            set_clause.append('updated_at = %s')
            values.append(datetime.now())
            values.append(user_id)

            query = f"UPDATE users SET {', '.join(set_clause)} WHERE user_id = %s"
            cursor.execute(query, values)

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    # ===== Методы работы с лайками и дизлайками =====

    def add_like(self, user_from: str, user_to: str) -> bool:
        """Добавить лайк"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO likes (user_from, user_to)
                VALUES (%s, %s)
                ON CONFLICT (user_from, user_to) DO NOTHING
            ''', (user_from, user_to))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding like: {e}")
            return False

    def add_dislike(self, user_from: str, user_to: str) -> bool:
        """Добавить дизлайк"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO dislikes (user_from, user_to)
                VALUES (%s, %s)
                ON CONFLICT (user_from, user_to) DO NOTHING
            ''', (user_from, user_to))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding dislike: {e}")
            return False

    def has_interacted(self, user_from: str, user_to: str) -> bool:
        """Проверить, взаимодействовал ли пользователь уже"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 1 FROM likes WHERE user_from = %s AND user_to = %s
                UNION
                SELECT 1 FROM dislikes WHERE user_from = %s AND user_to = %s
            ''', (user_from, user_to, user_from, user_to))

            result = cursor.fetchone() is not None
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Error checking interaction: {e}")
            return False

    def get_matches(self, user_id: str) -> List[str]:
        """Получить взаимные нравятся (мэтчи)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT user_to FROM likes
                WHERE user_from = %s AND user_to IN (
                    SELECT user_from FROM likes WHERE user_to = %s
                )
            ''', (user_id, user_id))

            matches = [row[0] for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return matches
        except Exception as e:
            print(f"Error getting matches: {e}")
            return []

    # ===== Методы для поиска профилей =====

    def get_profile_for_user(self, user_id: str, category: str) -> Optional[Dict[str, Any]]:
        """Получить следующий профиль для просмотра пользователем"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Ищем профили противоположного пола в выбранной категории
            # которые еще не были просмотрены (нет like/dislike)
            cursor.execute('''
                SELECT * FROM users
                WHERE user_id != %s
                AND categories @> %s::jsonb
                AND user_id NOT IN (
                    SELECT user_to FROM likes WHERE user_from = %s
                    UNION
                    SELECT user_to FROM dislikes WHERE user_from = %s
                )
                ORDER BY RANDOM()
                LIMIT 1
            ''', (user_id, json.dumps([category]), user_id, user_id))

            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                user = dict(row)
                # user['categories'] = json.loads(user['categories']) if user['categories'] else []
                return user
            return None
        except Exception as e:
            print(f"Error getting profile: {e}")
            return None

    # ===== Методы работы с сообщениями =====

    def save_message(self, from_user: str, to_user: str, message: str) -> bool:
        """Сохранить сообщение"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO messages (from_user, to_user, message)
                VALUES (%s, %s, %s)
            ''', (from_user, to_user, message))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving message: {e}")
            return False

    def get_messages(self, user1: str, user2: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить сообщения между двумя пользователями"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute('''
                SELECT * FROM messages
                WHERE (from_user = %s AND to_user = %s)
                   OR (from_user = %s AND to_user = %s)
                ORDER BY created_at DESC
                LIMIT %s
            ''', (user1, user2, user2, user1, limit))

            messages = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return messages[::-1]  # Разворачиваем для хронологического порядка
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []

    # ===== Методы работы с состоянием FSM =====

    def set_user_state(self, user_id: str, state: str, data: Optional[Dict] = None):
        """Установить состояние FSM пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # data_json = json.dumps(data.current_profile) if data else None
            if data is None:
                cursor.execute('''
                                INSERT INTO user_states (user_id, state)
                                VALUES (%s, %s)
                                ON CONFLICT (user_id) DO UPDATE SET
                                    state = EXCLUDED.state,
                                    updated_at = NOW()
                            ''', (user_id, state))
            else:
                other_id = data['current_profile']['user_id']
                cursor.execute('''
                                INSERT INTO user_states (user_id, state, other_id)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (user_id) DO UPDATE SET
                                    state = EXCLUDED.state,
                                    other_id = EXCLUDED.other_id,
                                    updated_at = NOW()
                            ''', (user_id, state, other_id))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error setting user state: {e}")
            return False

    # def get_user_state(self, user_id: str) -> tuple:
    #     """Получить состояние FSM пользователя (state, data)"""
    #     try:
    #         conn = self.get_connection()
    #         cursor = conn.cursor(cursor_factory=RealDictCursor)
    #
    #         cursor.execute('SELECT state, data FROM user_states WHERE user_id = %s', (user_id,))
    #         row = cursor.fetchone()
    #         cursor.close()
    #         conn.close()
    #
    #         if row:
    #             data = json.loads(row['data']) if row['data'] else {}
    #             return row['state'], data
    #         return None, {}
    #     except Exception as e:
    #         print(f"Error getting user state: {e}")
    #         return None, {}
    def get_user_state(self, user_id: str) -> tuple:
        """Получить состояние FSM пользователя (state, data)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            cursor.execute('SELECT state, other_id FROM user_states WHERE user_id = %s', (user_id,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                return row['state'], row['other_id']
            return None, {}
        except Exception as e:
            print(f"Error getting user state: {e}")
            return None, {}

    def clear_user_state(self, user_id: str):
        """Очистить состояние пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM user_states WHERE user_id = %s', (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error clearing user state: {e}")

    # ===== Методы работы с уведомлениями =====

    def add_notification(self, user_id: str, from_user_id: str, from_user_name: str,
                        from_user_username: str, notification_type: str, message: str = None) -> bool:
        """Добавить уведомление"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO notifications
                (user_id, from_user_id, from_user_name, from_user_username, notification_type, message)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, from_user_id, from_user_name, from_user_username, notification_type, message))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding notification: {e}")
            return False

    def get_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict[str, Any]]:
        """Получить уведомления пользователя"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            if unread_only:
                cursor.execute('''
                    SELECT * FROM notifications
                    WHERE user_id = %s AND is_read = FALSE
                    ORDER BY created_at DESC
                ''', (user_id,))
            else:
                cursor.execute('''
                    SELECT * FROM notifications
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                ''', (user_id,))

            notifications = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            conn.close()
            return notifications
        except Exception as e:
            print(f"Error getting notifications: {e}")
            return []

    def get_unread_notifications_count(self, user_id: str) -> int:
        """Получить количество непрочитанных уведомлений"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT COUNT(*) FROM notifications
                WHERE user_id = %s AND is_read = FALSE
            ''', (user_id,))

            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result else 0
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0

    def mark_notification_as_read(self, notification_id: int) -> bool:
        """Отметить уведомление как прочитанное"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE notifications SET is_read = TRUE WHERE id = %s
            ''', (notification_id,))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking notification as read: {e}")
            return False

    def mark_all_notifications_as_read(self, user_id: str) -> bool:
        """Отметить все уведомления пользователя как прочитанные"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE notifications SET is_read = TRUE WHERE user_id = %s
            ''', (user_id,))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error marking all notifications as read: {e}")
            return False

    # ===== Методы работы с блокировками чатов =====

    def block_chat(self, user1_id: str, user2_id: str) -> bool:
        """Заблокировать чат между двумя пользователями (обоюдно)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Нормализуем: меньший ID первый
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id

            cursor.execute('''
                INSERT INTO blocked_chats (user1_id, user2_id)
                VALUES (%s, %s)
                ON CONFLICT (user1_id, user2_id) DO NOTHING
            ''', (user1_id, user2_id))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error blocking chat: {e}")
            return False

    def is_chat_blocked(self, user1_id: str, user2_id: str) -> bool:
        """Проверить, заблокирован ли чат между двумя пользователями"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Нормализуем: меньший ID первый
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id

            cursor.execute('''
                SELECT 1 FROM blocked_chats
                WHERE user1_id = %s AND user2_id = %s
            ''', (user1_id, user2_id))

            result = cursor.fetchone() is not None
            cursor.close()
            conn.close()
            return result
        except Exception as e:
            print(f"Error checking blocked chat: {e}")
            return False

    def unblock_chat(self, user1_id: str, user2_id: str) -> bool:
        """Разблокировать чат между двумя пользователями"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Нормализуем: меньший ID первый
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id

            cursor.execute('''
                DELETE FROM blocked_chats
                WHERE user1_id = %s AND user2_id = %s
            ''', (user1_id, user2_id))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error unblocking chat: {e}")
            return False


# Глобальный экземпляр БД
db = Database()
