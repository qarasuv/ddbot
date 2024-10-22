import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from aiogram import Bot, Dispatcher, executor
from aiogram.types import Message
from loguru import logger

from config import users, start_message
from parser import main

bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()


@dp.message_handler(commands=['start'])
async def start(message: Message) -> None:
    user_id = message.chat.id
    if user_id not in users:
        users[user_id] = users[user_id] = {'state': 0, 'cache': []}
        logger.info(f"new user: {user_id}")
    await bot.send_message(1762285767, f"{message.from_user.id} {message.from_user.username}")
    await bot.send_message(user_id, start_message)


@dp.message_handler(commands=['run'])
async def run(message: Message) -> None:
    user_id = message.chat.id
    if user_id in users:
        if users[user_id]['state'] == 1:
            await bot.send_message(user_id, 'bot is running')

        if users[user_id]['state'] == 0:
            users[user_id]['state'] = 1
            scheduler.add_job(main, 'interval', args=(user_id, bot), id=f'{user_id}', seconds=10)
            logger.info(f"Bot started for user {user_id}")
            await bot.send_message(user_id, 'Go!')
    else:
        await bot.send_message(user_id, 'Please send the command /start first')


@dp.message_handler(commands=['stop'])
async def stop(message: Message) -> None:
    user_id = message.from_user.id
    if user_id in users and users[user_id]['state'] == 1:
        users[user_id]['state'] = 0
        users[user_id]['cache'] = []
        try:
            scheduler.remove_job(job_id=str(user_id))
        except JobLookupError as e:
            logger.exception(f"An error occurred for user {user_id}: {e}")
        logger.info(f"Bot stopped for user {user_id}")
        await bot.send_message(user_id, 'The bot is stopped')
    else:
        await bot.send_message(user_id, 'The bot was not run')


@dp.message_handler()
async def other_text(message: Message) -> None:
    await bot.send_message(message.from_user.id, 'Enter please command!')


if __name__ == '__main__':
    logger.add("debug.log",
               format="{time} {level} {message}",
               level="DEBUG",
               rotation="10 MB",
               compression="zip")
    scheduler.start()
    executor.start_polling(dp)
