# strings we're expecting to near author's name
import re

# tags we're consider as a good home for an author
import sys
from helper import get_around_words

TAGS = ['a', 'span', 'div', 'h3', 'h4', 'b', 'strong', 'i', 'p', 'li']

# strings we're expecting in element's attributes
ATTR_WORDS = ['author', 'name', 'person', 'byline'] #'writer',
ATTR_NAMES = ['id', 'class', 'rel', 'href', 'itemprop', 'title', 'data-author']

# all combinations (tuples) of pairs of ATTR_WORDS and ATTR_NAMES
ATTRIBUTES = []
for word in ATTR_WORDS:
    for name in ATTR_NAMES:
        ATTRIBUTES.append((name, word))

HEADER_TAGS = ['h1', 'h2', 'h3', 'header']
HEADER_RE = []
for tag in HEADER_TAGS:
    p = re.compile('<%s' % tag)
    HEADER_RE.append(p)


class Candidate:
    def __init__(self, el, dom, text, body_text, title_idx):
        self.dom = dom # reference to the dom instance
        self.el = el # reference to the Node instance the word(s) were found in
        self.text = text
        self.text_lower = text.lower()
        self.words = text.split(' ')
        self.body_text = body_text
        self.title_idx = title_idx

        # initialize features
        self.tag_name = ''  # containing element tag name
        self.is_capitalized = 0  # is first word capitalized
        self.all_capital = 0  # are all words capitalized
        self.dist_title = -1  # distance to title text
        self.attributes = []  # indicates that ith pair of attribute/value from ATTRIBUTES is present
        self.has_date = 0  # indicates that there is some date nearby (radius 10 words)
        self.has_time = 0  # indicates that there is some time nearby

    def get_features(self):
        return [self.has_date, self.has_time, self.is_capitalized, self.all_capital, self.dist_title, self.tag_name] + self.attributes

    @classmethod
    def get_labels(cls):
        labels = []
        labels.extend(['Has Date Around', 'Has Time Around', 'Is Capitalized', 'All Capitalized', 'Distance to Title', 'Tag Name'])
        for attr in ATTRIBUTES:
            labels.append('Attribute "%s" has value "%s"' % attr)
        return labels

    def __str__(self):
        nonempty = [pair for i, pair in enumerate(ATTRIBUTES) if self.attributes[i] == 1]
        return 'Candidate: %s\n\tAuthor attr: %s\n\tTitle dist: %s\n\tHas date: %s\n\tHas time: %s\n' % \
               (self.text, '\n'.join(['%s: %s' % (attr, value) for attr, value in nonempty]),
                self.dist_title, self.has_date, self.has_time)

    def has_attribute_value(self, attr):
        attr_name, attr_value = attr
        attributes = self.el.attributes
        return attr in attributes and attributes[attr].find(attr_value) > -1

    def get_distance_to_title(self, el):
        dist = sys.maxint # distance to title
        author_idx = self.body_text.find(self.text)
        if author_idx > -1:
            for tidx in self.title_idx:
                dist = min(dist, abs(author_idx - tidx))
        return dist

    def calculate_features(self):
        self.tag_name = self.el.tag.lower()

        self.dist_title = self.get_distance_to_title(self.el)

        before, after = get_around_words(self.el, self.text_lower)

        self.has_date = 1 if 'DATE' in before or 'DATE' in after else 0
        self.has_time = 1 if 'TIME' in before or 'TIME' in after else 0

        self.is_capitalized = 1
        for word in self.words:
            if word[0].isupper() and (len(word) == 1 or not word[1].isupper()):
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

        # check for presence of values in some attributes
        for attr in ATTRIBUTES:
            has_attr_value = self.has_attribute_value(attr)
            self.attributes.append(1 if has_attr_value else 0)