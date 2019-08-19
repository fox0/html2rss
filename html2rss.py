#!/usr/bin/env python3
import sys
import logging

from config import Config
import parsers


def main(*urls):
    config = Config('config.ini')
    result = []
    for url in urls:
        rules = config.get_config(url)
        func = getattr(parsers, rules['parser'])
        for i in func(url, rules):
            result.append(i)
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
    rrr = main(*sys.argv[1:])
    sys.stdout.write(rrr)
