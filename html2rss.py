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
    with open(filename) as f:  # todo cssselect?
        d = JSONDecoder().decode(f.read())
    return list((re.compile(expr), rule) for expr, rule in d.items())


class Parser(object):
    rules = load_rules()

    def __init__(self, url):
        self.url = url
        self.rule = self._get_rule()
        self.parsed_uri = urlparse(self.url)

    def _get_rule(self):
        for expr, rule in self.rules:
            if expr.match(self.url):
                return rule
        raise Exception('Not found rule for url "%s"' % self.url)

    def to_rss(self):
        ls = []
        soup = self._get_soup(self.url)  # (!)
        ls.extend(self._get_feed_info(soup))
        ls.extend(self._get_items(soup))  # first page

        paginator = self.rule.get('paginator')
        if paginator:
            for i in range(2, paginator['count'] + 1):
                url = '{url}?{name}={count}'.format(url=self.url, name=paginator['name'], count=i)  # todo
                soup = self._get_soup(url)
                ls.extend(self._get_items(soup))

        rss = E.rss(E.channel(*ls), version='2.0')
        return ET.tostring(rss, xml_declaration=True, encoding='utf-8').decode('utf-8')

    def _get_soup(self, url):
        try:
            headers = {'User-Agent': self.rule['user_agent']}
        except KeyError:
            headers = None
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
        rule = self.rule['item'].copy()
        sel = rule.pop('parent')
        queryset = soup.find_all(sel['tag'], attrs=sel.get('attrs', {}))
        if not queryset:
            log.error('Not found parent tag "%s"', sel)
        for tag in queryset:
            ls = []
            for k, sel in rule.items():
                tag2 = tag.find(sel['tag'], attrs=sel.get('attrs', {}))
                if not tag2:
                    log.warning('Not found tag "%s". Ignore it.', sel)
                    continue
                if k == 'link':
                    href = tag2.find('a')['href']
                    if not href:
                        log.warning('Not found link')
                    uri2 = urlparse(href)
                    log.debug(uri2)
                    text = '{uri.scheme}://{uri.netloc}{uri2.path}'.format(uri=self.parsed_uri, uri2=uri2)
                    ls.append(E.guid(text))
                    log.debug(text)
                elif k == 'description':
                    text = tag2.__unicode__()
                else:
                    text = tag2.text.strip()
                ls.append(E.__getattr__(k)(text))
            result.append(E.item(*ls))
        return result


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) == 1:
        # sys.argv.append('http://medstories.net/')
        sys.argv.append('https://pikabu.ru/@iLawyer')
    print(Parser(sys.argv[1]).to_rss())
