import requests

from config import BOT_TOKEN, ADMIN_ID


class TelegramClient:
    def __init__(self, token: str, base_url: str):
        self.token = token
        self.base_url = base_url

    def prepare_url(self, method: str):
        url = f'{self.base_url}/bot{self.token}/'
        if method is not None:
            url += method
        return url

    def post(self, method: str = None, params: dict = None, body: dict = None):
        url = self.prepare_url(method)
        response = requests.post(url, params=params, data=body)
        return response.json()


if __name__ == '__main__':
    telegram_client = TelegramClient(BOT_TOKEN, 'https://api.telegram.org')
    params = {'chat_id': ADMIN_ID, 'text': 'uwu'}
    print(telegram_client.post('SendMessage', params=params))
