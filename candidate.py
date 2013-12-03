# strings we're expecting to near author's name
import os
from pattern.web import plaintext
import re

# tags we're consider as a good home for an author
from helper import get_context

TAGS = ['a', 'span', 'div', 'h3', 'h4', 'b', 'strong', 'i', 'p', 'li']

BEFORE = ['posted', 'by', 'author', 'and', '&', 'from']
AFTER = ['on', 'today', 'yesterday' 'hours', 'minutes', 'posted', 'updated', #'is',
         '&amp;', 'and', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat',
         'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday',
         'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
         'January', 'February', 'March', 'April', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
         #'author', 'writer', 'expert', 'columnist'

# strings we're expecting in element's attributes
ATTR_WORDS = ['author', 'name', 'person', 'byline'] #'writer',
ATTR_NAMES = ['id', 'class', 'rel', 'href', 'itemprop', 'title', 'data-author']

STOP_WORDS = ['a', 'the', 'article', 'in', 'or', 'to', 'this', 'that', 'those', 'these', 'are', 'who', 'which', 'why', 'when', 'what', 'of', '&lt;', '&gt;', ',', ':', '&nbsp;', '&amp;', 'us', 'with', 'for', 'get', 'with', '#', '%']
STOP_WORDS += BEFORE + AFTER
STOP_WORDS = set(STOP_WORDS)

HEADER_TAGS = ['h1', 'h2', 'h3', 'header']
HEADER_RE = []
for tag in HEADER_TAGS:
    p = re.compile('<%s' % tag)
    HEADER_RE.append(p)


def etime():
    """See how much user and system time this process has used so far and return the sum."""
    user, sys, chuser, chsys, real = os.times()
    return user+sys



class Candidate:
    text = '' # text we're considering as a author's name candidate
    location = 0
    tag_idx = 0
    author_attr = [] # ith element contains distance to ATTR_NAMES[i]. 0 - means in the same element
    words_before = [] # distance from candidate to i-th the word in BEFORE
    words_after = []
    is_capitalized = 0 # 0 or 1
    all_capital = 0 # 0 or 1
    words_count = 0
    has_image_around = 0 # 0 or 1
    header_dist = [] # distance to hx tag


    def __init__(self, el, dom, text, idx):
        self.dom = dom # reference to the dom instance
        self.el = el # reference to the Node instance the word(s) were found in
        self.text = text
        self.text_lower = text.lower()
        self.words = text.split(' ')
        self.words = filter(lambda w: len(w) > 1, self.words)
        self.idx = idx # word index in the text (starts from 0)

    def get_features(self):
        # [self.location, self.tag_idx] +
        # , self.has_image_around
        return self.author_attr + self.header_dist + [self.is_capitalized, self.all_capital, self.words_count] + self.words_before + self.words_after

    def __str__(self):
        words_before = [BEFORE[i] for i in range(len(BEFORE)) if self.words_before[i] > -1]
        words_after = [AFTER[i] for i in range(len(AFTER)) if self.words_after[i] > -1]
        attr = [ATTR_NAMES[i] for i in range(len(ATTR_NAMES)) if self.author_attr[i] > -1]
        return 'Candidate: %s\n\tAuthor attr: %s\n\tHeader dist: %s\n\tWords before: %s\n\tWords after: %s\n' % \
               (self.text, ', '.join(attr), self.header_dist, ', '.join(words_before), ', '.join(words_after))

    def element_has_author(self, el):
        attributes = el.attributes
        indexes = []
        for attr in ATTR_NAMES:
            for word in ATTR_WORDS:
                if attr in attributes and attributes[attr].find(word) > -1:
                    indexes.append(ATTR_NAMES.index(attr))
        return indexes


    def get_author_attr(self):
        dist = [-1 for i in ATTR_NAMES]
        el = self.el
        depth = 0
        while depth < 4 and el is not None:
            indexes = self.element_has_author(el)
            for idx in indexes:
                if dist[idx] == -1:
                    dist[idx] = depth
            depth += 1
            el = el.parent
        return dist


    def get_horizontal_loc(self, el):
        prev = el
        loc = 0
        while prev.previous:
            loc += 1
            prev = prev.previous
        return loc


    def get_headers_dist(self, el):
        loc = 0
        parent = el
        dist = [-1 for i in HEADER_RE]
        depth = 6
        while parent.parent is not None and depth > 0:
            source = parent.source
            for i in range(len(HEADER_RE)):
                if dist[i] == -1 and HEADER_RE[i].search(source) is not None:
                    dist[i] = loc
            loc += 1
            depth -= 1
            parent = parent.parent
        return dist


    # todo: replace with distance to h1 tag or header tag
    def get_location(self, el, text):
        loc = 0
        parent = el
        text_len = len(text)
        while parent.parent is not None:
            source = plaintext(parent.source).strip()
            if text_len / len(source.split(' ')) < 0.7:
                break
            loc += 1
            parent = parent.parent
        return loc


    def find_words_before(self, before):
        dist = [-1 for i in BEFORE]
        before_len = len(before)
        for i in range(before_len):
            word = before[i]
            if word in BEFORE:
                dist[BEFORE.index(word)] = before_len - i
        return dist


    def find_words_after(self, after):
        dist = [-1 for i in AFTER]
        for i in range(len(after)):
            word = after[i]
            if word in AFTER:
                dist[AFTER.index(word)] = i
        return dist


    def calculate_features(self):
        self.location = 0 #self.get_location(self.el, self.text_lower) + .0
        self.tag_idx = TAGS.index(self.el.tag.lower())
        self.author_attr = self.get_author_attr()
        self.words_count = len(self.words)

        # check distance to Hx tags
        self.header_dist = self.get_headers_dist(self.el)

        before, after = get_context(self.el, self.text_lower)

        self.words_before = self.find_words_before(before)
        self.words_after = self.find_words_after(after)

        self.before = before
        self.after = after

        self.is_capitalized = 1
        for word in self.words:
            if word[0].isupper() and not word[1].isupper():
                continue
            else:
                self.is_capitalized = 0
        # check if all letters are in uppercase
        self.all_capital = 1
        if self.is_capitalized == 0:
            for word in self.words:
                if self.all_capital == 0:
                    break
                for c in word:
                    if not c.isupper():
                        self.all_capital = 0
                        break
