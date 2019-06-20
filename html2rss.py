#!/usr/bin/env python3
import configparser
import sys
import logging
import email.utils
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from rss import RSS, RSSItem

log = logging.getLogger(__name__)


class Parser(object):

    def __init__(self, url):
        self.url = url
        self.rule = _get_rule(url)

    # todo ... -> dict -> rss
    def to_rss(self):
        ls = []

        if 'paginator' in self.rule:
            for i in range(1, self.rule['paginator']['count'] + 1):
                url = '{url}?{name}={count}'.format(url=self.url, name=self.rule['paginator']['name'], count=i)
                soup = self._get_soup(url)
                ls.extend(self._get_items(soup))
        else:
            soup = self._get_soup(self.url)
            ls.extend(self._get_items(soup))
        ls.extend(self._get_feed_info(soup))

        rss = E.rss(E.channel(*ls), version='2.0')
        return ET.tostring(rss, xml_declaration=True, encoding='utf-8').decode('utf-8')

    def _get_soup(self, url):
        headers = None
        if self.rule.get('user_agent', False):
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru',
                'DNT': '1',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0',
            }
            log.debug(headers)
        response = requests.get(url, headers=headers)
        if self.rule.get('fix_encoding', False):
            response.encoding = response.apparent_encoding
        response.raise_for_status()
        return BeautifulSoup(response.text, self.rule.get('parser', 'lxml'))

    def _get_feed_info(self, soup):
        result = [E.title(soup.find('title').text), E.link(self.url)]
        t = soup.find('meta', attrs={'name': 'description'})
        if t:
            result.append(E.description(t['content']))
        return result

    def _get_items(self, soup):
        result = []
        queryset = self._find_all(soup, 'parent')
        if 'slice' in self.rule:
            begin = self.rule['slice'].get('begin', 0)
            end = self.rule['slice']['end']
            queryset = queryset[begin:end]
        name_title = 'title' if 'title' in self.rule else 'link'
        for tag in queryset:
            ls = []
            link = self._get_link(tag)
            ls.append(E.link(link))
            ls.append(E.guid(link))
            ls.append(E.title(self._find_all(tag, name_title)[0].text.strip()))
            if 'text' in self.rule:
                tag = self._find_all(tag, 'text')[0]
            ls.append(E.description(tag.__unicode__()))
            result.append(E.item(*ls))
        return result

    def _get_link(self, soup):
        rule = self.rule['link']
        tag = soup.find_all(rule['tag'], attrs=rule.get('attrs', {}))[0]
        if rule['tag'] != 'a':
            tag = tag.find('a')
        url = tag['href']
        result = '{uri.scheme}://{uri.netloc}{uri2.path}'.format(uri=urlparse(self.url), uri2=urlparse(url))
        log.debug(result)
        return result

    def _find_all(self, soup, sel):
        rule = self.rule[sel]
        result = soup.find_all(rule['tag'], attrs=rule.get('attrs', {}))
        if not result:
            log.warning('Not found tag "%s"', rule)
        return result


def vk_api(url):
    from vk_api import API
    domain = urlparse(url).path.strip('/')
    log.debug('domain=%s', domain)
    api = API()
    r = api.wall_get(domain=domain)
    for i in r['items']:
        yield RSSItem(
            link='https://vk.com/wall%d_%d' % (i['owner_id'], i['id']),
            title='#%d' % i['id'],
            description=i['text'].replace('\n', '<br>'),
            pub_date=email.utils.format_datetime(datetime.fromtimestamp(i['date'])),  # todo tz
        )
    raise StopIteration


def main(*urls):
    config = configparser.ConfigParser()
    config.read('config.ini')

    rss = RSS()
    for url in urls:
        host = urlparse(url).netloc
        log.debug('host=%s', host)
        if host not in config:
            log.error('')
            continue
        rules = config[host]
        func = globals()[rules['source']]
        for i in func(url):
            rss.append(i)
    return rss.tostring()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sys.stdout.write(main(*sys.argv[1:]))
