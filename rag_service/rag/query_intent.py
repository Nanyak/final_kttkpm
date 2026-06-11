"""Lightweight shopping-query intent helpers for RAG ranking."""
import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class QueryIntent:
    max_price: Optional[float] = None
    categories: frozenset[str] = frozenset()
    product_types: frozenset[str] = frozenset()
    audiences: frozenset[str] = frozenset()
    seasons: frozenset[str] = frozenset()

    @property
    def has_constraints(self) -> bool:
        return bool(
            self.max_price or self.categories or self.product_types or
            self.audiences or self.seasons
        )


_CATEGORY_TERMS = {
    'Earbuds': (
        'earbud', 'earbuds', 'headphone', 'headphones', 'headset', 'tai nghe',
        'airpod', 'airpods', 'aeropods',
    ),
    'Clothing': (
        'clothing', 'clothes', 'shirt', 'shirts', 'tee', 't-shirt', 'hoodie',
        'sweater', 'jacket', 'jeans', 'quan ao', 'quần áo', 'ao', 'áo',
        'quan', 'quần',
    ),
    'Shoes': ('shoes', 'sneakers', 'giay', 'giày'),
    'Bags': ('bag', 'bags', 'tote', 'backpack', 'balo', 'tui', 'túi'),
    'Power Banks': ('power bank', 'powerbank', 'sac du phong', 'sạc dự phòng'),
    'Speakers': ('speaker', 'speakers', 'loa'),
    'Smartphones': ('smartphone', 'phone', 'iphone', 'dien thoai', 'điện thoại'),
    'Laptops': ('laptop', 'may tinh', 'máy tính'),
}

_ROOT_TERMS = {
    'fashion': ('fashion', 'thoi trang', 'thời trang'),
    'electronics': ('electronics', 'do dien tu', 'đồ điện tử', 'cong nghe', 'công nghệ'),
    'book': ('book', 'books', 'sach', 'sách'),
}

_AUDIENCE_TERMS = {
    'female': ('women', 'woman', 'female', 'ladies', 'girl', 'girls', 'womens', "women's", 'nu', 'nữ'),
    'male': ('men', 'man', 'male', 'mens', "men's", 'nam'),
    'unisex': ('unisex', 'all gender', 'all genders'),
}

_SEASON_TERMS = {
    'winter': ('winter', 'cold weather', 'warm', 'fleece', 'down', 'mua dong', 'mùa đông', 'lanh', 'lạnh'),
    'summer': ('summer', 'hot weather', 'lightweight', 'mua he', 'mùa hè'),
}


def parse_query_intent(query: str) -> QueryIntent:
    normalized = _normalize(query)
    max_price = _parse_max_price(normalized)

    categories = {
        category
        for category, terms in _CATEGORY_TERMS.items()
        if any(_has_term(normalized, term) for term in (_normalize(t) for t in terms))
    }
    product_types = {
        product_type
        for product_type, terms in _ROOT_TERMS.items()
        if any(_has_term(normalized, term) for term in (_normalize(t) for t in terms))
    }
    audiences = {
        audience
        for audience, terms in _AUDIENCE_TERMS.items()
        if any(_has_term(normalized, term) for term in (_normalize(t) for t in terms))
    }
    seasons = {
        season
        for season, terms in _SEASON_TERMS.items()
        if any(_has_term(normalized, term) for term in (_normalize(t) for t in terms))
    }

    if categories & {'Clothing', 'Shoes', 'Bags'}:
        product_types.add('fashion')
    if categories & {'Earbuds', 'Power Banks', 'Speakers', 'Smartphones', 'Laptops'}:
        product_types.add('electronics')

    return QueryIntent(
        max_price=max_price,
        categories=frozenset(categories),
        product_types=frozenset(product_types),
        audiences=frozenset(audiences),
        seasons=frozenset(seasons),
    )


def score_metadata_match(metadata: Dict[str, Any], intent: QueryIntent) -> float:
    if not intent.has_constraints:
        return 1.0

    score = 1.0
    category = _normalize(str(metadata.get('category', '')))
    category_root = _normalize(str(metadata.get('category_root', '')))
    category_path = _normalize(' '.join(metadata.get('category_path') or []))
    product_type = _normalize(str(metadata.get('product_type', '')))
    name = _normalize(str(metadata.get('name', '')))
    audience = _normalize(str(metadata.get('audience', '')))
    season = _normalize(str(metadata.get('season', '')))
    brand = _normalize(str(metadata.get('brand', '')))
    material = _normalize(str(metadata.get('material', '')))
    description = _normalize(str(metadata.get('description', '')))
    haystack = ' '.join([
        name,
        category,
        category_root,
        category_path,
        product_type,
        audience,
        season,
        brand,
        material,
        description,
        _normalize(str(metadata.get('author', ''))),
        _normalize(str(metadata.get('isbn', ''))),
        _normalize(str(metadata.get('publisher', ''))),
        _normalize(str(metadata.get('language', ''))),
        _normalize(str(metadata.get('genre', ''))),
        _normalize(str(metadata.get('model_number', ''))),
        _normalize(str(metadata.get('connectivity', ''))),
        _normalize(str(metadata.get('warranty_period', ''))),
        _normalize(str(metadata.get('voltage_requirement', ''))),
        _normalize(str(metadata.get('technical_specs', ''))),
    ])

    if intent.max_price is not None:
        price = _as_float(metadata.get('price'))
        if price is None:
            score *= 0.85
        elif price <= intent.max_price:
            score *= 1.35
        else:
            over_ratio = price / max(intent.max_price, 1.0)
            score *= 0.15 if over_ratio > 1.25 else 0.45

    if intent.categories:
        normalized_categories = {_normalize(item) for item in intent.categories}
        if category in normalized_categories or any(item in haystack for item in normalized_categories):
            score *= 1.8
        else:
            score *= 0.25

    if intent.product_types:
        normalized_types = {_normalize(item) for item in intent.product_types}
        if product_type in normalized_types or category_root in normalized_types or any(item in category_path for item in normalized_types):
            score *= 1.2
        else:
            score *= 0.7

    if intent.audiences:
        normalized_audiences = {_normalize(item) for item in intent.audiences}
        if audience in normalized_audiences or 'unisex' in audience or any(item in haystack for item in normalized_audiences):
            score *= 1.5
        else:
            score *= 0.35

    if intent.seasons:
        normalized_seasons = {_normalize(item) for item in intent.seasons}
        if season in normalized_seasons or any(item in haystack for item in normalized_seasons):
            score *= 1.35
        else:
            score *= 0.65

    return score


def filter_relevant_hits(hits: Iterable[tuple[int, float]], metadata_by_pid: Dict[int, Dict[str, Any]], intent: QueryIntent) -> list[tuple[int, float]]:
    if not intent.has_constraints:
        return list(hits)

    reranked = []
    for pid, score in hits:
        metadata = metadata_by_pid.get(pid, {})
        adjusted = score * score_metadata_match(metadata, intent)
        if adjusted > 0:
            reranked.append((pid, adjusted))
    return sorted(reranked, key=lambda item: item[1], reverse=True)


def _parse_max_price(normalized_query: str) -> Optional[float]:
    if not any(term in normalized_query for term in ('duoi', '<', 'under', 'below', 'toi da', 'max')):
        return None

    patterns = (
        r'(?:duoi|under|below|toi da|max|<)\s*(\d+(?:[.,]\d+)?)\s*(trieu|tr|m|k|nghin|ngan|vnd|d|₫)?',
        r'(\d+(?:[.,]\d+)?)\s*(trieu|tr|m|k|nghin|ngan)\s*(?:tro xuong|do lai|or less)?',
    )
    for pattern in patterns:
        match = re.search(pattern, normalized_query)
        if match:
            amount = float(match.group(1).replace(',', '.'))
            unit = match.group(2) or ''
            return amount * _unit_multiplier(unit)
    return None


def _unit_multiplier(unit: str) -> float:
    if unit in {'trieu', 'tr', 'm'}:
        return 1_000_000.0
    if unit in {'k', 'nghin', 'ngan'}:
        return 1_000.0
    return 1.0


def _normalize(value: str) -> str:
    value = unicodedata.normalize('NFD', value.lower())
    value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn')
    return re.sub(r'\s+', ' ', value).strip()


def _has_term(text: str, term: str) -> bool:
    if ' ' in term:
        return term in text
    return re.search(rf'(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])', text) is not None


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
