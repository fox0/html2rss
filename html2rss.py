#!/usr/bin/env python3
import re
import sys
from os.path import dirname, join
from json import JSONDecoder
import requests
from bs4 import BeautifulSoup
from lxml import etree as ET
from lxml.builder import E


def main(url='http://medstories.net/'):
    print(Parser(url).to_rss())


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
        rss = E.rss(
            E.channel(
                E.title(self.soup.title.string),
                E.link(self.url),
                E.description(self.soup.find('meta', attrs={'name': 'description'})['content']),
                *self._get_items()), version='2.0')
        return ET.tostring(rss, xml_declaration=True, encoding='utf-8').decode('utf-8')

    def _get_items(self):
        result = []
        for i in self.soup.select(self.rule['item']):
            result.append(E.item(
                E.description(i.__unicode__())
            ))
        # for i in self.soup.select(self.rule['parent']):
        #     ls = []
        #     for k in ('title',):
        #         try:
        #             selector = self.rule[k]
        #             a = i.select(selector)
        #             ls.append(a)
        #         except KeyError:
        #             pass
        #     result.append(E.item(*ls))
        return result


if __name__ == '__main__':
    main(*sys.argv[1:])
