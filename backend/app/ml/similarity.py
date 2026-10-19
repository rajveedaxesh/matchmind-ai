"""Text similarity: TF-IDF cosine plus a semantic embedding signal.

Semantic backends
-----------------
* ``lsa`` (default) - Latent Semantic Analysis (TF-IDF + truncated SVD). Fully local, needs only
  scikit-learn, no downloads. It captures co-occurrence ("fastapi" ~ "rest" ~ "python") learned from
  the corpus the engine was fitted on.
* ``sentence-transformers`` (optional) - neural sentence embeddings. Only used when the package is
  installed AND the model can be loaded; otherwise we silently fall back to LSA and record why.
"""
from __future__ import annotations

import logging
import re
from typing import Sequence

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import Normalizer

logger = logging.getLogger(__name__)

_REPLACEMENTS = (
    (re.compile(r"c\+\+", re.I), "cpp"),
    (re.compile(r"c#", re.I), "csharp"),
    (re.compile(r"\.net\b", re.I), "dotnet"),
    (re.compile(r"\b(node|next|vue|react)\.js\b", re.I), r"\1js"),
    (re.compile(r"\bci\s*/\s*cd\b", re.I), "cicd"),
    (re.compile(r"\ba\s*/\s*b\b", re.I), "abtesting"),
)


def prepare_text(text: str) -> str:
    """Lowercase and protect tokens that tokenisers would otherwise mangle (c++, node.js ...)."""
    out = (text or "").lower()
    for pattern, repl in _REPLACEMENTS:
        out = pattern.sub(repl, out)
    return re.sub(r"\s+", " ", out).strip()


class LsaEncoder:
    name = "lsa"

    def __init__(self, n_components: int = 48, random_state: int = 42) -> None:
        self.n_components = n_components
        self.random_state = random_state
        self.available = False
        self._vectorizer: TfidfVectorizer | None = None
        self._svd: TruncatedSVD | None = None
        self._norm = Normalizer(copy=False)

    def fit(self, docs: Sequence[str]) -> "LsaEncoder":
        self._vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
        matrix = self._vectorizer.fit_transform(docs)
        k = min(self.n_components, matrix.shape[0] - 1, matrix.shape[1] - 1)
        if k < 2:
            self.available = False
            return self
        self._svd = TruncatedSVD(n_components=k, random_state=self.random_state)
        self._svd.fit(matrix)
        self.available = True
        return self

    def transform(self, texts: Sequence[str]) -> np.ndarray:
        assert self._vectorizer is not None and self._svd is not None
        return self._norm.transform(self._svd.transform(self._vectorizer.transform(texts)))


class SentenceTransformerEncoder:
    name = "sentence-transformers"

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # optional dependency

        self._model = SentenceTransformer(model_name)
        self.available = True

    def fit(self, docs: Sequence[str]) -> "SentenceTransformerEncoder":
        return self  # pre-trained; nothing to fit

    def transform(self, texts: Sequence[str]) -> np.ndarray:
        return np.asarray(self._model.encode(list(texts), normalize_embeddings=True))


def build_encoder(backend: str = "lsa", model_name: str = "all-MiniLM-L6-v2"):
    """Return ``(encoder, fallback_reason)``. Never raises for an unavailable optional backend."""
    if backend == "sentence-transformers":
        try:
            return SentenceTransformerEncoder(model_name), None
        except Exception as exc:  # ImportError, offline model download failure, ...
            reason = f"sentence-transformers unavailable ({type(exc).__name__}); using local LSA"
            logger.warning(reason)
            return LsaEncoder(), reason
    return LsaEncoder(), None


class TextSimilarity:
    """TF-IDF cosine blended with a semantic embedding cosine, with graceful degradation."""

    def __init__(
        self,
        encoder_backend: str = "lsa",
        semantic_weight: float = 0.35,
        saturation: float = 0.40,
        st_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.semantic_weight = semantic_weight
        # Raw cosine values between a profile and a posting are naturally small (rarely above 0.5).
        # A raw blended cosine >= ``saturation`` counts as 100% text alignment. Tunable constant.
        self.saturation = saturation
        self._backend_requested = encoder_backend
        self._st_model = st_model
        self.encoder = None
        self.fallback_reason: str | None = None
        self.tfidf: TfidfVectorizer | None = None
        self._features: np.ndarray | None = None
        self._cache: dict[str, tuple] = {}

    # ------------------------------------------------------------------ fitting
    def fit(self, corpus: Sequence[str]) -> "TextSimilarity":
        docs = [prepare_text(d) for d in corpus if d and d.strip()] or ["placeholder document"]
        self.tfidf = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        try:
            self.tfidf.fit(docs)
        except ValueError:  # e.g. every document was only stop-words
            self.tfidf = TfidfVectorizer(ngram_range=(1, 1), sublinear_tf=False).fit(docs + ["placeholder"])
        self._features = np.asarray(self.tfidf.get_feature_names_out())
        encoder, self.fallback_reason = build_encoder(self._backend_requested, self._st_model)
        try:
            self.encoder = encoder.fit(docs)
        except ValueError:
            self.encoder = LsaEncoder()
            self.encoder.available = False
        self._cache.clear()
        return self

    @property
    def semantic_available(self) -> bool:
        return bool(self.encoder is not None and getattr(self.encoder, "available", False))

    @property
    def backend_name(self) -> str:
        if not self.semantic_available:
            return "tfidf-only"
        return self.encoder.name

    # ----------------------------------------------------------------- vectors
    def _vectors(self, text: str):
        hit = self._cache.get(text)  # keyed by the raw text: avoids re-running prepare_text for repeat documents
        if hit is None:
            if self.tfidf is None:
                self.fit([text])
            key = prepare_text(text)
            sparse = self.tfidf.transform([key])
            dense = self.encoder.transform([key])[0] if self.semantic_available else None
            hit = (sparse, dense)
            self._cache[text] = hit
        return hit

    # -------------------------------------------------------------- similarity
    def tfidf_cosine(self, a: str, b: str) -> float:
        if not a.strip() or not b.strip():
            return 0.0
        va, vb = self._vectors(a)[0], self._vectors(b)[0]
        return float(np.clip(va.multiply(vb).sum(), 0.0, 1.0))  # rows are L2-normalised

    def semantic_cosine(self, a: str, b: str) -> float | None:
        if not self.semantic_available or not a.strip() or not b.strip():
            return None
        da, db = self._vectors(a)[1], self._vectors(b)[1]
        return float(np.clip(np.dot(da, db), 0.0, 1.0))

    def similarity(self, a: str, b: str) -> dict[str, float | None]:
        """Return raw cosines plus a calibrated 0-1 ``score``."""
        tf = self.tfidf_cosine(a, b)
        sem = self.semantic_cosine(a, b)
        raw = tf if sem is None else (1 - self.semantic_weight) * tf + self.semantic_weight * sem
        return {"tfidf": tf, "semantic": sem, "raw": raw, "score": float(min(1.0, raw / self.saturation))}

    def shared_terms(self, a: str, b: str, n: int = 6) -> list[str]:
        """Highest-weighted terms present in both documents (for explanations)."""
        if not a.strip() or not b.strip():
            return []
        prod = self._vectors(a)[0].multiply(self._vectors(b)[0]).tocoo()
        if prod.nnz == 0:
            return []
        order = np.argsort(-prod.data, kind="stable")
        terms: list[str] = []
        covered: set[str] = set()
        for idx in order:
            words = str(self._features[prod.col[idx]]).split()
            term = " ".join(words)
            if all(w in covered for w in words):
                continue  # adds no new information (e.g. a unigram already inside a kept bigram)
            terms.append(term)
            covered.update(words)
            if len(terms) >= n:
                break
        return terms
