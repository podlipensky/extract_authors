import numpy
from numpy import array, save, load
from optparse import OptionParser
from pprint import pprint
from sklearn import linear_model, svm
from sklearn.preprocessing import StandardScaler
from candidate import Candidate
from dataset_generator import SampleGenerator
from decision_tree import DecisionTree
from feature_extractor import FeatureExtractor
from helper import etime, read_web

"""
    This script's aim is to find author name of any arbitrary article based on
    training data (observed articles and authors). The main intuition here is that
    author's name will appear either at the beginning or at the end of the document.
    Also author's name usually surrounded by words like "Posted by" or article
    published date/time. Here is a full list of features used in the model:

    feature: document position (looking for beginning or end of the document)
    feature: css class, id like '%author%' or '%name%' or '%person%' in its attributes or closest three parents attributes
    feature: has words 'Posted by', 'by', 'author', 'and' before the name
    feature: has words 'on', 'today', 'hours', 'minutes', 'February', 'is', 'posted', ',', 'and' after the name
    feature: first letters of first/last name are capital
    feature: has image nearby (not implemented yet)
    feature: surrounded text density

    in order to get nearby words (context), we should go up to the nearest parent (recursively)
    and get plaintext on each step, once amount of text is increased:
    1. if this is first increase since we've got the element text -> continue if
       overall text length is less than 15 words. Otherwise use original element's text <--- Should we stop here?
    2. if this is n-th text increase, and total length is more than on 40% comparing to
       previous result - stop and use previous plaintext as a context.

    TODO: process meta tags
    <meta content="Nischelle Turner, CNN" itemprop="author" name="author"/>
    <meta name="author" content='Matt Asay' />
"""

class AuthorDetector():
    def __init__(self, feature_extractor, algo_cls):
        self.feature_extractor = feature_extractor
        self.algo_cls = algo_cls
        self.classifier = algo_cls()

    def train(self, sampler=None):
        if sampler:
            X = []
            y = []
            urls = sampler.get_urls()

            for url in urls:
                # calculate features, prepare for training/classification
                candidates = self.get_candidates(url)

                # transform dataset
                features = []
                authors = []
                is_author_found = False

                for candidate in candidates:
                    features.append(candidate.get_features())
                    # determine whether this is a true author or not
                    is_target = sampler.is_author(url, candidate.el, candidate.text)
                    is_author_found = is_author_found or is_target
                    authors.append(1 if is_target else 0)

                    if is_target:
                        print 'Candidate found: %s' % candidate.text
                        try:
                            print candidate
                        except UnicodeEncodeError:
                            pass
                        print

                if is_author_found:
                    X.extend(features)
                    y.extend(authors)

            data = (array(X), array(y))
            self.save(data)
        else:
            data = self.restore()

        start = etime()
        self.classifier.fit(*data)
        end = etime()
        print 'Train classifier %s' % str(end - start)

    def predict(self, url):
        # calculate features, prepare for training/classification
        candidates = self.get_candidates(url)
        X = []
        for candidate in candidates:
            # print candidate
            X.append(candidate.get_features())
        y = self.classifier.clf.predict(X)
        self.print_results(y, candidates)

    def print_results(self, y, candidates):
        for score, candidate in zip(y, candidates):
            if score > 0:
                pprint(candidate.text)

    def get_candidates(self, url):
        print
        print 'Working with: %s' % url

        start = etime()

        html = read_web(url)
        candidates = self.feature_extractor.get_candidates(html)

        end = etime()
        print 'Gather candidates time: %s' % str(end - start)

        start = etime()

        for candidate in candidates:
            candidate.calculate_features()

        end = etime()
        print 'Calculate features time: %s' % str(end - start)

        return candidates

    def save(self, data):
        Xa, ya = data
        save('sample', Xa)
        save('target', ya)

    def restore(self):
        X_str = load('sample.npy')
        y = load('target.npy')
        X = []
        for i, row in enumerate(X_str):
            t = []
            for j, val in enumerate(row):
                try:
                    t.append(numpy.float32(val))
                except ValueError:
                    t.append(val)
            X.append(t)
        return (X, y.astype(float))


class LogisticRegression():
    clf = linear_model.LogisticRegression(C=1.0, penalty='l1', tol=1e-6)

    def fit(self, X, y):
        X = StandardScaler().fit_transform(X)
        self.clf.fit(X, y)
        return y


class SVM():
    clf = svm.SVC(class_weight={1:3})
    def fit(self, X, y):
        self.clf.fit(X, y)
        return y


def get_algo_from_name(name):
    name_lower = name.lower()
    if (name_lower == 'lr'):
        return LogisticRegression
    if (name_lower == 'svm'):
        return SVM
    if (name_lower == 'decisiontree'):
        return DecisionTree


def __main__():
    parser = OptionParser()
    parser.add_option("-t", "--train", dest="train",
                  help="write report to FILE", metavar="FILE")
    parser.add_option("-a", "--algorithm", dest="algorithm",
                  help="write report to FILE", metavar="FILE")
    parser.add_option("-u", "--url", dest="url",
                  help="write report to FILE", metavar="FILE")

    options, arguments = parser.parse_args()

    algo_cls = get_algo_from_name(options.algorithm) if options.algorithm else DecisionTree
    detector = AuthorDetector(FeatureExtractor(), algo_cls)

    options.train = True
    # options.url = 'http://venturebeat.com/2013/05/19/biolite-stoves/'

    if options.train:
        sampler = SampleGenerator(urls_path='urls/small.txt')
        detector.train(sampler)
        # train from saved results
        # detector.train()
        detector.classifier.draw_tree(column_names=Candidate.get_labels())
    if options.url:
        detector.train()  # restore last training data
        detector.predict(options.url)

__main__()