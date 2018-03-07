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
        self.soup = BeautifulSoup(self._get_html(), 'lxml')

    def _get_rule(self):
        for expr, rule in self.rules:
            if expr.match(self.url):
                return rule
        raise Exception('Not found rule for url "%s"' % self.url)

    def _get_html(self):
        try:
            headers = {'User-Agent': self.rule['user_agent']}
        except KeyError:
            headers = None
        response = requests.get(self.url, headers=headers)
        response.raise_for_status()
        return response.text

    def to_rss(self):
        ls = self._get_items()
        ls.append(E.title(self.soup.title.string))
        ls.append(E.link(self.url))
        try:
            t = self.soup.find('meta', attrs={'name': 'description'})['content']
            ls.append(E.description(t))
        except TypeError:
            pass
        rss = E.rss(E.channel(*ls), version='2.0')
        return ET.tostring(rss, xml_declaration=True, encoding='utf-8').decode('utf-8')

    def _get_items(self):
        result = []
        parsed_uri = urlparse(self.url)
        p = self.rule['item'].pop('parent')
        for tag in self.soup.find_all(p['tag'], attrs=p.get('attrs', {})):
            ls = []
            for k, p in self.rule['item'].items():
                tag2 = tag.find(p['tag'], attrs=p.get('attrs', {}))
                # todo rewrite?
                if k == 'link':
                    href = tag2.find('a')['href']
                    text = '{uri.scheme}://{uri.netloc}{href}'.format(uri=parsed_uri, href=href)
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
