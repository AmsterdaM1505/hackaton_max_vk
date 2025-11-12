"""
Утилиты и вспомогательные функции
"""

from config import MIN_AGE, MAX_AGE, MAX_BIO_LENGTH
from database import db
from typing import Tuple, Optional
import re

class ValidationError(Exception):
    """Исключение для ошибок валидации"""
    pass

def validate_name(name: str) -> bool:
    """Проверить имя"""
    if not name or len(name) < 2 or len(name) > 50:
        raise ValidationError("Имя должно быть от 2 до 50 символов")
    if not re.match(r"^[а-яА-ЯёЁa-zA-Z\s'-]+$", name):
        raise ValidationError("Имя может содержать только буквы, пробелы и дефис")
    return True

def validate_age(age_str: str) -> int:
    """Проверить возраст"""
    try:
        age = int(age_str)
        if age < MIN_AGE or age > MAX_AGE:
            raise ValidationError(f"Возраст должен быть от {MIN_AGE} до {MAX_AGE}")
        return age
    except ValueError:
        raise ValidationError("Возраст должен быть числом")

def validate_bio(bio: str) -> bool:
    """Проверить биографию"""
    if not bio or len(bio) < 5 or len(bio) > MAX_BIO_LENGTH:
        raise ValidationError(f"Описание должно быть от 5 до {MAX_BIO_LENGTH} символов")
    return True

def validate_gender(gender: str) -> bool:
    """Проверить пол"""
    if gender not in ['male', 'female']:
        raise ValidationError("Выбери корректный пол: мужской или женский")
    return True

def get_gender_emoji(gender: str) -> str:
    """Получить эмодзи для пола"""
    return "👨" if gender == 'male' else "👩"

def get_gender_text(gender: str) -> str:
    """Получить текст для пола"""
    return "Мужчина" if gender == 'male' else "Женщина"

def extract_command_arg(text: str) -> Optional[str]:
    """Извлечь аргумент из команды"""
    parts = text.split()
    if len(parts) > 1:
        return " ".join(parts[1:])
    return None

def format_user_profile(user: dict) -> str:
    """Форматировать профиль пользователя"""
    from config import CATEGORIES

    categories = user.get('categories', [])
    categories_names = [CATEGORIES.get(cat, cat) for cat in categories]

    profile_text = f"""
👤 *{user['name']}*, {user['age']} лет {get_gender_emoji(user['gender'])}

📝 О себе:
{user['bio']}

🎯 Интересы:
{', '.join(categories_names) if categories_names else 'Не указаны'}

📅 На платформе с: {user['created_at'][:10]}
"""
    return profile_text

def extract_user_from_command(command: str) -> Optional[str]:
    """Извлечь user_id из команды типа /like_user123"""
    parts = command.split('_', 1)
    if len(parts) > 1:
        return parts[1]
    return None

def extract_match_from_command(command: str) -> Optional[str]:
    """Извлечь match_id из команды типа /chat_user123"""
    if command.startswith('/chat_'):
        return command[6:]  # Убираем '/chat_'
    return None

def get_default_gender_text() -> str:
    """Текст для выбора пола"""
    return "👨 Мужчина или 👩 Женщина?"
