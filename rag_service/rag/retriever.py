"""FAISS-based semantic product retriever."""
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


class ProductRetriever:
    def __init__(self, faiss_dir: Path, embed_model: str = ''):
        from .embedder import load_index, _get_model
        self.index, self.product_ids, self.product_texts, product_metadata, meta = load_index(faiss_dir)
        self._id_to_offset = {pid: idx for idx, pid in enumerate(self.product_ids)}
        self._metadata = {
            item.get('id'): item
            for item in product_metadata
            if isinstance(item, dict) and item.get('id') is not None
        }
        model_name  = embed_model or meta.get('embed_model',
                                              'paraphrase-multilingual-MiniLM-L12-v2')
        self._model = _get_model(model_name)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Return [(product_id, cosine_score)] ranked by similarity."""
        vec = self._model.encode([query], normalize_embeddings=True)
        vec = np.array(vec, dtype=np.float32)
        scores, indices = self.index.search(vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0:
                results.append((self.product_ids[idx], float(score)))
        return results

    def get_text(self, product_id: int) -> str:
        idx = self._id_to_offset.get(product_id)
        if idx is None:
            return f'Product {product_id}'
        try:
            return self.product_texts[idx]
        except IndexError:
            return f'Product {product_id}'

    def get_metadata(self, product_id: int) -> Dict[str, Any]:
        return self._metadata.get(product_id, {})


@lru_cache(maxsize=1)
def get_retriever() -> ProductRetriever:
    from django.conf import settings
    faiss_dir = Path(settings.FAISS_DIR)
    if not (faiss_dir / 'products.index').exists():
        return None
    return ProductRetriever(faiss_dir, embed_model=settings.EMBED_MODEL)
