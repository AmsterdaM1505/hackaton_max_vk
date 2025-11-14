"""
Клавиатуры (кнопки) для бота
"""

from config import CATEGORIES, INLINE_BUTTONS
from typing import List
from maxapi.types import ButtonsPayload
from maxapi.types.attachments.buttons import CallbackButton

def get_main_menu_keyboard(unread_count: int = 0) -> str:
    """Главное меню"""
    notification_badge = f" ({unread_count})" if unread_count > 0 else ""
    return f"""
📋 *Главное меню*

Выбери действие:
1️⃣ `/view_profile` - Мой профиль
2️⃣ `/browse` - Просматривать анкеты
3️⃣ `/messages` - Сообщения и чаты
4️⃣ `/likes` - Мои лайки
🔔 `/notifications` - Уведомления{notification_badge}
5️⃣ `/edit` - Редактировать профиль
"""

def get_gender_keyboard() -> str:
    """Выбор пола"""
    return """
Выбери свой пол:
`/gender_male` - 👨 Мужской
`/gender_female` - 👩 Женский
"""

def get_categories_keyboard() -> str:
    """Выбор категорий знакомств"""
    keyboard = "Выбери категории (можешь несколько):\n\n"
    for i, (key, value) in enumerate(CATEGORIES.items(), 1):
        keyboard += f"{i}️⃣ `/{key}` - {value}\n"
    keyboard += "\n✅ `/done_categories` - Завершить выбор"
    return keyboard

def get_profile_view_keyboard(user_id: str) -> str:
    """Клавиатура для просмотра профиля"""
    return f"""
❤️ `/like` - {INLINE_BUTTONS['like']}
👎 `/dislike` - {INLINE_BUTTONS['dislike']}
⏭️ `/skip` - {INLINE_BUTTONS['skip']}
🏠 `/menu` - Вернуться в меню
"""

def get_browse_category_keyboard() -> str:
    """Выбор категории для просмотра"""
    keyboard = "Какие анкеты ты хочешь смотреть?\n\n"
    for i, (key, value) in enumerate(CATEGORIES.items(), 1):
        keyboard += f"{i}️⃣ `/{key}` - {value}\n"
    keyboard += "\n🏠 `/menu` - Вернуться в меню"
    return keyboard

def format_profile_card(profile: dict) -> str:
    """Форматировать карточку профиля"""
    bio = profile.get('bio', 'Нет описания')
    categories = profile.get('categories', [])

    # Переводим коды категорий в названия
    categories_names = [CATEGORIES.get(cat, cat) for cat in categories]

    card = f"""
👤 *{profile['name']}*, {profile['age']} лет

📝 О себе:
{bio}

🎯 Интересы:
{', '.join(categories_names) if categories_names else 'Не указаны'}
"""
    return card

def get_edit_profile_keyboard() -> str:
    """Меню редактирования профиля"""
    return """
📝 *Редактирование профиля*

Что ты хочешь изменить?
1️⃣ `/edit_name` - Имя
2️⃣ `/edit_age` - Возраст
3️⃣ `/edit_gender` - Пол
4️⃣ `/edit_bio` - Описание
5️⃣ `/edit_categories` - Категории
6️⃣ `/menu` - Вернуться в меню
"""

def get_profile_info_keyboard(user_id: str) -> str:
    """Информация о профиле с кнопками действий"""
    return """
🏠 `/menu` - Главное меню
✏️ `/edit` - Редактировать
"""

def format_matches_list(matches: List[dict]) -> str:
    """Форматировать список матчей"""
    if not matches:
        return "😔 У тебя пока нет взаимных лайков"

    text = "💕 *Твои мэтчи:*\n\n"
    for match in matches:
        text += f"👤 {match['name']}, {match['age']}\n"
        text += f"🏠 `/chat_{match['user_id']}` - Написать\n\n"

    return text

def get_chat_keyboard(match_id: str) -> str:
    """Клавиатура в чате"""
    return f"""
Сообщение отправлено! ✅

💬 Напиши ещё что-нибудь или:
🏠 `/menu` - Вернуться в меню
👤 `/back` - К списку мэтчей
❌ `/stop_chat` - Прервать беседу"""


# ===== INLINE КНОПКИ =====

def get_main_menu_buttons(unread_count: int = 0) -> ButtonsPayload:
    """Inline кнопки главного меню"""
    notification_badge = f" ({unread_count})" if unread_count > 0 else ""
    return ButtonsPayload(buttons=[
        [
            CallbackButton(text="👤 Мой профиль", payload="/view_profile"),
            CallbackButton(text="👥 Просмотр анкет", payload="/browse")
        ],
        [
            CallbackButton(text="💬 Сообщения", payload="/messages"),
            CallbackButton(text="❤️ Мои лайки", payload="/likes")
        ],
        [
            CallbackButton(text=f"🔔 Уведомления{notification_badge}", payload="/notifications"),
            CallbackButton(text="✏️ Редактировать", payload="/edit")
        ]
    ])


def get_gender_buttons() -> ButtonsPayload:
    """Inline кнопки выбора пола"""
    return ButtonsPayload(buttons=[
        [
            CallbackButton(text="👨 Мужской", payload="/gender_male"),
            CallbackButton(text="👩 Женский", payload="/gender_female")
        ]
    ])


def get_categories_buttons() -> ButtonsPayload:
    """Inline кнопки выбора категорий"""
    buttons = []
    current_row = []

    for i, (key, value) in enumerate(CATEGORIES.items(), 1):
        current_row.append(CallbackButton(text=f"{value}", payload=f"/{key}"))
        if i % 2 == 0:
            buttons.append(current_row)
            current_row = []

    # Добавляем оставшиеся кнопки
    if current_row:
        buttons.append(current_row)

    # Добавляем кнопку завершения
    buttons.append([CallbackButton(text="✅ Завершить выбор", payload="/done_categories")])

    return ButtonsPayload(buttons=buttons)


def get_profile_view_buttons() -> ButtonsPayload:
    """Inline кнопки для просмотра профиля"""
    return ButtonsPayload(buttons=[
        [
            CallbackButton(text="❤️ Лайк", payload="/like"),
            CallbackButton(text="👎 Дизлайк", payload="/dislike"),
            CallbackButton(text="⏭️ Пропустить", payload="/skip")
        ],
        [
            CallbackButton(text="🏠 В меню", payload="/menu")
        ]
    ])


def get_browse_category_buttons(user=None) -> ButtonsPayload:
    """Inline кнопки выбора категории для просмотра"""
    buttons = []
    current_row = []
    if user is None:
        for i, (key, value) in enumerate(CATEGORIES.items(), 1):
            current_row.append(CallbackButton(text=f"{value}", payload=f"/{key}"))
            if i % 2 == 0:
                buttons.append(current_row)
                current_row = []

        if current_row:
            buttons.append(current_row)

        buttons.append([CallbackButton(text="🏠 В меню", payload="/menu")])

        return ButtonsPayload(buttons=buttons)
    else:
        categories = user.get('categories', [])
        categories_names = [CATEGORIES.get(cat, cat) for cat in categories]

        for i, (key, value) in enumerate(CATEGORIES.items(), 1):
            if value in categories_names:
                current_row.append(CallbackButton(text=f"{value}", payload=f"/{key}"))
                if i % 2 == 0:
                    buttons.append(current_row)
                    current_row = []

        if current_row:
            buttons.append(current_row)

        buttons.append([CallbackButton(text="🏠 В меню", payload="/menu")])

        return ButtonsPayload(buttons=buttons)


def get_edit_profile_buttons() -> ButtonsPayload:
    """Inline кнопки меню редактирования профиля"""
    return ButtonsPayload(buttons=[
        [
            CallbackButton(text="📝 Имя", payload="/edit_name"),
            CallbackButton(text="🎂 Возраст", payload="/edit_age")
        ],
        [
            CallbackButton(text="⚧️ Пол", payload="/edit_gender"),
            CallbackButton(text="📄 Описание", payload="/edit_bio")
        ],
        [
            CallbackButton(text="🎯 Категории", payload="/edit_categories"),
            CallbackButton(text="🏠 В меню", payload="/menu")
        ]
    ])


def get_chat_buttons(match_id: str) -> ButtonsPayload:
    """Inline кнопки в чате"""
    return ButtonsPayload(buttons=[
        [
            CallbackButton(text="🏠 В меню", payload="/menu"),
            CallbackButton(text="❌ Прервать чат", payload="/stop_chat")
        ]
    ])


def get_profile_action_buttons() -> ButtonsPayload:
    """Inline кнопки для действий с профилем"""
    return ButtonsPayload(buttons=[
        [
            CallbackButton(text="✏️ Редактировать", payload="/edit"),
            CallbackButton(text="🏠 В меню", payload="/menu")
        ]
    ])


def get_back_to_menu_button() -> ButtonsPayload:
    """Inline кнопка для возврата в меню"""
    return ButtonsPayload(buttons=[
        [
            CallbackButton(text="🏠 В меню", payload="/menu")
        ]
    ])


def get_invalid_action_message() -> str:
    """Сообщение при неверном действии"""
    return """
⚠️ Команда не распознана

Пожалуйста, используй кнопки в меню или введи команду:
- `/start` - Начать
- `/menu` - Главное меню
"""
