from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import os

# Configurable max features for TF-IDF vectorizer
DEFAULT_MAX_FEATURES = int(os.environ.get("RAG_MAX_FEATURES", "5000"))

class Embedder:
    """TF-IDF vectorizer for document embeddings.
    
    Args:
        model_name: Name of the embedding model (currently only 'tfidf' supported)
        vectorizer: Optional pre-configured TfidfVectorizer
        max_features: Maximum number of features (default: 5000, configurable via RAG_MAX_FEATURES env var)
    """
    def __init__(self, model_name: str = "tfidf", vectorizer=None, max_features: int = None):
        self.model_name = model_name
        self.max_features = max_features or DEFAULT_MAX_FEATURES
        self.vectorizer = vectorizer or TfidfVectorizer(
            max_features=self.max_features, 
            lowercase=True, 
            stop_words='english',
            ngram_range=(1, 2),  # Include bigrams for better matching
            min_df=1,  # Include rare terms
            max_df=0.95  # Exclude very common terms
        )

    def fit(self, texts):
        """Fit the vectorizer on training texts."""
        self.vectorizer.fit(texts)
        return self

    def embed(self, texts):
        """Return 2D numpy array of embeddings for list of texts."""
        if isinstance(texts, str):
            texts = [texts]
        return self.vectorizer.transform(texts).toarray()
