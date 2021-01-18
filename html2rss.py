#!/usr/bin/env python3
import sys
import logging
from urllib.parse import urlparse, ParseResult

import parsers

log = logging.getLogger(__name__)


def main(url):
    """Точка входа"""
    uri: ParseResult = urlparse(url)
    log.debug('%s', uri)
    if uri.netloc == 'vk.com':
        result = parsers.vk(uri)
    else:
        raise NotImplementedError

    # todo dict2xml

    return '''\
<?xml version='1.0' encoding='utf-8'?>
<rss version="2.0">
    <channel>
        <link>{link}</link>
        {items}
    </channel>
</rss>'''.format(link=url, items=''.join('<item>{}</item>'.format(i) for i in result))


if __name__ == '__main__':
    # logging.basicConfig(level=logging.INFO)
    logging.basicConfig(level=logging.DEBUG)
    sys.stdout.write(main(sys.argv[1]))
