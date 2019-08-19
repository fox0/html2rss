import re
import logging
from urllib.parse import urlparse

from markupsafe import Markup

log = logging.getLogger(__name__)


def http(url, rules):
    import requests
    from bs4 import BeautifulSoup

    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'lxml')

    if rules.get('link'):
        result = _http(soup, url, rules)
    else:
        result = []
        for i in soup.select(rules['selector']):
            result.append(Markup('<description>{text}</description>').format(text=i))
    log.debug('len=%d', len(result))
    return result


def _http(soup, url, rules):
    config_selector = rules['selector']
    config_link = rules.get('link')
    config_title = rules.get('title', config_link)
    config_title_filter = rules.getint('title.filter')
    config_text = rules.get('text', config_link)

    result = []
    for i in soup.select(config_selector):
        url2 = i.select(config_link)[0]['href']
        title = i.select(config_title)[0].text.strip()

        if config_title_filter:
            ls = re.findall(r'(\d+)', title)
            log.debug('%s | %s', ls, title)
            if ls and int(ls[0]) <= config_title_filter:
                continue

        result.append(Markup('''\
<link>{uri.scheme}://{uri.netloc}{uri2.path}</link>
<guid>{uri.scheme}://{uri.netloc}{uri2.path}</guid>
<title>{title}</title>
<description>{text}</description>''').format(
            uri=urlparse(url),
            uri2=urlparse(url2),
            title=title,
            text=i.select(config_text)[0]))
    return result


def vk(url, rules):
    from datetime import datetime
    import email.utils
    from vk_api import API

    domain = urlparse(url).path.strip('/')
    log.debug('domain=%s', domain)
    api = API()
    r = api.wall_get(domain=domain)
    result = []
    for i in r['items']:
        result.append(Markup('''\
<link>https://vk.com/wall{i[owner_id]}_{i[id]}</link>
<guid>https://vk.com/wall{i[owner_id]}_{i[id]}</guid>
<title>#{i[id]}</title>
<description>{text}</description>
<pubDate>{date}</pubDate>''').format(
            i=i,
            text=i['text'].replace('\n', '<br>'),
            date=email.utils.format_datetime(datetime.fromtimestamp(i['date']))))  # todo tz
    log.debug('len=%d', len(result))
    return result
