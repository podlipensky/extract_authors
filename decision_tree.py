from PIL import Image, ImageDraw
from math import log


class DecisionTreeClassifier:
    def __init__(self, decision_tree):
        self.decision_tree = decision_tree

    def predict(self, X):
        Y = []
        for x in X:
            Y.append(self.decision_tree.predict(x, self.decision_tree.root))
        return Y


class DecisionNode:
    def __init__(self, col=-1, value=None, results=None, tb=None, fb=None):
        self.col = col  # col is the column index of the criteria to be tested
        self.value = value  # value is the value that the column must match to get a true result
        # results stores a dictionary of results for this branch. This is None for everything except endpoints
        self.results = results
        # tb and fb are DecisionNodes, which are the next nodes in the tree if the result is
        # true or false, respectively.
        self.tb = tb
        self.fb = fb


class DecisionTree:
    def __init__(self):
        self.clf = DecisionTreeClassifier(self)

    # Divides a set on a specific column. Can handle numeric
    # or nominal values
    def divide_set(self, rows, column, value):
        # Make a function that tells us if a row is in
        # the first group (true) or the second group (false)
        split_function = None
        if isinstance(value, int) or isinstance(value, float):
            split_function = lambda row:row[column] >= value
        else:
            split_function = lambda row:row[column] == value
        # Divide the rows into two sets and return them
        set1=[row for row in rows if split_function(row)]
        set2=[row for row in rows if not split_function(row)]
        return (set1, set2)

    # Create counts of possible results (the last column of
    # each row is the result)
    def unique_counts(self, rows):
        results = {}
        for row in rows:
            # The result is the last column
            r = row[len(row) - 1]
            if r not in results: results[r] = 0
            results[r] += 1
        return results

    # Probability that a randomly placed item will
    # be in the wrong category
    def gini_impurity(self, rows):
        total = len(rows)
        counts = self.unique_counts(rows)
        imp = 0
        for k1 in counts:
            p1 = float(counts[k1]) / total
            for k2 in counts:
                if k1 == k2: continue
                p2 = float(counts[k2]) / total
                imp += p1 * p2
        return imp

    # Entropy is the sum of p(x)log(p(x)) across all
    # the different possible results
    def entropy(self, rows):
        log2 = lambda x:log(x) / log(2)
        results = self.unique_counts(rows)  # Now calculate the entropy ent = 0.0
        ent = 0.0
        for r in results.keys():
            p = float(results[r]) / len(rows)
            ent = ent - p * log2(p)
        return ent

    def fit(self, X, Y):
        rows = []
        for x, y in zip(X, Y):
            row = []
            row.extend(x)
            row.extend([y])
            rows.append(row)
        self.root = self.build_tree(rows)
        self.prune(self.root, 0.1)

    def build_tree(self, rows, scoref = None):
        if len(rows) == 0: return DecisionNode()
        if not scoref:
            scoref = self.entropy
        current_score = scoref(rows)
        # Set up some variables to track the best criteria
        best_gain = 0.0
        best_criteria = None
        best_sets = None
        column_count = len(rows[0]) - 1
        for col in range(0, column_count):
            # Generate the list of different values in
            # this column
            column_values = {}
            for row in rows:
                column_values[row[col]] = 1
            # Now try dividing the rows up for each value # in this column
            for value in column_values.keys():
                (set1, set2) = self.divide_set(rows, col, value)
                # Information gain
                p = float(len(set1)) / len(rows)
                gain = current_score - p*scoref(set1) - (1 - p)*scoref(set2)
                if gain > best_gain and len(set1) > 0 and len(set2) > 0:
                    best_gain = gain
                    best_criteria = (col, value)
                    best_sets = (set1, set2)
        # Create the subbranches
        if best_gain > 0:
            trueBranch = self.build_tree(best_sets[0])
            falseBranch = self.build_tree(best_sets[1])
            return DecisionNode(col = best_criteria[0], value = best_criteria[1],
                            tb = trueBranch, fb = falseBranch)
        return DecisionNode(results = self.unique_counts(rows))

    def predict(self, X, node):
        if node.results != None:
            return node.results
        else:
            v = X[node.col]
            branch = None
            if isinstance(v, int) or isinstance(v, float):
                if v >= node.value: branch=node.tb
                else: branch=node.fb
            else:
                if v == node.value: branch = node.tb
                else: branch = node.fb
        return self.predict(X, branch)

    def prune(self, tree, mingain):
        # If the branches aren't leaves, then prune them
        if tree.tb.results == None:
            self.prune(tree.tb, mingain)
        if tree.fb.results == None:
            self.prune(tree.fb, mingain)
        # If both the subbranches are now leaves, see if they
        # should merged
        if tree.tb.results != None and tree.fb.results != None:
            # Build a combined dataset
            tb, fb=[], []
            for v, c in tree.tb.results.items():
                tb += [[v]]*c
            for v, c in tree.fb.results.items():
                fb += [[v]]*c
            # Test the reduction in entropy
            delta = self.entropy(tb + fb) - (self.entropy(tb) + self.entropy(fb) / 2)
            if delta < mingain:
                # Merge the branches
                tree.tb, tree.fb = None, None
                tree.results = self.unique_counts(tb + fb)

    def getwidth(self, tree):
        if tree.tb == None and tree.fb == None: return 1
        return self.getwidth(tree.tb) + self.getwidth(tree.fb)

    def getdepth(self, tree):
        if tree.tb == None and tree.fb == None: return 0
        return max(self.getdepth(tree.tb), self.getdepth(tree.fb)) + 1

    def draw_tree(self, column_names, jpeg = 'tree.jpg'):
        w = self.getwidth(self.root)*100
        h = self.getdepth(self.root)*100 + 120
        img = Image.new('RGB', (w, h), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        self.draw_node(draw, column_names, self.root, w / 2, 20)
        img.save(jpeg, 'JPEG')

    def draw_node(self, draw, column_names, tree, x, y):
        if tree.results == None:
            # Get the width of each branch
            w1 = self.getwidth(tree.fb)*100
            w2 = self.getwidth(tree.tb)*100
            # Determine the total space required by this node
            left = x - (w1 + w2) / 2
            right = x + (w1 + w2) / 2
            # Draw the condition string
            if tree.results == None:
                 text = str(column_names[tree.col]) + ':' + str(tree.value)
            else:
                text = str(tree.value)
            draw.text((x - 20, y - 10), text, (0, 0, 0))
            # Draw links to the branches
            draw.line((x, y, left + w1 / 2, y + 100), fill=(255, 0, 0))
            draw.line((x, y, right - w2 / 2, y + 100), fill=(255, 0, 0))
            # Draw the branch nodes
            self.draw_node(draw, column_names, tree.fb, left + w1 / 2, y + 100)
            self.draw_node(draw, column_names, tree.tb, right - w2 / 2, y + 100)
        else:
            txt = ' \n'.join(['%s:%d'%v for v in tree.results.items()])
            draw.text((x - 20, y), txt, (0, 0, 0))