"""
FSM (Finite State Machine) - состояния для диалога с пользователем
"""

from enum import Enum

class UserState(Enum):
    """Состояния пользователя"""
    START = "start"
    MAIN_MENU = "main_menu"

    # Создание профиля
    CREATE_PROFILE = "create_profile"
    ENTER_NAME = "enter_name"
    ENTER_AGE = "enter_age"
    ENTER_GENDER = "enter_gender"
    ENTER_BIO = "enter_bio"
    CHOOSE_CATEGORIES = "choose_categories"

    # Просмотр анкет
    BROWSE_PROFILES = "browse_profiles"
    VIEWING_PROFILE = "viewing_profile"
    CHOOSE_CATEGORY = "choose_category"

    # Чат
    IN_CHAT = "in_chat"
    CHOOSE_MATCH = "choose_match"

    # Редактирование профиля
    EDIT_PROFILE = "edit_profile"
    EDIT_MENU = "edit_menu"

class MainMenuAction(Enum):
    """Действия в главном меню"""
    VIEW_PROFILE = "view_profile"
    BROWSE = "browse"
    MESSAGES = "messages"
    LIKES = "likes"
    EDIT = "edit"

class EditAction(Enum):
    """Действия при редактировании профиля"""
    EDIT_NAME = "edit_name"
    EDIT_AGE = "edit_age"
    EDIT_GENDER = "edit_gender"
    EDIT_BIO = "edit_bio"
    EDIT_CATEGORIES = "edit_categories"
