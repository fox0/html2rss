"""Враппер для VK_API"""
import requests

try:
    from private_settings import DEFAULT_ACCESS_TOKEN
except ImportError:
    DEFAULT_ACCESS_TOKEN = ''


class VkAPI:
    def __init__(self):
        self._access_token = DEFAULT_ACCESS_TOKEN
        self._session = requests.Session()

    def __getattr__(self, attr: str):
        url = 'https://api.vk.com/method/' + attr.replace('_', '.')

        def func(**kwargs) -> dict:
            kwargs['access_token'] = self._access_token
            kwargs['v'] = '5.84'
            result = self._session.post(url, kwargs).json()
            return result['response']

        self.__setattr__(attr, func)
        return func
