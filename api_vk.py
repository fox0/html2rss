import requests
from private_settings import access_token as default_access_token


class API(object):
    def __init__(self, access_token=None, v='5.84'):
        self.access_token = access_token or default_access_token
        self.version_api = v
        # todo session

    def __getattr__(self, attr):
        url = 'https://api.vk.com/method/' + attr.replace('_', '.')

        def func(**kwargs):
            kwargs['access_token'] = self.access_token
            kwargs['v'] = self.version_api
            result = requests.post(url, kwargs).json()
            return result['response']

        self.__setattr__(attr, func)
        return func
