#!/usr/bin/env python3
import re
import sys
import logging
import email.utils
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markupsafe import Markup

from config import Config

log = logging.getLogger(__name__)


def http_parser(url, rules):
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'lxml')
    for i in soup.select(rules['selector']):
        sel_link = rules['link']
        url2 = i.select(sel_link)[0]['href']
        title = i.select(rules.get('title', sel_link))[0].text.strip()

        f = rules.getint('title.filter')
        if f:
            ls = re.findall(r'(\d+)', title)
            log.debug('%s | %s', ls, title)
            if ls and int(ls[0]) <= f:
                continue

        yield Markup('''\
<link>{uri.scheme}://{uri.netloc}{uri2.path}</link>
<guid>{uri.scheme}://{uri.netloc}{uri2.path}</guid>
<title>{title}</title>
<description>{text}</description>''').format(
            uri=urlparse(url),
            uri2=urlparse(url2),
            title=title,
            text=i.select(rules.get('text', sel_link))[0])


def vk_api(url, rules):
    from vk_api import API
    domain = urlparse(url).path.strip('/')
    log.debug('domain=%s', domain)
    api = API()
    r = api.wall_get(domain=domain)
    for i in r['items']:
        yield Markup('''\
<link>https://vk.com/wall{i[owner_id]}_{i[id]}</link>
<guid>https://vk.com/wall{i[owner_id]}_{i[id]}</guid>
<title>#{i[id]}</title>
<description>{text}</description>
<pubDate>{date}</pubDate>''').format(
            i=i,
            text=i['text'].replace('\n', '<br>'),
            date=email.utils.format_datetime(datetime.fromtimestamp(i['date'])))  # todo tz


sources = {
    'vk_api': vk_api,
    'http_parser': http_parser,
}


def main(*urls):
    config = Config('config.ini')
    result = []
    for url in urls:
        rules = config.get_config(url)
        func = sources[rules['source']]
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
