# Borrowed for testing with real test data from the scikit-learn project.
# https://github.com/scikit-learn/scikit-learn

PYTHON_TEST_FILES = {"file1.py": """
from abc import ABCMeta
from abc import abstractmethod

import numpy as np
from scipy.special import expit, logsumexp

from ..tree._tree import TREE_LEAF
from ..utils.stats import _weighted_percentile
from ..dummy import DummyClassifier
from ..dummy import DummyRegressor

class LossFunction(metaclass=ABCMeta):
    
    is_multi_class = False

    def __init__(self, n_classes):
        self.K = n_classes

    def init_estimator(self):
        raise NotImplementedError()

    @abstractmethod
    def __call__(self, y, raw_predictions, sample_weight=None):

    @abstractmethod
    def negative_gradient(self, y, raw_predictions, **kargs):

    def update_terminal_regions(self, tree, X, y, residual, raw_predictions,
                                sample_weight, sample_mask,
                                learning_rate=0.1, k=0):
       
        # compute leaf for each sample in ``X``.
        terminal_regions = tree.apply(X)

        # mask all which are not in sample mask.
        masked_terminal_regions = terminal_regions.copy()
        masked_terminal_regions[~sample_mask] = -1

        # update each leaf (= perform line search)
        for leaf in np.where(tree.children_left == TREE_LEAF)[0]:
            self._update_terminal_region(tree, masked_terminal_regions,
                                         leaf, X, y, residual,
                                         raw_predictions[:, k], sample_weight)

        # update predictions (both in-bag and out-of-bag)
        raw_predictions[:, k] += \
            learning_rate * tree.value[:, 0, 0].take(terminal_regions, axis=0)

    @abstractmethod
    def _update_terminal_region(self, tree, terminal_regions, leaf, X, y,
                                residual, raw_predictions, sample_weight):

    @abstractmethod
    def get_init_raw_predictions(self, X, estimator):
        pass
""", "file2.py": """
from __future__ import division, print_function, absolute_import
import numpy as np
from scipy.linalg import (inv, eigh, cho_factor, cho_solve, cholesky, orth,
                          LinAlgError)
from scipy.sparse.linalg import aslinearoperator

__all__ = ['lobpcg']

def bmat(*args, **kwargs):
    import warnings
    with warnings.catch_warnings(record=True):
        warnings.filterwarnings(
            'ignore', '.*the matrix subclass is not the recommended way.*')
        return np.bmat(*args, **kwargs)


def _save(ar, fileName):
    # Used only when verbosity level > 10.
    np.savetxt(fileName, ar)


def _report_nonhermitian(M, name):
    from scipy.linalg import norm

    md = M - M.T.conj()

    nmd = norm(md, 1)
    tol = 10 * np.finfo(M.dtype).eps
    tol = max(tol, tol * norm(M, 1))
    if nmd > tol:
        print('matrix %s of the type %s is not sufficiently Hermitian:'
              % (name, M.dtype))
        print('condition: %.e < %e' % (nmd, tol))
"""}
