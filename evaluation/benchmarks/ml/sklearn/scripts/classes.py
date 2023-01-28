from sklearn.linear_model import _logistic
import sys
import numpy as np
import pickle

with open(sys.argv[1], 'rb') as file:
    y = pickle.load(file)

try:
    _logistic.check_classification_targets(y)
    with open('./tmp/classes.obj', 'w+b') as file:
        pickle.dump(np.unique(y), file)
    exit(0)
except:
    exit(1)