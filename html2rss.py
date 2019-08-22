#!/usr/bin/env python3
"""html2rss"""
import sys
import logging

from config import Config
import parsers

log = logging.getLogger(__name__)


def main(*urls):
    """Точка входа"""
    config = Config('config.ini')
    result = []
    for url in urls:
        rules = config.get_config(url)
        func = getattr(parsers, rules['parser'])
        ls = func(url, rules)
        log.debug('len=%d', len(ls))
        if rules.getboolean('reverse'):
            ls.reverse()
        result.extend(ls)

    return '''\
<?xml version='1.0' encoding='utf-8'?>
<rss version="2.0">
    <channel>
        <link>{link}</link>
        <item>{items}</item>
    </channel>
</rss>'''.format(link=urls[0], items='</item>\n<item>'.join(result))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sys.stdout.write(main(*sys.argv[1:]))
