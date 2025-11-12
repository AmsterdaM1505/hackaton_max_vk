# 🚀 Дорожная карта функциональности

## Текущая версия (1.0)

### ✅ Реализованные функции

#### Управление профилем
- [x] Создание профиля (имя, возраст, пол, описание)
- [x] Выбор категорий интересов (5 категорий)
- [x] Редактирование всех данных профиля
- [x] Просмотр собственного профиля
- [x] Валидация входных данных

#### Swipe функционал (как Tinder)
- [x] Просмотр профилей в выбранной категории
- [x] Система лайков (Like ❤️)
- [x] Система дизлайков (Dislike 👎)
- [x] Пропуск профиля (Skip ⏭️)
- [x] Смена категорий во время просмотра
- [x] Случайный порядок профилей
- [x] Исключение уже просмотренных профилей

#### Мэтчи и общение
- [x] Система взаимных лайков (Matches)
- [x] Уведомления о мэтчах
- [x] Список мэтчей с быстрым доступом к чату
- [x] Чат между пользователями
- [x] История сообщений

#### Интерфейс и УХ
- [x] Главное меню
- [x] Системы команд (slash-commands)
- [x] Красивое форматирование профилей
- [x] Поддержка эмодзи
- [x] Четкая навигация

---

## Версия 2.0 (Планируется)

### 🎨 Фото в профилях
```python
# В database.py добавить таблицу
CREATE TABLE IF NOT EXISTS user_photos (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL,
    photo_url TEXT NOT NULL,
    is_main BOOLEAN DEFAULT 0,
    created_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)

# В handlers.py добавить
async def cmd_upload_photo(event: MessageCreated):
    """Загрузить фото профиля"""
    # Обработка медиа-файлов
    pass
```

### 👤 Верификация и аватары
```python
def verify_user_age(user_id: str) -> bool:
    """Верификация возраста через фото"""
    pass

def set_profile_avatar(user_id: str, photo_url: str):
    """Установить аватар профиля"""
    pass
```

### 💎 Премиум функции
```python
class PremiumFeatures:
    # Неограниченные лайки в день
    UNLIMITED_LIKES = "unlimited_likes"

    # Лайк-все (Like All)
    LIKE_ALL = "like_all"

    # Просмотр кто лайкнул
    WHO_LIKED = "who_liked"

    # Повторный просмотр профиля (Undo)
    UNDO_LAST = "undo_last"

    # Скрыть профиль
    HIDE_PROFILE = "hide_profile"
```

### 🔔 Уведомления
```python
class Notifications:
    NEW_MATCH = "new_match"
    NEW_MESSAGE = "new_message"
    PROFILE_VIEWED = "profile_viewed"
    LIKED_YOU = "liked_you"

async def send_notification(user_id: str, notification_type: str):
    """Отправить уведомление пользователю"""
    pass
```

### 🌍 Геолокация
```python
# В database.py добавить поля
ALTER TABLE users ADD COLUMN latitude REAL;
ALTER TABLE users ADD COLUMN longitude REAL;
ALTER TABLE users ADD COLUMN city TEXT;

def search_nearby(user_id: str, distance_km: int = 50):
    """Поиск людей рядом"""
    pass
```

---

## Версия 3.0 (Долгосрочно)

### 📊 Умная рекомендация
```python
class SmartRecommendations:
    def get_recommended_profiles(self, user_id: str) -> List[dict]:
        """
        Используя ML алгоритмы:
        - Анализ истории лайков
        - Общие интересы
        - Возрастной диапазон
        - Историческое совпадение
        """
        pass
```

### 🎯 Тесты совместимости
```python
class CompatibilityTest:
    QUESTIONS = [
        {"question": "Что важнее?", "options": ["Карьера", "Семья", "Приключения"]},
        # ... 50+ вопросов
    ]

    def calculate_compatibility(self, user1_id: str, user2_id: str) -> int:
        """Считает процент совместимости"""
        pass
```

### 🛡️ Система модерации и жалоб
```python
class Reports:
    REASONS = {
        "spam": "Спам",
        "fake": "Поддельный профиль",
        "offensive": "Оскорбительное содержание",
        "scam": "Мошенничество",
        "inappropriate": "Неприемлемый контент"
    }

    async def report_user(self, reporter_id: str, reported_id: str, reason: str):
        pass
```

### 👥 Группы и вечеринки
```python
class GroupChat:
    def create_group_chat(self, members: List[str], name: str):
        """Групповые чаты по интересам"""
        pass

    def create_party(self, location: str, time: str, max_members: int):
        """События и встречи"""
        pass
```

### 🎮 Социальные игры
```python
class SocialGames:
    GAMES = {
        "questions": "Вопросы для знакомства",
        "truth_dare": "Правда или действие",
        "compatibility_quiz": "Тест совместимости",
        "would_you_rather": "Выбери одно"
    }

    async def start_game(self, user1_id: str, user2_id: str, game_type: str):
        pass
```

### 📱 Мобильное приложение
- Нативное приложение iOS/Android
- Push-уведомления
- Оффлайн режим

---

## Примеры кода для расширений

### Пример 1: Добавление функции "Кто лайкнул"

```python
# В database.py
def get_who_liked_me(self, user_id: str) -> List[str]:
    """Получить список пользователей, которые лайкнули меня"""
    conn = self.get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_from FROM likes
        WHERE user_to = ?
        AND user_from NOT IN (
            SELECT user_to FROM likes WHERE user_from = ?
        )
    ''', (user_id, user_id))

    likers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return likers

# В handlers.py
@self.dp.message_created(F.message.body.text == '/who_liked')
async def handle_who_liked(event: MessageCreated):
    user_id = event.message.from_user.user_id
    likers = db.get_who_liked_me(user_id)

    if not likers:
        await event.message.answer("😢 Пока никто не лайкнул")
        return

    text = "💚 Тебя лайкнули:\n\n"
    for liker_id in likers:
        user = db.get_user(liker_id)
        text += f"👤 {user['name']}, {user['age']}\n"

    await event.message.answer(text)
```

### Пример 2: Система блокировки

```python
# В database.py
def block_user(self, user_id: str, blocked_user_id: str):
    """Заблокировать пользователя"""
    try:
        conn = self.get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT OR IGNORE INTO blocked_users (user_id, blocked_user_id, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, blocked_user_id, now))

        # Удалить лайки
        cursor.execute('DELETE FROM likes WHERE user_from = ? AND user_to = ?',
                      (user_id, blocked_user_id))

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error blocking user: {e}")
        return False

def is_blocked(self, user_id: str, checked_user_id: str) -> bool:
    """Проверить, заблокирован ли пользователь"""
    conn = self.get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 1 FROM blocked_users
        WHERE user_id = ? AND blocked_user_id = ?
    ''', (user_id, checked_user_id))

    result = cursor.fetchone() is not None
    conn.close()
    return result
```

### Пример 3: Система действительности для рекомендаций

```python
# В database.py
def get_compatibility_score(self, user1_id: str, user2_id: str) -> int:
    """Считает совместимость пользователей"""
    user1 = self.get_user(user1_id)
    user2 = self.get_user(user2_id)

    if not user1 or not user2:
        return 0

    score = 50  # базовый рейтинг

    # Возрастная совместимость (±5 лет = полная совместимость)
    age_diff = abs(user1['age'] - user2['age'])
    if age_diff <= 5:
        score += 30
    elif age_diff <= 10:
        score += 15

    # Общие интересы
    common_interests = set(user1['categories']) & set(user2['categories'])
    score += len(common_interests) * 10

    return min(score, 100)  # максимум 100
```

### Пример 4: Уведомления

```python
# В handlers.py
async def check_new_matches(self, user_id: str):
    """Проверить новые мэтчи и отправить уведомление"""
    # Получить новые мэтчи (созданные в последний час)
    conn = db.get_connection()
    cursor = conn.cursor()

    one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()

    cursor.execute('''
        SELECT user_from FROM likes
        WHERE user_to = ?
        AND created_at > ?
        AND user_from IN (
            SELECT user_to FROM likes WHERE user_from = ?
        )
    ''', (user_id, one_hour_ago, user_id))

    new_matches = [row[0] for row in cursor.fetchall()]
    conn.close()

    if new_matches:
        text = f"🎉 У тебя {len(new_matches)} новых мэтчей!\n\n"
        for match_id in new_matches:
            user = db.get_user(match_id)
            text += f"💕 {user['name']}, {user['age']}\n"

        await self.bot.send_message(user_id, text)
```

---

## Метрики и аналитика (Version 4.0)

```python
class Analytics:
    # Отслеживание
    - Количество лайков в день
    - Процент мэтчей
    - Средняя длина чата
    - Время сеанса
    - Самые популярные категории
    - Распределение по возрасту/полу
```

---

## Эффективность разработки

### Краткосрочно (1-2 недели)
- Фото профилей
- "Кто лайкнул"
- Черный список

### Среднесрочно (1-2 месяца)
- Премиум функции
- Уведомления
- Улучшенная рекомендация

### Долгосрочно (3-6 месяцев)
- Мобильное приложение
- Система модерации
- Аналитика

---

## Заметки для разработки

1. **Производительность**: В будущем добавить кэширование популярных профилей
2. **Безопасность**: Реализовать сквозное шифрование сообщений
3. **Масштабируемость**: Перейти с SQLite на PostgreSQL при >10k пользователей
4. **Интеграция**: Добавить API для партнёров
5. **Монетизация**: Премиум подписка, реклама

---

**Последнее обновление:** 2025-11-08
