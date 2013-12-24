import re
from pattern.text import ngrams
from pattern.web import Text, plaintext, DOM
from candidate import TAGS, Candidate
from helper import get_words


class FeatureExtractor(object):

    def get_title_index(self, dom, plain_text):
        title_el = dom('title')
        if title_el:
            # get title text
            title = plaintext(title_el[0].source)
            # usually title in <title> tag is a little bit different from
            # acutal article title - publishers tend to add website name or author name either to the
            # end or to the beginning of the title, for example:
            #
            # Insurers: Despite deadline, Obamacare glitches persist - CNN.com
            # India's Dating Sites Skip Straight to the Wedding - P. Nash Jenkins - The Atlantic
            #
            # But it will be separated by either : or -, so let's take substring
            # two first such separators
            title_parts = re.split('\:|\-|\|', title)
            # find title in tagless text
            # part_idx = 1 if len(title_parts) > 2 else 0
            part_idx = 0
            part_len = len(title_parts[0])
            for idx, part in enumerate(title_parts):
                if len(part) > part_len:
                    part_idx = idx
                    part_len = len(part)
            title_idx = [m.start() for m in re.finditer(title_parts[part_idx].strip(), plain_text)]
            return title_idx
        return []

    def get_candidates(self, html):
        dom = DOM(html)
        if not dom.body:
            return []

        # feature: text length
        # filter out long blocks of text
        plain_text = plaintext(dom.body.source, keep=TAGS)
        title_idx = self.get_title_index(dom, plain_text)

        candidates = []
        for tag in TAGS:
            elements = self.get_elements_with_short_text(dom, tag, plain_text, title_idx)
            for el in elements:
                # looking for username
                words = get_words(el)
                # generate bi- and tri-grams
                text = ' '.join(words)
                bigrams = ngrams(text, 2)
                trigrams = ngrams(text, 3)
                for t in (bigrams+trigrams):
                    s = ' '.join(t)
                    candidates.append(Candidate(el, dom, s, plain_text, title_idx))
        print 'Candidates found %s' % len(candidates)
        return candidates

    def get_distance_to_title(self, tag_name, text, plain_text, title_idx):
        idx = plain_text.find(text)
        dist = []
        if idx > -1:
            for tidx in title_idx:
                dist.append(abs(idx - tidx))
        return dist

    def get_elements_with_short_text(self, dom, tag_name, plain_text, title_idx):
        """
        Get all potential candidates elements by tagName. Filter out elements with
        more than 9 words and with distance to title more than 300 characters
        """
        elements = []
        for el in dom.by_tag(tag_name):
            l = 0
            el_plain_text = plaintext(el.source, keep=TAGS)
            title_dist = self.get_distance_to_title(tag_name,
                                                    el_plain_text,
                                                    plain_text, title_idx)
            is_valid = False
            for tdist in title_dist:
                if tdist < 300 and len(el_plain_text) < 300:
                    is_valid = True
                    break
            if not is_valid:
                continue
            for child in el.children:
                if issubclass(child.__class__, Text):
                    l += len(filter(len, child.source.strip().split(' ')))
                    if l > 9 or l == 0:
                        break
            if l <= 9:
                elements.append(el)
        return elements
