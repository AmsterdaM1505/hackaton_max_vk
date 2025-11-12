"""
Скрипт для создания тестовых пользователей в базе данных
Используй для тестирования функций лайков и чатов
"""

from database import db
from states import UserState
from datetime import datetime

def create_test_users():
    """Создаёт несколько тестовых пользователей"""

    test_users = [
        {
            'user_id': '1001',
            'username': 'alice_test',
            'name': 'Alice',
            'age': 25,
            'gender': 'female',
            'bio': '🌍 Люблю путешествия и новые впечатления. Ищу интересного человека для дружбы и общения.',
            'categories': ['love', 'friendship']
        },
        {
            'user_id': '1002',
            'username': 'bob_test',
            'name': 'Bob',
            'age': 28,
            'gender': 'male',
            'bio': '🎸 Музыкант, люблю играть в гитаре. Ищу вторую половину для серьёзных отношений.',
            'categories': ['love']
        },
        {
            'user_id': '1003',
            'username': 'charlie_test',
            'name': 'Charlie',
            'age': 30,
            'gender': 'male',
            'bio': '⚽ Спортсмен, любитель активного отдыха. Ищу друзей и компанию для увлекательных мероприятий.',
            'categories': ['friendship', 'hobby']
        },
        {
            'user_id': '1004',
            'username': 'diana_test',
            'name': 'Diana',
            'age': 23,
            'gender': 'female',
            'bio': '📚 Студентка, увлекаюсь литературой и кино. Ищу собеседника для интересных разговоров.',
            'categories': ['love', 'hobby']
        },
        {
            'user_id': '1005',
            'username': 'eva_test',
            'name': 'Eva',
            'age': 26,
            'gender': 'female',
            'bio': '🎨 Художница, творческая личность. Ищу человека, который ценит искусство и креативность.',
            'categories': ['love', 'friendship', 'hobby']
        },
        {
            'user_id': '1006',
            'username': 'frank_test',
            'name': 'Frank',
            'age': 32,
            'gender': 'male',
            'bio': '💼 Инженер по профессии, люблю технологии и инновации. Ищу партнёра для жизни.',
            'categories': ['love']
        }
    ]

    print("🚀 Создаю тестовых пользователей...")
    print("-" * 60)

    for user in test_users:
        user_id = user['user_id']

        # Проверяем, не существует ли уже такой пользователь
        if db.user_exists(user_id):
            print(f"⚠️  Пользователь {user['name']} ({user_id}) уже существует, пропускаю")
            continue

        # Создаём профиль
        success = db.create_user(
            user_id=user_id,
            username=user['username'],
            name=user['name'],
            age=user['age'],
            gender=user['gender'],
            bio=user['bio'],
            categories=user['categories']
        )

        if success:
            categories_text = ', '.join(user['categories'])
            print(f"✅ Создан профиль: {user['name']} ({user['age']} лет, {user['gender']})")
            print(f"   ID: {user_id}")
            print(f"   Интересы: {categories_text}")
            print()
        else:
            print(f"❌ Ошибка при создании профиля {user['name']}")
            print()

    print("-" * 60)

    # Добавляем несколько тестовых лайков для демонстрации мэтчей
    print("\n💕 Создаю тестовые лайки...")
    print("-" * 60)

    test_likes = [
        ('1001', '1002'),  # Alice лайкнула Bob
        ('1002', '1001'),  # Bob лайкнул Alice - МАТЧ!
        ('1003', '1004'),  # Charlie лайкнул Diana
        ('1004', '1005'),  # Diana лайкнула Eva
        ('1005', '1003'),  # Eva лайкнула Charlie - МАТЧ!
    ]

    for user_from, user_to in test_likes:
        if not db.has_interacted(user_from, user_to):
            db.add_like(user_from, user_to)
            user_from_obj = db.get_user(user_from)
            user_to_obj = db.get_user(user_to)
            print(f"❤️  {user_from_obj['name']} лайкнула {user_to_obj['name']}")

    print("-" * 60)
    print("\n✨ Тестовые данные успешно созданы!\n")

    # Выводим статистику
    print("📊 Статистика:")
    conn = db.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM likes")
    likes_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM messages")
    messages_count = cursor.fetchone()[0]

    conn.close()

    print(f"   👥 Пользователей: {user_count}")
    print(f"   ❤️  Лайков: {likes_count}")
    print(f"   💬 Сообщений: {messages_count}")

    print("\n" + "=" * 60)
    print("🎯 МЭТЧИ (взаимные лайки):")
    print("=" * 60)

    matches_info = [
        ('Alice', 'Bob'),
        ('Charlie', 'Eva')
    ]

    for name1, name2 in matches_info:
        print(f"💕 {name1} ↔️  {name2}")

    print("\n" + "=" * 60)
    print("🧪 КАК ТЕСТИРОВАТЬ:\n")
    print("1. Запусти бота: python main.py")
    print("2. Отправь /start")
    print("3. Выбери категорию: /love (или /friendship, /hobby)")
    print("4. Ставь лайки/дизлайки на профили тестовых пользователей")
    print("5. Когда будет матч, появится уведомление")
    print("6. Команда /messages покажет список мэтчей")
    print("7. Команда /chat_<user_id> начнёт чат")
    print("8. Команда /stop_chat прервёт чат (блокирует обоюдно)")
    print("\n" + "=" * 60)


if __name__ == '__main__':
    create_test_users()
