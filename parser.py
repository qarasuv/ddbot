import json
import os
import re
from typing import Union
from urllib.parse import urljoin, urlencode
from aiohttp import client_exceptions

import numpy as np
import aiohttp
from aiogram import types
from loguru import logger

from config import users, default_params, headers, DISCOUNTS, BASE_URL


async def check_mileage(mileage: str) -> bool:
    if mileage:
        mileage_int = int(mileage[:-3].replace(',', ''))
        return mileage[-2:] == 'km' and mileage_int <= 250000 or mileage[-2:] == 'mi' and mileage_int <= 150000
    return True


async def check_country(country: str) -> bool:
    return country == 'Ireland' or not country


async def check_owners(owners: str) -> bool:
    return owners == '' or (owners and int(owners) <= 5)


async def clear_cache(user_id: int) -> None:
    cache = users[user_id]['cache']
    if len(cache) > 40:
        cache.pop(0)


async def get_prices(car: dict, page_size: int = 40) -> list:
    try:
        car_params = await get_params(car, page_size)
        cars = await get_cars(car_params)
        prices = []
        total_ads = int(cars['paging']['totalResults'])
        for i in cars['ads']:
            if i['currency'] == 'EUR':
                prices.append(int(i['price'].replace(',', '')))

        if total_ads - page_size <= 1:
            return sorted(prices)
        return sorted(prices + await get_prices(car, page_size + 40))
    except Exception as e:
        logger.error(f"{e} total_ads: {total_ads} page: {page_size} car: {car} car_params: {car_params}")


async def get_params(car: dict, page_size: int) -> dict:
    sections = ["cars"]
    filters = [{"name": "adType", "values": ["for-sale"]}]
    ranges = [{"to": car["year"], "from": car["year"], "name": "year"}, {"name": "price", "from": "300"}]
    paging = {"pageSize": 40}
    if page_size > 40:
        paging["from"] = page_size - 40

    sort = "bestMatch"
    make_model = [{"model": car["model"], "make": car["make"]}]

    if car["fuelType"]:
        filters.append({"values": [car["fuelType"]], "name": "fuelType"})
    if car["transmission"]:
        filters.append({"values": [car["transmission"]], "name": "transmission"})

    if car.get("engine"):
        match1 = re.search(r'\d+\.\d\s', car['engine'])
        match2 = re.search(r'\d+\.\d{2,}', car['engine'])
        if match1:
            number = float(match1.group())
            engine = int(number * 1000)
            ranges.append({"name": "engine", "from": engine, "to": engine})
        if match2:
            number = float(match2.group())
            engine = int(round(number, 1) * 1000)
            ranges.append({"name": "engine", "from": engine - 100, "to": engine})

    car_params = {"sections": sections, "filters": filters, "ranges": ranges, "paging": paging, "sort": sort,
                  "makeModelFilters": make_model}
    return car_params


async def get_cars(car_params: dict = None) -> Union[list, dict]:
    try:
        async with aiohttp.ClientSession() as session:
            if car_params:
                async with session.post(os.getenv('URI'),
                                        data=json.dumps(car_params),
                                        headers=headers,
                                        ssl=False) as resp:
                    return await resp.json()

            async with session.post(os.getenv('URI'),
                                    data=json.dumps(default_params),
                                    headers=headers,
                                    ssl=False) as resp:
                return (await resp.json())['ads']
    except aiohttp.client_exceptions.ClientConnectorError as e:
        logger.error(e)
        return []


async def filter_newest_cars(newest_cars: list) -> list:
    newest_filtered_cars = []
    for car in newest_cars:
        if car['age'] == '0 min' and car['currency'] == 'EUR' and car['price'] != '1,234':  # todo 12,345
            info = {}
            for i in car['displayAttributes']:
                info[i['name']] = i['value']

            if await check_mileage(info['mileage']) and await check_country(info['country']) and await check_owners(
                    info['owners']):
                info['id'] = car['id']
                info['price'] = int(car['price'].replace(',', ''))
                info['ads_url'] = car['friendlyUrl']
                info['header'] = car['header']
                info['location'] = f"{car['county']} {car['countyTown']}" if 'countyTown' in car else f"{car['county']}"
                info['dd_link'] = await get_dd_link(info) if info['make'] and info['model'] and info['year'] else None
                newest_filtered_cars.append(info)
    return newest_filtered_cars


async def get_dd_link(car: dict) -> str:
    make = car['make']
    model = car['model']
    year = car['year']
    url = f"{BASE_URL}/cars/{make}/{model}/{year}"

    param = {'fuelType': car.get('fuelType', None), 'transmission': car.get('transmission', None), 'price_from': '300'}

    if car.get("engine"):
        match1 = re.search(r'\d+\.\d\s', car['engine'])
        match2 = re.search(r'\d+\.\d{2,}', car['engine'])
        if match1:
            number = float(match1.group())
            engine = int(number * 1000)
            param['engine_from'] = engine
            param['engine_to'] = engine
        if match2:
            number = float(match2.group())
            engine = int(round(number, 1) * 1000)
            param['engine_from'] = engine - 100
            param['engine_to'] = engine

    filtered_params = {key: value for key, value in param.items() if value}
    url_with_params = urljoin(url, "?" + urlencode(filtered_params, doseq=True))

    return url_with_params


async def send_car_in_chat(user_id: int, car: dict, bot) -> None:
    engine = car.get('engine', "")
    dd_link = car['dd_link'] if car['dd_link'] else f"{BASE_URL}/cars?sort=publishdatedesc"
    message = (
        f"{car['header']}\n\n"
        f"💶 €{car['price']}\n\n"
        f"📅 {car['year']}\n"
        f"🕹️ {car['transmission']}\n"
        f"⛽ {engine}\n"
        f"📟 {car['mileage']}\n"
        f"👤 {car['owners']}\n"
        f"📍 {car['location']}\n"
        f"🅓 [DoneDeal]({dd_link})\n\n"
        f"{car['ads_url']}\n"
    )
    await bot.send_message(os.getenv('CHAT_ID'), message, parse_mode=types.ParseMode.MARKDOWN)


async def remove_outliers(prices: list) -> list:
    lower_quartile = np.percentile(prices, 25)
    upper_quartile = np.percentile(prices, 75)

    iqr = upper_quartile - lower_quartile

    lower_whisker = lower_quartile - 1.5 * iqr
    upper_whisker = upper_quartile + 1.5 * iqr

    prices_without_outliers = [price for price in prices if lower_whisker <= price <= upper_whisker]

    return prices_without_outliers


async def main(user_id: int, bot) -> None:
    try:
        newest_cars = await get_cars()
        newest_filtered_cars = await filter_newest_cars(newest_cars)

        for car in newest_filtered_cars:
            if car['id'] not in users[user_id]['cache']:
                users[user_id]['cache'].append(car['id'])
                await clear_cache(user_id)
                if car['make'] and car['model'] and car['year']:
                    prices = await get_prices(car)
                    if len(prices) == 1:
                        await send_car_in_chat(user_id, car, bot)
                    else:
                        clean_list = await remove_outliers(prices)
                        avg = int(sum(clean_list) / len(clean_list))

                        for price_limit, discount in DISCOUNTS.items():
                            if avg <= price_limit:
                                my_price = int(avg * (1 - discount))
                                if car['price'] <= my_price:
                                    await send_car_in_chat(user_id, car, bot)
                                break
                else:
                    await send_car_in_chat(user_id, car, bot)
    except Exception as e:
        logger.error(e)
