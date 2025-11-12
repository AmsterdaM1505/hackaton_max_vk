"""
Главный файл бота для знакомств в MAX
"""

import asyncio
import logging
import sys
from pathlib import Path

# Добавляем текущую директорию в path
sys.path.insert(0, str(Path(__file__).parent))

from maxapi import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import DatingBotHandlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция для запуска бота"""

    if not BOT_TOKEN or BOT_TOKEN == 'ваш_токен_здесь':
        logger.error("❌ Токен не установлен! Установи BOT_TOKEN в config.py или переменную окружения")
        print("\n⚠️  Инструкция:")
        print("1. Укажи токен в файле config.py")
        print("2. Или установи переменную окружения: export BOT_TOKEN='твой_токен'")
        return

    logger.info("🚀 Запуск бота для знакомств...")

    # Инициализируем бота
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем обработчики
    handlers = DatingBotHandlers(dp, bot)
    logger.info("✅ Обработчики зарегистрированы")

    # Запускаем long polling
    logger.info("👂 Бот слушает входящие сообщения...")
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("❌ Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)


if __name__ == '__main__':
    print("""
╔════════════════════════════════════════╗
║   💕 БОТ ДЛЯ ЗНАКОМСТВ - DATING BOT    ║
║          Версия 1.0                    ║
║          Платформа: MAX                ║
╚════════════════════════════════════════╝
    """)

    asyncio.run(main())
