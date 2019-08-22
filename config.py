"""Обёртка над библиотечным парсером конфигов"""
import configparser
import logging
from urllib.parse import urlparse

log = logging.getLogger(__name__)


class Config:
    """Обёртка над библиотечным парсером конфигов"""
    __slots__ = ('config',)

    def __init__(self, filename):
        """
        :param filename:
        :type filename: str
        """
        self.config = configparser.ConfigParser()
        self.config.read(filename)

    def get_config(self, url):
        """
        :param url:
        :type url: str
        :return:
        :rtype:
        """
        uri = urlparse(url)
        log.debug('%s', uri)
        bits = uri.path.split('/')
        # todo join нескольких секций
        try:
            section = uri.netloc + '/'.join(bits)
            log.debug('%s', section)
            return self.config[section]
        except KeyError:
            pass

        for _ in range(len(bits) - 1):
            bits.pop()
            section = uri.netloc + '/'.join(bits)
            log.debug('%s', section)
            try:
                return self.config[section]
            except KeyError:
                pass
        try:
            return self.config[uri.netloc]
        except KeyError:
            raise ValueError('Unknown host "%s"' % uri.netloc)
