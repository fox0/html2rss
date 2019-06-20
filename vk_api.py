import requests

try:
    from private_settings import DEFAULT_ACCESS_TOKEN
except ImportError:
    DEFAULT_ACCESS_TOKEN = ''


class API(object):
    def __init__(self):
        self.access_token = DEFAULT_ACCESS_TOKEN
        self._s = requests.Session()

    def __getattr__(self, attr):
        url = 'https://api.vk.com/method/' + attr.replace('_', '.')

        def func(**kwargs):
            kwargs['access_token'] = self.access_token
            kwargs['v'] = '5.84'
            result = self._s.post(url, kwargs).json()
            return result['response']

        self.__setattr__(attr, func)
        return func
