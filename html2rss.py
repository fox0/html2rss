#!/usr/bin/env python3
import os
import re
import sys
import logging
from json import JSONDecoder
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from lxml import etree as ET
from lxml.builder import E

log = logging.getLogger(__name__)


def load_rules():
    filename = os.path.join(os.path.dirname(__file__), 'rules.json')
    with open(filename) as f:
        d = JSONDecoder().decode(f.read())
    return list((re.compile(expr), rule) for expr, rule in d.items())


rules = load_rules()


def _get_rule(url):
    for expr, rule in rules:
        if expr.match(url):
            return rule
    raise Exception('Not found rule for url "%s"' % url)


class Parser(object):

    def __init__(self, url):
        self.url = url
        self.rule = _get_rule(url)

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
        response.raise_for_status()
        # return BeautifulSoup(response.text, 'lxml')  # глючит с https://pikabu.ru/@iLawyer
        return BeautifulSoup(response.text, 'html.parser')

    def _get_feed_info(self, soup):
        result = [E.title(soup.find('title').text), E.link(self.url)]
        t = soup.find('meta', attrs={'name': 'description'})
        if t:
            result.append(E.description(t['content']))
        return result

    def _get_items(self, soup):
        result = []
        queryset = self._find_all(soup, 'parent')
        if 'count' in self.rule:
            queryset = queryset[:self.rule['count']]
        for tag in queryset:
            ls = []
            href = self._find_all(tag, 'link')[0].find('a')['href']
            text = '{uri.scheme}://{uri.netloc}{uri2.path}'.format(uri=urlparse(self.url), uri2=urlparse(href))
            log.debug(text)
            ls.append(E.link(text))
            ls.append(E.guid(text))
            ls.append(E.title(self._find_all(tag, 'title' if 'title' in self.rule else 'link')[0].text.strip()))
            ls.append(E.description(self._find_all(tag, 'text')[0].__unicode__()))
            result.append(E.item(*ls))
        return result

    def _find_all(self, soup, sel):
        rule = self.rule[sel]
        result = soup.find_all(rule['tag'], attrs=rule.get('attrs', {}))
        if not result:
            log.warning('Not found tag "%s"', rule)
        return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) == 1:
        # sys.argv.append('http://medstories.net/')
        sys.argv.append('https://pikabu.ru/@iLawyer')
    sys.stdout.write(Parser(sys.argv[1]).to_rss())
