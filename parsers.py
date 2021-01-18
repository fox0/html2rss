"""Различные парсеры сайтов"""
import logging
from urllib.parse import ParseResult

from markupsafe import Markup

log = logging.getLogger(__name__)


def vk(uri: ParseResult):
    """Парсер стен ВКонтакте"""
    from datetime import datetime
    import email.utils
    from vkapi import VkAPI

    domain = uri.path.strip('/')
    log.debug('domain=%s', domain)
    api = VkAPI()
    response = api.wall_get(domain=domain)
    result = []
    for i in response['items']:
        result.append(Markup('''\
<link>https://vk.com/wall{i[owner_id]}_{i[id]}</link>
<guid>https://vk.com/wall{i[owner_id]}_{i[id]}</guid>
<title>#{i[id]}</title>
<description>{text}</description>
<pubDate>{date}</pubDate>''').format(i=i,
                                     text=i['text'].replace('\n', '<br>'),
                                     date=email.utils.format_datetime(datetime.fromtimestamp(i['date']))))  # todo tz
    return result

# def http_simple(url: str, rules):
#     """
#     Простой http парсер
#
#     Пример конфига:
#         [ficbook.net/readfic]
#         parser = http_simple
#         selector = div.comment_message
#         reverse = yes (опционально)
#     """
#     soup = _get_soup(url)
#     config_selector = rules['selector']
#     result = []
#     for i in soup.select(config_selector):
#         result.append(Markup('<description>{text}</description>').format(text=i))
#     return result
#
#
# def http(url: str, rules):
#     soup = _get_soup(url)
#     config_selector = rules['selector']
#     config_link = rules['link']
#     config_title = rules.get('title', config_link)
#     config_title_filter = rules.getint('title.filter')
#     config_text = rules.get('text', config_link)
#
#     result = []
#     for i in soup.select(config_selector):
#         url2 = i.select(config_link)[0]['href']
#         title = i.select(config_title)[0].text.strip()
#
#         if config_title_filter:
#             ls = re.findall(r'(\d+)', title)
#             log.debug('%s | %s', ls, title)
#             if ls and int(ls[0]) <= config_title_filter:
#                 continue
#
#         result.append(Markup('''\
# <link>{uri.scheme}://{uri.netloc}{uri2.path}</link>
# <guid>{uri.scheme}://{uri.netloc}{uri2.path}</guid>
# <title>{title}</title>
# <description>{text}</description>''').format(uri=urlparse(url),
#                                              uri2=urlparse(url2),
#                                              title=title,
#                                              text=i.select(config_text)[0]))
#     return result
#
#
# def _get_soup(url: str):
#     import requests
#     from bs4 import BeautifulSoup
#     response = requests.get(url)
#     response.raise_for_status()
#     soup = BeautifulSoup(response.text, 'lxml')
#     return soup
