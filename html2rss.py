#!/usr/bin/env python3
import re
import sys
from os.path import dirname, join
from json import JSONDecoder
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from lxml import etree as ET
from lxml.builder import E


def load_rules():
    with open(join(dirname(__file__), 'rules.json')) as f:
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
        soup = self._get_soup(self.url)
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
        return BeautifulSoup(response.text, 'lxml')

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
        for tag in soup.find_all(sel['tag'], attrs=sel.get('attrs', {})):
            ls = []
            for k, sel in rule.items():
                tag2 = tag.find(sel['tag'], attrs=sel.get('attrs', {}))
                # todo rewrite?
                if k == 'link':
                    href = tag2.find('a')['href']
                    text = '{uri.scheme}://{uri.netloc}{href}'.format(uri=self.parsed_uri, href=href)
                    ls.append(E.guid(text))  # todo?
                elif k == 'description':
                    text = tag2.__unicode__()
                else:
                    text = tag2.text.strip()
                ls.append(E.__getattr__(k)(text))
            result.append(E.item(*ls))
        return result


if __name__ == '__main__':
    print(Parser(sys.argv[1]).to_rss())
