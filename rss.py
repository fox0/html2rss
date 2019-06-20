from lxml import etree as ET
from lxml.builder import E


class RSSItem:
    __slots__ = ('link', 'title', 'description', 'pub_date')

    def __init__(self, link, title, description, pub_date=None):
        self.link = link
        self.title = title
        self.description = description
        self.pub_date = pub_date

    def to_xml(self):
        item = E.item(E.link(self.link), E.guid(self.link), E.title(self.title), E.description(self.description))
        if self.pub_date:
            item.append(E.pubDate(self.pub_date))
        return item


class RSS:
    __slots__ = ('_ls',)

    def __init__(self):
        self._ls = []

    def append(self, i: RSSItem):
        self._ls.append(i)

    def tostring(self) -> str:
        ls = [i.to_xml() for i in self._ls]
        rss = E.rss(E.channel(*ls), version='2.0')
        return ET.tostring(rss, xml_declaration=True, encoding='utf-8').decode('utf-8')
