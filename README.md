# DoneDeal Tracking Telegram Bot (ddbot)

**ddbot** — это телеграм-бот для отслеживания объявлений автомобилей на платформе DoneDeal.

## Установка

1. Клонируйте репозиторий:
    ```bash
    git clone https://github.com/qarasuv/ddbot.git
    cd ddbot
    python3 -m venv env
    source env/bin/activate
    pip install -r requirements.txt
    ```

3. Добавить файл setenv.sh и настроить файл `config.py` с вашим API-ключом Telegram.

4. Запустите бота:
    ```bash
    python bot.py
    ```

## Функционал

- Отслеживание всех автомобилей по заданным фильтрам на DoneDeal.
- Поиск аналогичных автомобилей для анализа средней рыночной цены.
- Уведомление в Telegram, если цена на авто ниже среднего рыночного значения.

## Стек технологий

- Python(aiogram, aiohttp, APScheduler, numpy)
- Docker

## Лицензия

Проект лицензирован под MIT License.
