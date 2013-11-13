import os
from pattern.web import Text, plaintext, collapse_linebreaks, collapse_tabs, collapse_spaces
import re


def cleanup(str, remove_punctuation=True):
    if remove_punctuation:
        str = re.sub('[^A-Za-z0-9\s\n]+', '', str)
    str = collapse_linebreaks(str, threshold=1).replace('\n', ' ')
    str = collapse_tabs(str, indentation=False, replace=' ')
    str = collapse_spaces(str, indentation=False, replace=' ')
    return str.strip()


def get_surroundings_with_radius(str, cut_radius):
    if not str:
        return ''
    str = str.split(' ')
    str = filter(len, str)
    str = cut_radius(str)
    return ' '.join(str)


def get_words_count(text):
    arr = text.split(' ')
    arr = filter(len, arr)
    return len(arr)


def get_context(el, text):
    if el is None:
        return []

    parent = el.parent
    context = text
    text_words = text.split(' ')
    context_len = len(text_words) + .0
    while parent is not None:
        norm_source = Helper.cleanup(parent.source, False)
        source = plaintext(norm_source, linebreaks=1).lower()
        if context_len / len(source.split(' ')) < 0.7 and Helper.get_words_count(source) >= 20:
            # extract string of total length 20 with center in position of text
            # and maximum raidus of 10 words
            source = Helper.cleanup(source)
            if (' ' + text_words[0] + ' ') not in (' ' + source + ' '):
                break
            context = source.split(' ')
            context = filter(lambda w: len(w) > 1, context)
            # look for previous source in order to avoid finding another mention of the author
            idx = context.index(text_words[0])
            before = context[max(idx-10, 0):idx]
            start_after = idx + len(text_words)
            after = context[start_after : start_after + 20-len(before)]
            context = '%s %s %s' % (' '.join(before), text, ' '.join(after))
            break
        if context != source:
            context = source.replace('\n', ' ')
        parent = parent.parent
    context = context.lower()
    # find the text
    idx = context.find(text)
    # split context
    before = context[:idx-1].strip()
    after = context[idx+len(text):].strip()
    before = before.split(' ')
    after = after.split(' ')
    return before, after


def get_words(el):
    if el is None:
        return []

    text = ''
    # get text from the node itself
    if issubclass(el.__class__, Text):
        text = el.source
    else: # get just text, ignore children's content
        for child in el.children:
            if issubclass(child.__class__, Text):
                text += ' ' + child.source.strip()

    text = cleanup(text).split(' ')

    return text


def get_biwords(words):
    biwords = []
    for i in range(len(words)-1):
        # if len(words[i]) > 1 and len(words[i+1]) > 1:
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
    try:
        start = etime()
        uri = URL(url)
        html = uri.download(cached=True)
    except Exception, e:
        print 'HTTP Error:' + str(e.message)
    end = etime()
    print 'Download html: %s' % str(end - start)

    return html

