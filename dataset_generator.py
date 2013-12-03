import re
from urlparse import urlparse

DEFAULT_URLS_PATH = './urls.txt'

class BaseAuthorExtractor():
    domain = ''
    selectors = []

    def __init__(self, domain=None, selector=None):
        if domain:
            self.domain = domain
        if selector:
            self.selectors = selector

    def get_parent(self, el):
        return el.parent

    def is_author(self, url, el, text):
        if urlparse(url).hostname != self.domain:
            return False
        for selector in self.selectors:
            elements = self.get_parent(el)(selector)
            if len(elements) and elements[0] == el:
                return self.compare_text(el, text)
        return False

    def compare_text(self, el, text):
        """
        For simplest use case element will contain only author name
        """
        return True


class UsaTodayExtractor(BaseAuthorExtractor):
    domain = 'www.usatoday.com'
    selectors = ['span[itemprop=name]']
    author_re = re.compile('\s?(?P<name>[^,]+)((, USA TODAY)|(, special for USA TODAY))')

    def compare_text(self, el, text):
        match = self.author_re.match(el.content)
        return match and match.group('name').strip().lower() == text.strip().lower()


class TheAtlanticExtractor(BaseAuthorExtractor):
    domain = 'www.theatlantic.com'
    selectors = ['a[rel=author]']

    def compare_text(self, el, text):
        if el.parent and el.parent.parent:
            return el.parent.parent.tagName == 'div' and  \
                   el.parent.parent.attr['class'] == 'metadata' and\
                   el.parent.parent.parent.tagName == 'article'
        return False


class CnnExtractor(BaseAuthorExtractor):
    domain = 'www.cnn.com'
    selectors = ['div.cnnByLine', 'div.cnnByLine>strong']
    author_re = re.compile('by (?P<first_name>\w+\s\w+)( and (?P<second_name>[^,]+),)|,')

    def get_parent(self, el):
        return el.parent.parent

    def compare_text(self, el, text):
        is_single = el.tagName == 'strong' and el.content.lower().strip() == text.lower()

        match = self.author_re.match(el.content.lower())
        is_multiple = match and (match.group('first_name').strip() == text.lower() or
            match.group('second_name').strip() == text.lower())

        return is_single or is_multiple


class SampleGenerator(object):

    AUTHOR_EXTRACTORS = [
        BaseAuthorExtractor(domain='venturebeat.com', selector='a[rel=author]'),
        BaseAuthorExtractor(domain='techcrunch.com', selector='a[rel=author]'),
        TheAtlanticExtractor(),
        UsaTodayExtractor(),
        CnnExtractor()
    ]

    def __init__(self, urls_path=DEFAULT_URLS_PATH):
        self.urls_path = urls_path

    def get_urls(self):
        f = open(self.urls_path)
        urls = []
        url = f.readline()
        while url:
            urls.append(url)
            url = f.readline()
        f.close()
        return urls

    def is_author(self, url, el, text):
        return any([extractor.is_author(url, el, text) for extractor in self.AUTHOR_EXTRACTORS])