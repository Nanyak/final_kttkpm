"""Build and load dense FAISS and sparse TF-IDF indexes over product text."""
import json
import pickle
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np


TFIDF_VECTORIZER_FILE = 'tfidf_vectorizer.pkl'
TFIDF_MATRIX_FILE = 'tfidf_matrix.npz'


@lru_cache(maxsize=1)
def _get_model(model_name: str):
    from sentence_transformers import SentenceTransformer
    print(f'[RAG] Loading embedding model: {model_name}')
    return SentenceTransformer(model_name, device='cpu')


def build_index(
    products: List[Tuple[int, str, str]],   # [(product_id, name, description), ...]
    faiss_dir: Path,
    embed_model: str = 'paraphrase-multilingual-MiniLM-L12-v2',
    product_metadata: List[Dict[str, Any]] = None,
):
    import faiss
    from scipy import sparse
    from sklearn.feature_extraction.text import TfidfVectorizer

    faiss_dir.mkdir(parents=True, exist_ok=True)
    ids   = [p[0] for p in products]
    texts = [f'{p[1]}. {p[2]}' for p in products]

    model = _get_model(embed_model)
    vecs  = model.encode(texts, batch_size=64, normalize_embeddings=True,
                         show_progress_bar=True)
    vecs  = np.array(vecs, dtype=np.float32)

    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)

    # Character n-grams make sparse matching robust for model numbers, brands,
    # product names, and Vietnamese text without needing a language tokenizer.
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(3, 5),
        lowercase=True,
        min_df=1,
        norm='l2',
    )
    tfidf_matrix = vectorizer.fit_transform(texts)

    faiss.write_index(index, str(faiss_dir / 'products.index'))
    sparse.save_npz(faiss_dir / TFIDF_MATRIX_FILE, tfidf_matrix)
    with open(faiss_dir / TFIDF_VECTORIZER_FILE, 'wb') as f:
        pickle.dump(vectorizer, f)
    with open(faiss_dir / 'product_ids.json',   'w') as f: json.dump(ids,   f)
    with open(faiss_dir / 'product_texts.json', 'w') as f: json.dump(texts, f)
    with open(faiss_dir / 'product_metadata.json', 'w') as f:
        json.dump(product_metadata or [], f)
    with open(faiss_dir / 'meta.json',          'w') as f:
        json.dump({'dim': vecs.shape[1], 'embed_model': embed_model}, f)

    print(
        f'[RAG] FAISS index ({index.ntotal} vectors) and '
        f'TF-IDF matrix ({tfidf_matrix.shape[0]} docs) saved to {faiss_dir}'
    )
    return index, ids


def load_index(faiss_dir: Path):
    import faiss
    index = faiss.read_index(str(faiss_dir / 'products.index'))
    with open(faiss_dir / 'product_ids.json')   as f: product_ids   = json.load(f)
    with open(faiss_dir / 'product_texts.json') as f: product_texts = json.load(f)
    with open(faiss_dir / 'meta.json')          as f: meta          = json.load(f)
    metadata_path = faiss_dir / 'product_metadata.json'
    if metadata_path.exists():
        with open(metadata_path) as f:
            product_metadata = json.load(f)
    else:
        product_metadata = []
    return index, product_ids, product_texts, product_metadata, meta
