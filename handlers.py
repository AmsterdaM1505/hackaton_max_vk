"""
Обработчики событий для бота знакомств
"""

import asyncio
import logging
from typing import Optional
from maxapi import Dispatcher, F, Bot
from maxapi.types import MessageCreated, Command, CallbackButton
from maxapi.filters.callback_payload import CallbackPayload

from config import MESSAGES, BOT_TOKEN, CATEGORIES
from database import db
from states import UserState
from keyboards import (
    get_main_menu_keyboard, get_gender_keyboard, get_categories_keyboard,
    get_profile_view_keyboard, format_profile_card, get_edit_profile_keyboard,
    get_browse_category_keyboard, format_matches_list, get_chat_keyboard,
    get_main_menu_buttons, get_gender_buttons, get_categories_buttons,
    get_profile_view_buttons, get_edit_profile_buttons, get_chat_buttons,
    get_profile_action_buttons, get_back_to_menu_button, get_invalid_action_message,
    get_browse_category_buttons
)
from utils import (
    validate_name, validate_age, validate_bio, validate_gender,
    ValidationError, extract_user_from_command, extract_match_from_command,
    format_user_profile, get_gender_text
)

logger = logging.getLogger(__name__)

class DatingBotHandlers:
    def __init__(self, dp: Dispatcher, bot: Bot):
        self.dp = dp
        self.bot = bot
        self.register_handlers()

    async def send_main_menu(self, event: MessageCreated):
        """Отправить главное меню с inline кнопками"""
        user_id = str(event.message.sender.user_id)
        unread_count = db.get_unread_notifications_count(user_id)
        buttons = get_main_menu_buttons(unread_count)
        await event.message.answer(
            "📋 *Главное меню*\n\nВыбери действие:",
            attachments=[buttons.pack()]
        )

    def register_handlers(self):
        """Регистрация всех обработчиков"""

        # Стартовая команда
        @self.dp.message_created(F.message.body.text.startswith('/start'))
        async def handle_start(event: MessageCreated):
            await self.cmd_start(event)

        # Главное меню
        @self.dp.message_created(F.message.body.text == '/menu')
        async def handle_menu(event: MessageCreated):
            await self.cmd_menu(event)

        # Просмотр профиля
        @self.dp.message_created(F.message.body.text == '/view_profile')
        async def handle_view_profile(event: MessageCreated):
            await self.cmd_view_profile(event)

        # Просмотр анкет
        @self.dp.message_created(F.message.body.text == '/browse')
        async def handle_browse(event: MessageCreated):
            await self.cmd_browse_start(event)

        # Выбор категории для просмотра
        @self.dp.message_created(F.message.body.text.in_(
            [f'/{cat}' for cat in CATEGORIES.keys()]
        ))
        async def handle_category_select(event: MessageCreated):
            await self.cmd_browse_category(event)

        # Лайк
        @self.dp.message_created(F.message.body.text == '/like')
        async def handle_like(event: MessageCreated):
            await self.cmd_like(event)

        # Дизлайк
        @self.dp.message_created(F.message.body.text == '/dislike')
        async def handle_dislike(event: MessageCreated):
            await self.cmd_dislike(event)

        # Пропустить
        @self.dp.message_created(F.message.body.text == '/skip')
        async def handle_skip(event: MessageCreated):
            await self.cmd_skip(event)

        # Лайки и мэтчи
        @self.dp.message_created(F.message.body.text == '/likes')
        async def handle_likes(event: MessageCreated):
            await self.cmd_likes(event)

        # Сообщения
        @self.dp.message_created(F.message.body.text == '/messages')
        async def handle_messages(event: MessageCreated):
            await self.cmd_matches(event)

        # Уведомления
        @self.dp.message_created(F.message.body.text == '/notifications')
        async def handle_notifications(event: MessageCreated):
            await self.cmd_notifications(event)

        # Редактирование профиля
        @self.dp.message_created(F.message.body.text == '/edit')
        async def handle_edit(event: MessageCreated):
            await self.cmd_edit_menu(event)

        # Редактирование имени
        @self.dp.message_created(F.message.body.text == '/edit_name')
        async def handle_edit_name(event: MessageCreated):
            await self.cmd_edit_name(event)

        # Редактирование возраста
        @self.dp.message_created(F.message.body.text == '/edit_age')
        async def handle_edit_age(event: MessageCreated):
            await self.cmd_edit_age(event)

        # Редактирование пола
        @self.dp.message_created(F.message.body.text == '/edit_gender')
        async def handle_edit_gender(event: MessageCreated):
            await self.cmd_edit_gender(event)

        # Редактирование описания
        @self.dp.message_created(F.message.body.text == '/edit_bio')
        async def handle_edit_bio(event: MessageCreated):
            await self.cmd_edit_bio(event)

        # Редактирование категорий
        @self.dp.message_created(F.message.body.text == '/edit_categories')
        async def handle_edit_categories(event: MessageCreated):
            await self.cmd_edit_categories(event)

        # Выбор пола
        @self.dp.message_created(F.message.body.text.in_(['/gender_male', '/gender_female']))
        async def handle_gender_select(event: MessageCreated):
            await self.cmd_gender_select(event)

        # Завершение выбора категорий
        @self.dp.message_created(F.message.body.text == '/done_categories')
        async def handle_done_categories(event: MessageCreated):
            await self.cmd_done_categories(event)

        # Вход в чат с пользователем
        @self.dp.message_created(F.message.body.text.startswith('/chat_'))
        async def handle_chat_start(event: MessageCreated):
            await self.cmd_start_chat(event)

        # Прерывание чата
        @self.dp.message_created(F.message.body.text == '/stop_chat')
        async def handle_stop_chat(event: MessageCreated):
            await self.cmd_stop_chat(event)

        # Обработка текстовых сообщений (всё остальное)
        @self.dp.message_created(F.message.body.text)
        async def handle_text_message(event: MessageCreated):
            await self.handle_text_input(event)

        # ===== CALLBACK ОБРАБОТЧИКИ (для inline кнопок) =====

        @self.dp.message_callback()
        async def handle_command_callback(event: MessageCreated):
            await self.cmd_command(event)


    # ===== ОСНОВНЫЕ КОМАНДЫ =====

    async def cmd_command(self, event: MessageCreated):
        command = event.callback.payload
        match command:
            # --- Основное меню ---
            case '/start':
                await self.cmd_start(event)
            case '/menu':
                await self.cmd_menu(event)

            # --- Просмотр профиля ---
            case '/view_profile':
                await self.cmd_view_profile(event)

            # --- Просмотр анкет ---
            case '/browse':
                await self.cmd_browse_start(event)
            case cmd if cmd in [f"/{cat}" for cat in CATEGORIES.keys()]:
                await self.cmd_browse_category(event)

            # --- Действия с анкетами ---
            case '/like':
                await self.cmd_like(event)
            case '/dislike':
                await self.cmd_dislike(event)
            case '/skip':
                await self.cmd_skip(event)

            # --- Лайки и сообщения ---
            case '/likes':
                await self.cmd_likes(event)
            case '/messages':
                await self.cmd_matches(event)
            case '/notifications':
                await self.cmd_notifications(event)

            # --- Редактирование профиля ---
            case '/edit':
                await self.cmd_edit_menu(event)
            case '/edit_name':
                await self.cmd_edit_name(event)
            case '/edit_age':
                await self.cmd_edit_age(event)
            case '/edit_gender':
                await self.cmd_edit_gender(event)
            case '/edit_bio':
                await self.cmd_edit_bio(event)
            case '/edit_categories':
                await self.cmd_edit_categories(event)
            case '/done_categories':
                await self.cmd_done_categories(event)
            case cmd if cmd in ['/gender_male', '/gender_female']:
                await self.cmd_gender_select(event)

            # --- Чат ---
            case cmd if cmd.startswith('/chat_'):
                await self.cmd_start_chat(event)
            case '/stop_chat':
                await self.cmd_stop_chat(event)

            # --- Команда не найдена ---
            case _:
                await event.answer("⚠️ Неизвестная команда, попробуйте /menu")

    async def cmd_start(self, event: MessageCreated):
        """Команда /start - автоматическая регистрация и в меню"""
        rep = self.dp
        CallbackPayload.filter()
        kek = F.event.message.body.text
        sf = Dispatcher.Event.callback.payload
        user_id = str(event.message.sender.user_id)
        username = event.message.sender.username or event.message.sender.first_name
        first_name = event.message.sender.first_name or "Друг"

        # Проверяем, есть ли уже профиль
        if db.user_exists(user_id):
            # Пользователь уже зарегистрирован
            unread_count = db.get_unread_notifications_count(user_id)
            user = db.get_user(user_id)

            if user:
                welcome_msg = f"👋 Добро пожаловать, {user['name']}!"
                await event.message.answer(welcome_msg)

            # Отправляем меню с inline кнопками
            buttons = get_main_menu_buttons(unread_count)
            await event.message.answer(
                "📋 *Главное меню*\n\nВыбери действие:",
                attachments=[buttons.pack()]
            )
            db.set_user_state(user_id, UserState.MAIN_MENU.value)
        else:
            # Автоматическая регистрация новых пользователей
            success = db.create_user(
                user_id=user_id,
                username=username,
                name=first_name,
                age=18,  # Дефолтный возраст
                gender='male',  # Дефолтный пол
                bio='Новый пользователь',  # Дефолтное описание
                categories=['love']  # Дефолтная категория
            )

            if success:
                await event.message.answer(
                    f"🎉 Привет, {first_name}!\n\n"
                    f"Ты успешно зарегистрирован! 🎊\n\n"
                    f"Не забудь отредактировать свой профиль, чтобы другие могли тебя найти."
                )

                # Отправляем меню
                buttons = get_main_menu_buttons(0)
                await event.message.answer(
                    "📋 *Главное меню*\n\nВыбери действие:",
                    attachments=[buttons.pack()]
                )
                db.set_user_state(user_id, UserState.MAIN_MENU.value)
                logger.info(f"✅ Новый пользователь зарегистрирован: {user_id} - {first_name}")
            else:
                await event.message.answer("❌ Ошибка регистрации. Попробуй позже.")

    async def cmd_menu(self, event: MessageCreated):
        """Возврат в главное меню"""
        user_id = str(event.message.sender.user_id)
        db.clear_user_state(user_id)
        db.set_user_state(user_id, UserState.MAIN_MENU.value)
        unread_count = db.get_unread_notifications_count(user_id)

        # Отправляем меню с inline кнопками
        buttons = get_main_menu_buttons(unread_count)
        await event.message.answer(
            "📋 *Главное меню*\n\nВыбери действие:",
            attachments=[buttons.pack()]
        )

    async def cmd_view_profile(self, event: MessageCreated):
        """Показать свой профиль"""
        user_id = str(event.message.recipient.user_id)
        user = db.get_user(user_id)

        if not user:
            await event.message.answer("❌ Профиль не найден!\n\nПопробуй /start")
            return

        profile_text = format_user_profile(user)
        await event.message.answer(profile_text)

        db.set_user_state(user_id, UserState.MAIN_MENU.value)

        buttons = get_profile_action_buttons()
        await event.message.answer(
            "Что ты хочешь сделать?",
            attachments=[buttons.pack()]
        )

    async def cmd_browse_start(self, event: MessageCreated):
        """Начало просмотра анкет"""
        user_id = str(event.message.recipient.user_id)

        if not db.user_exists(user_id):
            await event.message.answer("❌ Профиль не найден!\n\nПопробуй /start")
            return

        db.set_user_state(user_id, UserState.CHOOSE_CATEGORY.value)
        buttons = get_browse_category_buttons()
        await event.message.answer(
            "👀 Выбери категорию анкет:",
            attachments=[buttons.pack()]
        )

    async def cmd_browse_category(self, event: MessageCreated):
        """Просмотр анкет в выбранной категории"""
        user_id = str(event.message.recipient.user_id)
        category = event.callback.payload[1:]  # Убираем '/'

        if category not in CATEGORIES:
            await event.message.answer("❌ Неизвестная категория")
            return

        # Получаем следующий профиль
        profile = db.get_profile_for_user(user_id, category)

        if not profile:
            await event.message.answer(MESSAGES['no_profiles'])
            buttons = get_browse_category_buttons()
            await event.message.answer(
                "Выбери другую категорию или вернись в меню:",
                attachments=[buttons.pack()]
            )
            return

        # Сохраняем текущий профиль и категорию в состояние
        db.set_user_state(user_id, UserState.VIEWING_PROFILE.value, {
            'current_profile': profile,
            'category': category
        })

        # Показываем карточку профиля
        card = format_profile_card(profile)
        await event.message.answer(card)

        buttons = get_profile_view_buttons()
        await event.message.answer(
            "Выбери действие:",
            attachments=[buttons.pack()]
        )

    async def cmd_like(self, event: MessageCreated):
        """Лайк профилю"""
        user_id = str(event.message.sender.user_id)
        state, data = db.get_user_state(user_id)

        if state != UserState.VIEWING_PROFILE.value or not data:
            await event.message.answer("⚠️ Сначала выбери анкету для просмотра")
            return

        profile = data.get('current_profile')
        if not profile:
            return

        profile_id = profile['user_id']
        current_user = db.get_user(user_id)
        other_user = db.get_user(profile_id)

        # Добавляем лайк
        db.add_like(user_id, profile_id)

        # Отправляем уведомление о лайке
        db.add_notification(
            user_id=profile_id,
            from_user_id=user_id,
            from_user_name=current_user['name'],
            from_user_username=current_user['username'],
            notification_type='like',
            message=f"{current_user['name']} ({current_user['age']}) лайкнул вашу анкету!"
        )

        # Проверяем, есть ли обратный лайк (матч!)
        if db.get_matches(profile_id) and user_id in db.get_matches(profile_id):
            # Создаём уведомления о взаимной симпатии для обоих
            db.add_notification(
                user_id=user_id,
                from_user_id=profile_id,
                from_user_name=other_user['name'],
                from_user_username=other_user['username'],
                notification_type='match',
                message=f"💕 Взаимная симпатия с {other_user['name']}! @{other_user['username']}"
            )

            db.add_notification(
                user_id=profile_id,
                from_user_id=user_id,
                from_user_name=current_user['name'],
                from_user_username=current_user['username'],
                notification_type='match',
                message=f"💕 Взаимная симпатия с {current_user['name']}! @{current_user['username']}"
            )

            await event.message.answer(
                f"💕 МЭТЧ! Вы понравились друг другу!\n\n"
                f"Напиши {'ей' if other_user['gender'] == 'female' else 'ему'}: /chat_{profile_id}\n"
                f"или в /messages"
            )
        else:
            # Сообщение об успешном лайке
            await event.message.answer(
                f"❤️ Вы лайкнули {profile['name']}!\n\n"
                f"Если {'ей' if other_user['gender'] == 'female' else 'ему'} вы понравитесь, "
                f"вы получите уведомление!"
            )

        # Показываем следующий профиль
        await self._show_next_profile(event, data.get('category'))

    async def cmd_dislike(self, event: MessageCreated):
        """Дизлайк профилю"""
        user_id = str(event.message.sender.user_id)
        state, data = db.get_user_state(user_id)

        if state != UserState.VIEWING_PROFILE.value or not data:
            await event.message.answer("⚠️ Сначала выбери анкету для просмотра")
            return

        profile = data.get('current_profile')
        if not profile:
            return

        db.add_dislike(user_id, profile['user_id'])

        # Показываем следующий профиль
        await self._show_next_profile(event, data.get('category'))

    async def cmd_skip(self, event: MessageCreated):
        """Пропустить профиль"""
        user_id = str(event.message.sender.user_id)
        state, data = db.get_user_state(user_id)

        if state != UserState.VIEWING_PROFILE.value or not data:
            await event.message.answer("⚠️ Сначала выбери анкету для просмотра")
            return

        await self._show_next_profile(event, data.get('category'))

    async def cmd_likes(self, event: MessageCreated):
        """Показать лайки и мэтчи"""
        user_id = str(event.message.sender.user_id)
        matches = []

        # Получаем ID мэтчей
        match_ids = db.get_matches(user_id)

        # Преобразуем в объекты пользователей
        for match_id in match_ids:
            user = db.get_user(match_id)
            if user:
                matches.append(user)

        db.set_user_state(user_id, UserState.CHOOSE_MATCH.value)
        await event.message.answer(format_matches_list(matches))

        # Показываем кнопку возврата
        buttons = get_back_to_menu_button()
        await event.message.answer(
            "Вернись в меню:",
            attachments=[buttons.pack()]
        )

    async def cmd_matches(self, event: MessageCreated):
        """Показать мэтчи и чаты"""
        user_id = str(event.message.sender.user_id)
        matches = []

        match_ids = db.get_matches(user_id)
        for match_id in match_ids:
            user = db.get_user(match_id)
            if user:
                matches.append(user)

        db.set_user_state(user_id, UserState.CHOOSE_MATCH.value)
        await event.message.answer(format_matches_list(matches))

        # Если есть мэтчи, показываем кнопку возврата
        if matches:
            buttons = get_back_to_menu_button()
            await event.message.answer(
                "Выбери из списка выше или вернись в меню:",
                attachments=[buttons.pack()]
            )
        else:
            buttons = get_back_to_menu_button()
            await event.message.answer(
                "Вернись в меню:",
                attachments=[buttons.pack()]
            )

    async def cmd_notifications(self, event: MessageCreated):
        """Показать уведомления"""
        user_id = str(event.message.sender.user_id)
        notifications = db.get_notifications(user_id)

        if not notifications:
            await event.message.answer("📭 У тебя пока нет уведомлений")
        else:
            # Форматируем и отправляем уведомления
            notification_text = "🔔 *Твои уведомления:*\n\n"

            for notif in notifications:
                if notif['notification_type'] == 'like':
                    notification_text += f"❤️ *Лайк* от {notif['from_user_name']}\n"
                    notification_text += f"   {notif['message']}\n"
                    notification_text += f"   @{notif['from_user_username']}\n\n"
                elif notif['notification_type'] == 'match':
                    notification_text += f"💕 *МЭТЧ!*\n"
                    notification_text += f"   {notif['message']}\n\n"

            await event.message.answer(notification_text)

            # Отмечаем все уведомления как прочитанные
            db.mark_all_notifications_as_read(user_id)

        db.set_user_state(user_id, UserState.MAIN_MENU.value)

        # Возвращаемся в меню
        await self.send_main_menu(event)

    # ===== ЧАТЫ И ПЕРЕПИСКА =====

    async def cmd_start_chat(self, event: MessageCreated):
        """Начать чат с пользователем (после взаимной симпатии)"""
        user_id = str(event.message.sender.user_id)
        text = event.message.body.text

        # Извлекаем ID пользователя из команды /chat_<user_id>
        try:
            match_id = text.split('_', 1)[1]
        except (IndexError, ValueError):
            await event.message.answer("⚠️ Неверный формат команды")
            buttons = get_back_to_menu_button()
            await event.message.answer(
                "Вернись в меню:",
                attachments=[buttons.pack()]
            )
            return

        # Проверяем, что пользователь существует
        match_user = db.get_user(match_id)
        if not match_user:
            await event.message.answer("⚠️ Пользователь не найден")
            buttons = get_back_to_menu_button()
            await event.message.answer(
                "Вернись в меню:",
                attachments=[buttons.pack()]
            )
            return

        # Проверяем, что это мэтч (взаимная симпатия)
        if match_id not in db.get_matches(user_id):
            await event.message.answer(
                "⚠️ Это не ваш мэтч.\n\n"
                "Сначала нужна взаимная симпатия!"
            )
            buttons = get_back_to_menu_button()
            await event.message.answer(
                "Вернись в меню:",
                attachments=[buttons.pack()]
            )
            return

        # Проверяем, что чат не заблокирован
        if db.is_chat_blocked(user_id, match_id):
            await event.message.answer(
                "⛔ Чат с этим пользователем был прерван и больше невозможен."
            )
            buttons = get_back_to_menu_button()
            await event.message.answer(
                "Вернись в меню:",
                attachments=[buttons.pack()]
            )
            return

        # Устанавливаем состояние IN_CHAT
        db.set_user_state(user_id, UserState.IN_CHAT.value, {
            'match_id': match_id
        })

        await event.message.answer(
            f"💬 Вы вошли в чат с {match_user['name']}\n\n"
            f"Напиши своё сообщение (введи текст или команду /stop_chat для выхода)"
        )

    async def cmd_stop_chat(self, event: MessageCreated):
        """Прервать чат и заблокировать переписку с пользователем"""
        user_id = str(event.message.sender.user_id)
        state, data = db.get_user_state(user_id)

        if state != UserState.IN_CHAT.value or not data:
            await event.message.answer("⚠️ Ты не находишься в чате")
            return

        match_id = data.get('match_id')
        if not match_id:
            await event.message.answer("⚠️ Ошибка чата")
            return

        # Блокируем чат (обоюдно)
        db.block_chat(user_id, match_id)

        # Очищаем состояние
        db.clear_user_state(user_id)

        match_user = db.get_user(match_id)
        await event.message.answer(
            f"❌ Чат с {match_user['name'] if match_user else 'пользователем'} прерван.\n"
            f"Вы больше не сможете переписываться."
        )

        # Возвращаемся в меню
        await self.send_main_menu(event)

    # ===== СОЗДАНИЕ И РЕДАКТИРОВАНИЕ ПРОФИЛЯ =====

    async def cmd_edit_menu(self, event: MessageCreated):
        """Меню редактирования профиля"""
        user_id = str(event.message.sender.user_id)

        if not db.user_exists(user_id):
            await event.message.answer("❌ Сначала создай свой профиль!\n\n/start")
            return

        buttons = get_edit_profile_buttons()
        await event.message.answer(
            "Что ты хочешь изменить?",
            attachments=[buttons.pack()]
        )

    async def cmd_edit_name(self, event: MessageCreated):
        """Редактировать имя"""
        user_id = str(event.message.sender.user_id)
        db.set_user_state(user_id, UserState.ENTER_NAME.value, {'editing': True})
        await event.message.answer(MESSAGES['enter_name'])

    async def cmd_edit_age(self, event: MessageCreated):
        """Редактировать возраст"""
        user_id = str(event.message.sender.user_id)
        db.set_user_state(user_id, UserState.ENTER_AGE.value, {'editing': True})
        await event.message.answer(MESSAGES['enter_age'])

    async def cmd_edit_gender(self, event: MessageCreated):
        """Редактировать пол"""
        user_id = str(event.message.sender.user_id)
        db.set_user_state(user_id, UserState.ENTER_GENDER.value, {'editing': True})
        buttons = get_gender_buttons()
        await event.message.answer(
            "Выбери свой пол:",
            attachments=[buttons.pack()]
        )

    async def cmd_edit_bio(self, event: MessageCreated):
        """Редактировать описание"""
        user_id = str(event.message.sender.user_id)
        db.set_user_state(user_id, UserState.ENTER_BIO.value, {'editing': True})
        await event.message.answer(MESSAGES['enter_bio'])

    async def cmd_edit_categories(self, event: MessageCreated):
        """Редактировать категории"""
        user_id = str(event.message.sender.user_id)
        db.set_user_state(user_id, UserState.CHOOSE_CATEGORIES.value, {'editing': True})
        buttons = get_categories_buttons()
        await event.message.answer(
            "Выбери категории (можешь несколько):",
            attachments=[buttons.pack()]
        )

    async def cmd_gender_select(self, event: MessageCreated):
        """Выбор пола"""
        user_id = str(event.message.sender.user_id)
        gender = 'male' if event.message.body.text == '/gender_male' else 'female'

        state, data = db.get_user_state(user_id)

        # Если редактируем
        if data.get('editing'):
            db.update_user(user_id, gender=gender)
            await event.message.answer("✅ Пол обновлён!")
            unread_count = db.get_unread_notifications_count(user_id)

            # Отправляем меню с inline кнопками
            buttons = get_main_menu_buttons(unread_count)
            await event.message.answer(
                "📋 *Главное меню*\n\nВыбери действие:",
                attachments=[buttons.pack()]
            )
            db.clear_user_state(user_id)
            return

        # Если создаём профиль
        db.set_user_state(user_id, UserState.ENTER_BIO.value, {
            'name': data.get('name'),
            'age': data.get('age'),
            'gender': gender
        })
        await event.message.answer("Спасибо! Теперь расскажи о себе:")
        await event.message.answer(MESSAGES['enter_bio'])

    async def cmd_done_categories(self, event: MessageCreated):
        """Завершение выбора категорий"""
        user_id = str(event.message.sender.user_id)
        state, data = db.get_user_state(user_id)

        categories = data.get('categories', [])

        if not categories:
            await event.message.answer("⚠️ Выбери хотя бы одну категорию")
            return

        # Если редактируем
        if data.get('editing'):
            db.update_user(user_id, categories=categories)
            await event.message.answer("✅ Категории обновлены!")
            unread_count = db.get_unread_notifications_count(user_id)

            # Отправляем меню с inline кнопками
            buttons = get_main_menu_buttons(unread_count)
            await event.message.answer(
                "📋 *Главное меню*\n\nВыбери действие:",
                attachments=[buttons.pack()]
            )
            db.clear_user_state(user_id)
            return

        # Если создаём профиль
        user = db.get_user(user_id)
        if not user:
            # Создаём профиль
            username = event.message.sender.username or event.message.sender.first_name
            success = db.create_user(
                user_id=user_id,
                username=username,
                name=data['name'],
                age=data['age'],
                gender=data['gender'],
                bio=data['bio'],
                categories=categories
            )

            if not success:
                await event.message.answer("❌ Ошибка при сохранении профиля. Попробуй заново.")
                return

            print(f"✅ Профиль создан: {user_id} - {data['name']}")

        await event.message.answer(MESSAGES['profile_created'])
        unread_count = db.get_unread_notifications_count(user_id)

        # Отправляем меню с inline кнопками
        buttons = get_main_menu_buttons(unread_count)
        await event.message.answer(
            "📋 *Главное меню*\n\nВыбери действие:",
            attachments=[buttons.pack()]
        )
        db.clear_user_state(user_id)

    # ===== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ =====

    async def handle_text_input(self, event: MessageCreated):
        """Обработка текстовых входов в зависимости от состояния"""
        user_id = str(event.message.sender.user_id)
        text = event.message.body.text
        state, data = db.get_user_state(user_id)

        # Имя
        if state == UserState.ENTER_NAME.value:
            await self.handle_name_input(event, data)

        # Возраст
        elif state == UserState.ENTER_AGE.value:
            await self.handle_age_input(event, data)

        # Описание
        elif state == UserState.ENTER_BIO.value:
            await self.handle_bio_input(event, data)

        # Категории (выбор)
        elif state == UserState.CHOOSE_CATEGORIES.value:
            await self.handle_category_choice(event, data)

        # Чат
        elif state == UserState.IN_CHAT.value:
            await self.handle_chat_message(event, data)

        # По умолчанию - показываем меню с предупреждением
        else:
            # Если пользователь вообще не зарегистрирован
            if not db.user_exists(user_id):
                await event.message.answer(
                    "👤 Сначала зарегистрируйся командой /start"
                )
                return

            # Некорректное действие - предлагаем меню
            await event.message.answer(
                "⚠️ Команда не распознана.\n\n"
                "Используй кнопки в меню или вернись в главное меню:"
            )

            unread_count = db.get_unread_notifications_count(user_id)
            buttons = get_main_menu_buttons(unread_count)
            await event.message.answer(
                "📋 *Главное меню*\n\nВыбери действие:",
                attachments=[buttons.pack()]
            )
            db.set_user_state(user_id, UserState.MAIN_MENU.value)

    async def handle_name_input(self, event: MessageCreated, data: dict):
        """Обработка ввода имени"""
        user_id = str(event.message.sender.user_id)
        name = event.message.body.text

        try:
            validate_name(name)
        except ValidationError as e:
            await event.message.answer(f"❌ {str(e)}")
            return

        # Если редактируем
        if data.get('editing'):
            db.update_user(user_id, name=name)
            await event.message.answer("✅ Имя обновлено!")
            await self.send_main_menu(event)
            db.clear_user_state(user_id)
            return

        # Если создаём
        db.set_user_state(user_id, UserState.ENTER_AGE.value, {
            'name': name
        })
        await event.message.answer(MESSAGES['enter_age'])

    async def handle_age_input(self, event: MessageCreated, data: dict):
        """Обработка ввода возраста"""
        user_id = str(event.message.sender.user_id)
        age_str = event.message.body.text

        try:
            age = validate_age(age_str)
        except ValidationError as e:
            await event.message.answer(f"❌ {str(e)}")
            return

        # Если редактируем
        if data.get('editing'):
            db.update_user(user_id, age=age)
            await event.message.answer("✅ Возраст обновлён!")
            await self.send_main_menu(event)
            db.clear_user_state(user_id)
            return

        # Если создаём
        db.set_user_state(user_id, UserState.ENTER_GENDER.value, {
            'name': data.get('name'),
            'age': age
        })
        buttons = get_gender_buttons()
        await event.message.answer(
            "Выбери свой пол:",
            attachments=[buttons.pack()]
        )

    async def handle_bio_input(self, event: MessageCreated, data: dict):
        """Обработка ввода описания"""
        user_id = str(event.message.sender.user_id)
        bio = event.message.body.text

        try:
            validate_bio(bio)
        except ValidationError as e:
            await event.message.answer(f"❌ {str(e)}")
            return

        # Если редактируем
        if data.get('editing'):
            db.update_user(user_id, bio=bio)
            await event.message.answer("✅ Описание обновлено!")
            await self.send_main_menu(event)
            db.clear_user_state(user_id)
            return

        # Если создаём
        db.set_user_state(user_id, UserState.CHOOSE_CATEGORIES.value, {
            'name': data.get('name'),
            'age': data.get('age'),
            'gender': data.get('gender'),
            'bio': bio,
            'categories': []
        })
        buttons = get_categories_buttons()
        await event.message.answer(
            "Выбери категории (можешь несколько):",
            attachments=[buttons.pack()]
        )

    async def handle_category_choice(self, event: MessageCreated, data: dict):
        """Обработка выбора категорий"""
        user_id = str(event.message.sender.user_id)
        text = event.message.body.text

        # Если это команда категории
        if text.startswith('/') and text[1:] in CATEGORIES:
            category = text[1:]
            categories = data.get('categories', [])

            if category not in categories:
                categories.append(category)
                data['categories'] = categories

                db.set_user_state(user_id, UserState.CHOOSE_CATEGORIES.value, data)
                await event.message.answer(f"✅ {CATEGORIES[category]} выбрана!")

                buttons = get_categories_buttons()
                await event.message.answer(
                    "Выбери ещё категории или заверши выбор:",
                    attachments=[buttons.pack()]
                )
            else:
                await event.message.answer(
                    f"⚠️ {CATEGORIES[category]} уже выбрана!\n\n"
                    f"Выбери другую или завершись выбор:"
                )
                buttons = get_categories_buttons()
                await event.message.answer(
                    "Выбери действие:",
                    attachments=[buttons.pack()]
                )
        else:
            await event.message.answer(
                "⚠️ Пожалуйста, выбери категорию из списка кнопок ниже!"
            )
            buttons = get_categories_buttons()
            await event.message.answer(
                "Выбери категории:",
                attachments=[buttons.pack()]
            )

    async def handle_chat_message(self, event: MessageCreated, data: dict):
        """Обработка сообщений в чате"""
        user_id = str(event.message.sender.user_id)
        match_id = data.get('match_id')
        text = event.message.body.text

        if not match_id:
            await event.message.answer("⚠️ Ошибка чата")
            return

        # Проверяем, что чат не заблокирован
        if db.is_chat_blocked(user_id, match_id):
            await event.message.answer(
                "⛔ Чат с этим пользователем был прерван и больше невозможен."
            )
            db.clear_user_state(user_id)
            await self.send_main_menu(event)
            return

        # Сохраняем сообщение
        db.save_message(user_id, match_id, text)

        match_user = db.get_user(match_id)
        await event.message.answer(
            f"💬 Сообщение отправлено для {match_user['name']}!\n\n" +
            get_chat_keyboard(match_id)
        )

    # ===== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ =====

    async def _show_next_profile(self, event: MessageCreated, category: str):
        """Показать следующий профиль в категории"""
        user_id = str(event.message.sender.user_id)

        if not category or category not in CATEGORIES:
            buttons = get_browse_category_buttons()
            await event.message.answer(
                "Выбери категорию:",
                attachments=[buttons.pack()]
            )
            return

        profile = db.get_profile_for_user(user_id, category)

        if not profile:
            await event.message.answer(MESSAGES['no_profiles'])
            buttons = get_browse_category_buttons()
            await event.message.answer(
                "Выбери другую категорию:",
                attachments=[buttons.pack()]
            )
            db.set_user_state(user_id, UserState.CHOOSE_CATEGORY.value)
            return

        db.set_user_state(user_id, UserState.VIEWING_PROFILE.value, {
            'current_profile': profile,
            'category': category
        })

        card = format_profile_card(profile)
        await event.message.answer(card)

        buttons = get_profile_view_buttons()
        await event.message.answer(
            "Выбери действие:",
            attachments=[buttons.pack()]
        )
