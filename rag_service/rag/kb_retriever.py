"""Static knowledge base retriever — policies, FAQs, shopping guides.

Documents live in rag_service/knowledge_base/*.json. Each document is a JSON
object with keys: id, title, content, category, keywords.

Retrieval uses a hybrid of:
  - Dense semantic search  (sentence-transformer embeddings, in-memory cosine)
  - Sparse lexical search  (char n-gram TF-IDF)
  fused via Reciprocal Rank Fusion (RRF).

This means paraphrases like "my item is broken" match "damaged / defective
product" and "đổi trả" even when no surface-level characters overlap.
TF-IDF handles exact brand names, model numbers, and Vietnamese diacritic
variants that semantic models may underweight.
"""
import json
import logging
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_KB_MIN_SCORE  = 0.03   # minimum fused score to include a result
_KB_TOP_K      = 3      # max KB entries returned per query
_DENSE_WEIGHT  = 0.65   # weight for semantic score in RRF fusion
_SPARSE_WEIGHT = 0.35   # weight for TF-IDF score in RRF fusion
_RRF_K         = 20     # RRF smoothing constant (small corpus → smaller k)


class KnowledgeRetriever:
    """
    Hybrid dense+sparse retriever over static knowledge-base documents.

    Dense path  : sentence-transformer embeddings → cosine similarity
    Sparse path : char n-gram TF-IDF → cosine similarity
    Fusion      : Weighted Reciprocal Rank Fusion (RRF)
    """

    def __init__(self, kb_dir: Path):
        self._docs: List[Dict] = []
        self._vectorizer = None
        self._tfidf_matrix = None
        self._embeddings: Optional[np.ndarray] = None   # (n_docs, dim)
        self._embed_model = None
        self._load(kb_dir)

    # ── public ────────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = _KB_TOP_K) -> List[Tuple[Dict, float]]:
        """Return [(doc, fused_score)] sorted by relevance, best first."""
        if not self._docs:
            return []

        dense_hits  = self._dense_search(query, top_k=top_k * 2)
        sparse_hits = self._sparse_search(query, top_k=top_k * 2)

        fused = _rrf_fuse(
            [(dense_hits, _DENSE_WEIGHT), (sparse_hits, _SPARSE_WEIGHT)],
            k=_RRF_K,
        )

        results = [
            (self._docs[idx], score)
            for idx, score in sorted(fused.items(), key=lambda x: x[1], reverse=True)
            if score >= _KB_MIN_SCORE
        ]
        return results[:top_k]

    def format_context(self, results: List[Tuple[Dict, float]]) -> str:
        """Format KB results as a context block for the LLM prompt."""
        if not results:
            return ''
        lines = ['[Store Knowledge Base]']
        for doc, _score in results:
            lines.append(f"## {doc['title']}")
            lines.append(doc['content'])
        return '\n'.join(lines)

    # ── private ───────────────────────────────────────────────────────────────

    def _load(self, kb_dir: Path) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        if not kb_dir.exists():
            logger.warning('[KB] knowledge_base directory not found: %s', kb_dir)
            return

        docs: List[Dict] = []
        for json_file in sorted(kb_dir.glob('*.json')):
            try:
                with open(json_file) as f:
                    entries = json.load(f)
                if isinstance(entries, list):
                    docs.extend(entries)
            except Exception as exc:
                logger.warning('[KB] Failed to load %s: %s', json_file, exc)

        if not docs:
            logger.warning('[KB] No knowledge-base documents loaded.')
            return

        # Build rich text for each doc: title + keywords + content
        def _doc_text(doc: Dict) -> str:
            kw = ' '.join(doc.get('keywords') or [])
            return f"{doc.get('title', '')} {kw} {doc.get('content', '')}"

        texts = [_doc_text(d) for d in docs]

        # ── sparse (TF-IDF) index ──────────────────────────────────────
        vectorizer = TfidfVectorizer(
            analyzer='char_wb',
            ngram_range=(3, 5),
            lowercase=True,
            min_df=1,
            norm='l2',
        )
        tfidf_matrix = vectorizer.fit_transform([_normalize(t) for t in texts])

        # ── dense (embedding) index ────────────────────────────────────
        embed_model = None
        embeddings  = None
        try:
            from rag.embedder import _get_model
            from django.conf import settings
            embed_model = _get_model(
                getattr(settings, 'EMBED_MODEL', 'paraphrase-multilingual-MiniLM-L12-v2')
            )
            embeddings = embed_model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            ).astype(np.float32)
            logger.info('[KB] Dense embeddings built for %d documents.', len(docs))
        except Exception as exc:
            logger.warning('[KB] Dense index unavailable, falling back to sparse only: %s', exc)

        self._docs         = docs
        self._vectorizer   = vectorizer
        self._tfidf_matrix = tfidf_matrix
        self._embed_model  = embed_model
        self._embeddings   = embeddings
        logger.info('[KB] Loaded %d knowledge-base documents from %s', len(docs), kb_dir)

    def _dense_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Return [(doc_idx, cosine_score)] using sentence-transformer embeddings."""
        if self._embed_model is None or self._embeddings is None:
            return []
        try:
            q_vec = self._embed_model.encode(
                [query], normalize_embeddings=True, show_progress_bar=False,
            ).astype(np.float32)
            scores = (self._embeddings @ q_vec.T).ravel()
            top_k  = min(top_k, len(scores))
            idxs   = scores.argsort()[::-1][:top_k]
            return [(int(i), float(scores[i])) for i in idxs]
        except Exception as exc:
            logger.warning('[KB] Dense search error: %s', exc)
            return []

    def _sparse_search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Return [(doc_idx, tfidf_score)] using char n-gram TF-IDF."""
        if self._vectorizer is None or self._tfidf_matrix is None:
            return []
        try:
            q_vec  = self._vectorizer.transform([_normalize(query)])
            scores = (self._tfidf_matrix @ q_vec.T).toarray().ravel()
            top_k  = min(top_k, len(scores))
            idxs   = scores.argsort()[::-1][:top_k]
            return [(int(i), float(scores[i])) for i in idxs if scores[i] > 0]
        except Exception as exc:
            logger.warning('[KB] Sparse search error: %s', exc)
            return []


# ── helpers ───────────────────────────────────────────────────────────────────

def _rrf_fuse(
    rankings: List[Tuple[List[Tuple[int, float]], float]],
    k: int = _RRF_K,
) -> Dict[int, float]:
    """Weighted Reciprocal Rank Fusion. Only rank positions matter, not raw scores."""
    fused: Dict[int, float] = {}
    k = max(1, k)
    for hits, weight in rankings:
        if weight <= 0:
            continue
        for rank, (idx, _score) in enumerate(hits, start=1):
            fused[idx] = fused.get(idx, 0.0) + weight / (k + rank)
    return fused


def _normalize(value: str) -> str:
    value = unicodedata.normalize('NFD', value.lower())
    value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn')
    return re.sub(r'\s+', ' ', value).strip()


# ── module-level singleton ────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_kb_retriever() -> Optional[KnowledgeRetriever]:
    from django.conf import settings
    kb_dir = Path(settings.BASE_DIR) / 'knowledge_base'
    return KnowledgeRetriever(kb_dir)
