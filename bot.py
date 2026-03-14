import os
import asyncio
import logging

import django
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.exceptions import TelegramAPIError

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'garant.settings')
django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
WEBAPP_URL = os.getenv('WEBAPP_URL', '')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Dictionary to store last message IDs per user (user_id: {user_msg_id, bot_msg_id})
last_messages = {}


def get_webapp_url():
    if WEBAPP_URL:
        return WEBAPP_URL
    return WEBAPP_URL


def get_webapp_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Kirish",
            web_app=WebAppInfo(url=get_webapp_url())
        )],
    ])
    
    return keyboard


async def delete_old_messages(user_id: int, chat_id: int):
    """Delete previous messages from chat, keeping only the last exchange"""
    if user_id in last_messages:
        user_msg_id = last_messages[user_id].get('user_msg_id')
        bot_msg_id = last_messages[user_id].get('bot_msg_id')

        if user_msg_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=user_msg_id)
            except TelegramAPIError as e:
                logger.debug("Could not delete user message %s: %s", user_msg_id, e)

        if bot_msg_id:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=bot_msg_id)
            except TelegramAPIError as e:
                logger.debug("Could not delete bot message %s: %s", bot_msg_id, e)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    telegram_id = message.from_user.id
    chat_id = message.chat.id
    text = (
        "⬇️ Kirish uchun tugmani bosing"
    )

    if telegram_id not in last_messages:
        last_messages[telegram_id] = {}
    old_user_msg_id = last_messages[telegram_id].get('user_msg_id')
    old_bot_msg_id = last_messages[telegram_id].get('bot_msg_id')
    last_messages[telegram_id]['user_msg_id'] = message.message_id

    sent_message = await message.answer(text, reply_markup=get_webapp_keyboard())
    last_messages[telegram_id]['bot_msg_id'] = sent_message.message_id

    if old_user_msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=old_user_msg_id)
        except TelegramAPIError as e:
            logger.debug("Could not delete user message %s: %s", old_user_msg_id, e)

    if old_bot_msg_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=old_bot_msg_id)
        except TelegramAPIError as e:
            logger.debug("Could not delete bot message %s: %s", old_bot_msg_id, e)


@dp.message()
async def handle_any(message: Message):
    await cmd_start(message)


async def main():
    logger.info("Starting Garant Bot...")
    logger.info(f"Bot token: {BOT_TOKEN[:10]}...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Garant Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running garant bot: {e}")