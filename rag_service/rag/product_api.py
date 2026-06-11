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
        product.get('category_name', ''),
        product.get('description', ''),
    ]
    product_type = product.get('product_type')
    if product_type:
        parts.append(product_type)
    return '. '.join(str(part).strip() for part in parts if part)


def compact_metadata(product: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': product.get('id'),
        'name': product.get('name', ''),
        'category': product.get('category_name', ''),
        'price': float(product.get('base_price') or 0.0),
        'description': product.get('description', ''),
        'image_url': product.get('image_url'),
        'product_type': product.get('product_type', 'generic'),
    }


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
