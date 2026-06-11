"""Helpers for reading product_service responses."""
from typing import Any, Dict, Iterable, List, Optional

import requests


def unwrap_items(payload: Any) -> List[Dict[str, Any]]:
    """Support local service envelopes, DRF pagination, and raw lists."""
    if isinstance(payload, dict) and 'status' in payload and 'data' in payload:
        payload = payload['data']
    if isinstance(payload, dict) and 'results' in payload:
        payload = payload['results']
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def next_url(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        return payload.get('next')
    return None


def product_text(product: Dict[str, Any]) -> str:
    parts = [
        product.get('name', ''),
        product.get('category_root') or _infer_category_root(product),
        ' '.join(product.get('category_path') or []),
        product.get('category_name', ''),
        product.get('description', ''),
    ]
    product_type = product.get('product_type')
    if product_type:
        parts.append(product_type)
    parts.extend(_typed_metadata_parts(product))
    return '. '.join(str(part).strip() for part in parts if part)


def compact_metadata(product: Dict[str, Any]) -> Dict[str, Any]:
    book = product.get('book') or {}
    if not isinstance(book, dict):
        book = {}
    electronics = product.get('electronics') or {}
    if not isinstance(electronics, dict):
        electronics = {}
    fashion = product.get('fashion') or {}
    if not isinstance(fashion, dict):
        fashion = {}

    return {
        'id': product.get('id'),
        'name': product.get('name', ''),
        'category': product.get('category_name', ''),
        'category_root': product.get('category_root') or _infer_category_root(product),
        'category_path': product.get('category_path') or _infer_category_path(product),
        'price': float(product.get('base_price') or 0.0),
        'description': product.get('description', ''),
        'image_url': product.get('image_url'),
        'product_type': product.get('product_type', 'generic'),

        # Book metadata
        'author': book.get('author', ''),
        'isbn': book.get('isbn', ''),
        'publisher': book.get('publisher', ''),
        'publication_year': book.get('publication_year', ''),
        'page_count': book.get('page_count', ''),
        'language': book.get('language', ''),
        'genre': book.get('genre', ''),

        # Electronics metadata
        'brand': fashion.get('brand') or electronics.get('brand', ''),
        'model_number': electronics.get('model_number', ''),
        'warranty_period': electronics.get('warranty_period', ''),
        'voltage_requirement': electronics.get('voltage_requirement', ''),
        'connectivity': electronics.get('connectivity', ''),
        'technical_specs': electronics.get('technical_specs', {}),

        # Fashion metadata
        'audience': _gender_label(fashion.get('gender')),
        'season': fashion.get('season', ''),
        'material': fashion.get('material', ''),
        'color': fashion.get('color', ''),
    }


def _typed_metadata_parts(product: Dict[str, Any]) -> List[Any]:
    parts: List[Any] = []

    book = product.get('book') or {}
    if isinstance(book, dict):
        parts.extend([
            book.get('author'),
            book.get('isbn'),
            book.get('publisher'),
            book.get('publication_year'),
            book.get('language'),
            book.get('genre'),
        ])

    electronics = product.get('electronics') or {}
    if isinstance(electronics, dict):
        parts.extend([
            electronics.get('brand'),
            electronics.get('model_number'),
            electronics.get('warranty_period'),
            electronics.get('voltage_requirement'),
            electronics.get('connectivity'),
            _flatten_dict(electronics.get('technical_specs')),
        ])

    fashion = product.get('fashion') or {}
    if isinstance(fashion, dict):
        parts.extend([
            fashion.get('brand'),
            _gender_label(fashion.get('gender')),
            fashion.get('season'),
            fashion.get('material'),
            fashion.get('color'),
        ])

    return parts


_CATEGORY_ROOTS = {
    'Software Engineering': 'Books',
    'Data Science': 'Books',
    'Cookbooks': 'Books',
    'Clothing': 'Fashion',
    'Shoes': 'Fashion',
    'Bags': 'Fashion',
    'Smartphones': 'Electronics',
    'Laptops': 'Electronics',
    'Earbuds': 'Electronics',
    'Power Banks': 'Electronics',
    'Speakers': 'Electronics',
    'Cookers': 'Electronics',
    'Ovens': 'Electronics',
    'Air Fryers': 'Electronics',
    'Microwaves': 'Electronics',
    'Kitchen & Dining': 'Home & Living',
    'Lighting': 'Home & Living',
    'Storage & Organization': 'Home & Living',
    'Decor': 'Home & Living',
    'Fitness': 'Sports & Outdoors',
    'Running': 'Sports & Outdoors',
    'Cycling': 'Sports & Outdoors',
    'Camping': 'Sports & Outdoors',
}

_CATEGORY_PARENTS = {
    'Smartphones': 'Technology Devices',
    'Laptops': 'Technology Devices',
    'Earbuds': 'Technology Devices',
    'Power Banks': 'Technology Devices',
    'Speakers': 'Technology Devices',
    'Cookers': 'Home Appliances',
    'Ovens': 'Home Appliances',
    'Air Fryers': 'Home Appliances',
    'Microwaves': 'Home Appliances',
}


def _infer_category_root(product: Dict[str, Any]) -> str:
    category = product.get('category_name') or ''
    return _CATEGORY_ROOTS.get(category, '')


def _infer_category_path(product: Dict[str, Any]) -> List[str]:
    category = product.get('category_name') or ''
    root = _infer_category_root(product)
    parent = _CATEGORY_PARENTS.get(category)
    return [item for item in (root, parent, category) if item]


def _flatten_dict(value: Any) -> str:
    if not isinstance(value, dict):
        return str(value or '')
    return ' '.join(f'{key} {item}' for key, item in value.items())


def _gender_label(value: Any) -> str:
    mapping = {'F': 'Female', 'M': 'Male', 'U': 'Unisex'}
    text = str(value or '').strip()
    return mapping.get(text, text)


def fetch_products_by_ids(base_url: str, product_ids: Iterable[int], timeout: float = 3.0) -> Dict[int, Dict[str, Any]]:
    ids = [int(pid) for pid in product_ids]
    if not ids:
        return {}

    response = requests.get(
        f'{base_url}/api/products/',
        params={'ids': ','.join(str(pid) for pid in ids), 'limit': len(ids)},
        timeout=timeout,
    )
    response.raise_for_status()
    products = {}
    for product in unwrap_items(response.json()):
        pid = product.get('id')
        if pid is not None:
            products[int(pid)] = product
    return products
