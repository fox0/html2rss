import configparser
import logging
from urllib.parse import urlparse

log = logging.getLogger(__name__)


class Config:
    def __init__(self, filename):
        self.config = configparser.ConfigParser()
        self.config.read(filename)

    def get_config(self, url):
        uri = urlparse(url)
        log.debug('%s', uri)
        bits = uri.path.split('/')
        # todo join нескольких секций
        try:
            s = uri.netloc + '/'.join(bits)
            log.debug('%s', s)
            return self.config[s]
        except KeyError:
            pass

        for _ in range(len(bits) - 1):
            bits.pop()
            s = uri.netloc + '/'.join(bits)
            log.debug('%s', s)
            try:
                return self.config[s]
            except KeyError:
                pass
        try:
            return self.config[uri.netloc]
        except KeyError:
            raise ValueError('Unknown host "%s"' % uri.netloc)
