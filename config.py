users = {}

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'user-agent': 'donedeal/1 CFNetwork/1410.0.3 Darwin/22.6.0',
    'platform': 'iOS',
    'brand': 'donedeal',
    'accept-language': 'en-GB,en;q=0.9',
    'accept-encoding': 'gzip, deflate, br'
}

BASE_URL = 'https://www.donedeal.ie'

default_params = {
    "sort": "publishDateDesc",
    "paging": {"pageSize": 40},
    "filters": [{"values": ["for-sale"], "name": "adType"}],
    "sections": ["cars"],
    "ranges": [{"to": "10000", "name": "price", "from": "300"}]}

start_message = "This is a DoneDeal tracking bot.\n\n" \
                "Start tracking - /run\n" \
                "Stop tracking - /stop\n"

DISCOUNTS = {
    1000: 0.60,
    2000: 0.50,
    3000: 0.40,
    4000: 0.35,
    10000: 0.30,
    20000: 0.45,
    100000: 0.50
}
