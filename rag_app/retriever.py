import numpy as np
from sklearn.neighbors import NearestNeighbors
from typing import List

class Retriever:
    def __init__(self, vectors: np.ndarray, max_neighbors: int = 100):
        # Use cosine metric via metric='cosine'
        self.vectors = vectors
        # Set n_neighbors to min of max_neighbors and actual vector count
        n = min(max_neighbors, len(vectors))
        self.nn = NearestNeighbors(n_neighbors=n, metric='cosine')
        self.nn.fit(vectors)

    def query(self, q_vector: np.ndarray, top_k: int = 5):
        qv = q_vector.reshape(1, -1)
        # Clamp top_k to actual number of samples and ensure at least 1
        k = max(1, min(top_k, len(self.vectors)))
        dists, idxs = self.nn.kneighbors(qv, n_neighbors=k)
        # cosine distance -> similarity
        sims = 1.0 - dists[0]
        return idxs[0].tolist(), sims.tolist()

    @classmethod
    def from_index(cls, index: dict):
        return cls(index['vectors'])
