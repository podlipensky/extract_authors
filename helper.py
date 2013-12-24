import os
from pattern.web import plaintext, collapse_linebreaks, collapse_tabs, collapse_spaces, URL
import re

BEFORE = ['posted', 'by', 'author', 'and', '&', 'from']
AFTER = ['on', 'updated', '&amp;', 'is', 'and']
POINT_IN_TIME = ['hours', 'minutes', 'seconds']
DAY = ['days', 'today', 'yesterday', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat',
       'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
MONTH = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
         'January', 'February', 'March', 'April', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
         #'author', 'writer', 'expert', 'columnist'

TIME_RE = re.compile('\d{1,2}:\d{1,2}\s?[p|a]?\.?m?\.?\s', re.IGNORECASE)
POINT_IN_TIME_RE = re.compile('\d{1,2}\s(' + '|'.join(POINT_IN_TIME) + ')[,\s]{0,2}', re.IGNORECASE)
DATE_RE = re.compile('(' + '|'.join(MONTH) + ')[,\s]{0,2}(\d{1,2})?[,\s]{0,2}(\d{2,4})?\s', re.IGNORECASE)

STOP_WORDS = ['a', 'the', 'article', 'in', 'or', 'to', 'this', 'that', 'those', 'these', 'are', 'who', 'which', 'why', 'when', 'what', 'of', '&lt;', '&gt;', ',', ':', '&nbsp;', '&amp;', 'us', 'with', 'for', 'get', 'with', '#', '%']
STOP_WORDS += BEFORE + AFTER
STOP_WORDS = set(STOP_WORDS)


def cleanup(text, remove_punctuation=True):
    if remove_punctuation:
        text = re.sub('[^A-Za-z0-9\s\n]+', '', text)
    text = collapse_linebreaks(text, threshold=1).replace('\n', ' ')
    text = collapse_tabs(text, indentation=False, replace=' ')
    text = collapse_spaces(text, indentation=False, replace=' ')
    return text.strip()


def get_surroundings_with_radius(text, cut_radius):
    if not text:
        return ''
    text = text.split(' ')
    text = filter(len, text)
    text = cut_radius(text)
    return ' '.join(text)


def get_words_count(text):
    arr = text.split(' ')
    arr = filter(len, arr)
    return len(arr)


def get_words_before_after(norm_source, after, before, idx, text):
    prefix = norm_source[:idx]
    suffix = norm_source[idx + len(text):]
    before = prefix.split(' ')
    after = suffix.split(' ')
    return after, before


def get_around_words(el, text, count=10):
    if el is None:
        return []

    parent = el.parent
    before = []
    after = []
    max_depth = 10
    source = ''
    idx = -1
    while parent is not None and max_depth:
        source = plaintext(parent.source, linebreaks=1).lower().replace('\n', ' ')
        idx = source.find(text)
        after, before = get_words_before_after(source, after, before, idx, text)
        if len(before) >= count and len(after) >= count:
            break
        parent = parent.parent
        max_depth -= 1
    # substitute date and time with recognizable tokens
    norm_source = re.sub(TIME_RE, 'TIME ', source)
    norm_source = re.sub(POINT_IN_TIME_RE, 'TIME ', norm_source)
    norm_source = re.sub(DATE_RE, 'DATE ', norm_source)
    after, before = get_words_before_after(norm_source, after, before, idx, text)

    return before[-count:], after[:count]


def get_words(el):
    if el is None:
        return []

    text = plaintext(el.source)
    text = cleanup(text).split(' ')
    text = [word for word in text if word.lower().strip() not in STOP_WORDS]

    return text


def get_biwords(words):
    biwords = []
    for i in range(len(words)-1):
        biwords.append(words[i] + ' ' + words[i+1])
    return biwords


def etime():
    """See how much user and system time this process has used so far and return the sum."""
    user, sys, chuser, chsys, real = os.times()
    return user+sys


def read_file(filename):
    html = ''
    try:
        f = open(filename, 'r')
        html = f.readlines()
        html = ' '.join(html).replace('\\\\', '\\')
    except Exception, e:
        print 'File not found:' + str(e.message)

    return html


def read_web(url):
    html = ''
    start = etime()
    try:
        uri = URL(url)
        html = uri.download(cached=True)
    except Exception, e:
        print 'HTTP Error:' + str(e.message)
    end = etime()
    print 'Download html: %s' % str(end - start)

    return html

