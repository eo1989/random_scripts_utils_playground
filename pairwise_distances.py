import numpy as np


def pdist(X1, X2):
    """
    Computes the matrix of pairwise distances btwn X1 & X2.

    The implementation is based on the following observation for matrices:
    (X1 - X2)^2 = X1^2 - 2(X1X2) + X2^2

    Parameters
    ----------
        X1: Array of m points (m x d)
        X2: Array of n points (n x d)

    Returns
    -------
        Matrix (m x n) of pairwise euclidean (L2) distances.


    Sanity Check!
    -------------
        from sklearn.metrics import pairwise_distances
        np.allclose(pairwise_distances(X1, X2, metric='l2'), pdist(X1, X2))
    """
    sqdist = np.sum(X1 ** 2, 1).reshape(-1, 1) + np.sum(X2 ** 2, 1) - 2 * X1 @ X2.T
    return np.sqrt(sqdist)
