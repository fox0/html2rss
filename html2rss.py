#!/usr/bin/env python3
import configparser
import re
import sys
import logging
import email.utils
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from markupsafe import Markup

log = logging.getLogger(__name__)


def http_parser(url, rules):
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'lxml')
    for i in soup.find_all(rules['tag']):
        url2 = i.find_all('a', attrs=_get_attrs(rules.get('link.attrs')))[0]['href']
        title = find_tag(i, rules, 'title').text.strip()
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
            text=find_tag(i, rules, 'text').__unicode__())


def find_tag(soup, rules, name):
    tag = rules.get(name + '.tag')
    attrs = rules.get(name + '.attrs')
    return soup.find_all(tag, attrs=_get_attrs(attrs))[0]


def _get_attrs(rule):
    """
    >>> _get_attrs('class=visit-link')
    {'class': 'visit-link'}
    """
    if rule is None:
        return {}
    r = {}
    for i in rule.split(' '):
        k, v = i.split('=')
        r[k] = v
    return r


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


def main(*urls):
    config = configparser.ConfigParser()
    config.read('config.ini')

    result = []
    for url in urls:
        host = urlparse(url).netloc
        log.debug('host=%s', host)
        if host not in config:
            log.error('invalid host %s', host)
            continue
        rules = config[host]
        func = {
            'vk_api': vk_api,
            'http_parser': http_parser,
        }[rules['source']]
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
