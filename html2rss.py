#!/usr/bin/env python3
import sys
from os.path import dirname, join
from xml.etree import cElementTree as et
from json import JSONDecoder
import requests
from htmldom import htmldom


def main(url):
    rules = load_rules()
    site = rules[url]  # TODO re
    try:
        headers = {'User-Agent': site['user_agent']}
    except KeyError:
        headers = None

    html = requests.get(url, headers=headers).text
    dom = htmldom.HtmlDom().createDom(html)
    context = {
        'link': url,
        'title': dom.find('title').text(),
    }

    item = site['item']
    if isinstance(item, str):
        items = [{'description': i.text().replace('\n', '<br>')} for i in dom.find(item)]
    else:
        raise NotImplementedError

    print('<?xml version="1.0" encoding="utf-8"?>')
    et.dump(generate_xml(context, items))
    sys.exit(0)


def load_rules():
    """
    item - обязательный параметр. Строка или словарь.
    user_agent - опционально
    """
    with open(join(dirname(__file__), 'rules.json')) as f:
        return JSONDecoder().decode(f.read())


def generate_xml(context, items):
    rss = et.Element('rss')
    channel = et.SubElement(rss, 'channel')
    _add_subelement(channel, context)
    for i in items:
        item = et.SubElement(channel, 'item')
        _add_subelement(item, i)
    return et.ElementTree(rss)


def _add_subelement(parent, d):
    for k, v in d.items():
        et.SubElement(parent, k).text = v


if __name__ == '__main__':
    # main('http://medstories.net/')
    main(sys.argv[1])
