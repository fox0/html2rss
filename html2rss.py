#!/usr/bin/env python3
import configparser
import sys
import logging
import email.utils
from datetime import datetime
from urllib.parse import urlparse
from lxml import etree as ET
from lxml.builder import E

import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def http_parser(url, rules):
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'lxml')
    for i in soup.find_all(rules['tag']):
        url2 = i.find_all('a', attrs=_get_attrs(rules.get('link.attrs')))[0]['href']
        link = '{uri.scheme}://{uri.netloc}{uri2.path}'.format(uri=urlparse(url), uri2=urlparse(url2))
        yield E.item(
            E.link(link),
            E.guid(link),
            E.title(i.find_all(rules.get('title.tag'), attrs=_get_attrs(rules.get('title.tag.attrs')))[0].text.strip()),
            E.description(i.find_all(rules.get('text.tag'), attrs=_get_attrs(rules.get('text.attrs')))[0].__unicode__())
        )


def _get_attrs(rule):
    """
    >>>_get_attrs('class=visit-link')
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
        link = 'https://vk.com/wall%d_%d' % (i['owner_id'], i['id'])
        yield E.item(
            E.link(link),
            E.guid(link),
            E.title('#%d' % i['id']),
            E.description(i['text'].replace('\n', '<br>')),
            E.pubDate(email.utils.format_datetime(datetime.fromtimestamp(i['date']))),  # todo tz
        )


def main(*urls):
    config = configparser.ConfigParser()
    config.read('config.ini')

    result = [E.link(urls[0])]
    for url in urls:
        host = urlparse(url).netloc
        log.debug('host=%s', host)
        if host not in config:
            log.error('invalid host %s', host)
            continue
        rules = config[host]
        func = globals()[rules['source']]
        for i in func(url, rules):
            result.append(i)
    rss = E.rss(E.channel(*result), version='2.0')
    return ET.tostring(rss, xml_declaration=True, encoding='utf-8').decode('utf-8')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sys.stdout.write(main(*sys.argv[1:]))
