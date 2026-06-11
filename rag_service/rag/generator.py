"""LLM answer generation with product context."""
import re
import unicodedata
from typing import List, Optional

SYSTEM_PROMPT = """You are a helpful e-commerce assistant with two sources of knowledge:

1. [Store Knowledge Base] — authoritative answers about store policies (shipping, returns, \
payment methods, warranty, promotions) and FAQs. When this block appears in the context, \
use it directly and accurately; do NOT invent or guess policy details.

2. [Product Results] — live product data retrieved for the customer's query. Give concise, \
personalised recommendations mentioning specific product names and key features.

Additional rules:
- Answer policy/FAQ questions from the Knowledge Base block only; never fabricate policies.
- For product queries, reference specific products from the Product Results block.
- For follow-up questions, acknowledge previously discussed products and compare.
- If neither block contains relevant information, say so politely.
- Respond in the same language the user used."""

# Vietnamese shorthand expansions applied before retrieval to improve recall.
_VI_EXPANSIONS = {
    'tai nghe':      'tai nghe headphone earbuds',
    'dt':            'điện thoại smartphone',
    'dien thoai':    'điện thoại smartphone',
    'đt':            'điện thoại smartphone',
    'loa bt':        'loa bluetooth speaker',
    'sac dp':        'sạc dự phòng power bank',
    'sac du phong':  'sạc dự phòng power bank',
    'may tinh xach tay': 'laptop máy tính xách tay',
    'tui xach':      'túi xách bag handbag',
    'balo':          'balo backpack',
}


def generate_answer(
    query:      str,
    context:    str,
    api_key:    str,
    model:      str = 'gpt-4o-mini',
    max_tokens: int = 512,
    history:    List[dict] = None,
) -> str:
    from openai import OpenAI
    client   = OpenAI(api_key=api_key)
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    if history:
        messages.extend(history[-6:])

    messages.append({
        'role':    'user',
        'content': f'Product context:\n{context}\n\nCustomer question: {query}',
    })

    response = client.chat.completions.create(
        model=model, messages=messages,
        max_tokens=max_tokens, temperature=0.7,
    )
    return response.choices[0].message.content.strip()


def generate_answer_stream(
    query:      str,
    context:    str,
    api_key:    str,
    model:      str = 'gpt-4o-mini',
    max_tokens: int = 512,
    history:    List[dict] = None,
):
    """Yield text tokens one at a time using the OpenAI streaming API."""
    from openai import OpenAI
    client   = OpenAI(api_key=api_key)
    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

    if history:
        messages.extend(history[-6:])

    messages.append({
        'role':    'user',
        'content': f'Product context:\n{context}\n\nCustomer question: {query}',
    })

    stream = client.chat.completions.create(
        model=model, messages=messages,
        max_tokens=max_tokens, temperature=0.7,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def generate_fallback(query: str, context: str, history: Optional[List[dict]] = None) -> str:
    is_vi    = looks_vietnamese(query)
    q_lower  = query.lower()
    has_prior = bool(history and any(m.get('role') == 'assistant' for m in history))

    wants_cheaper = any(kw in q_lower for kw in (
        'cheaper', 'less expensive', 'lower price', 'more affordable', 'budget',
        'rẻ hơn', 're hon', 'giá thấp hơn', 'ít tiền hơn',
    ))

    if not context:
        if has_prior:
            if is_vi:
                return "Mình không tìm thấy thêm sản phẩm phù hợp. Bạn có thể cho biết ngân sách tối đa hoặc mô tả thêm tính năng cần thiết không?"
            return "I couldn't find more products matching that. Could you share your maximum budget or describe the key features you need?"
        if is_vi:
            return "Mình chưa tìm thấy sản phẩm thật sự phù hợp với yêu cầu này. Bạn thử nới ngân sách hoặc mô tả rõ hơn nhóm hàng nhé."
        return "I couldn't find products that clearly match this request. Try widening the budget or adding a more specific category."

    raw_lines = [l for l in context.split('\n') if l.strip()][:5]

    if wants_cheaper:
        raw_lines = _sort_lines_by_price(raw_lines)

    display_lines = raw_lines[:3]
    products = '\n'.join(_format_product_line(line) for line in display_lines)

    if has_prior and wants_cheaper:
        if is_vi:
            return (
                f"Đây là những lựa chọn có giá thấp hơn mình tìm được:\n\n"
                f"{products}\n\n"
                f"Bạn muốn lọc thêm theo hãng, hoặc cho mình biết ngân sách tối đa không?"
            )
        return (
            f"Here are the more affordable options I found:\n\n"
            f"{products}\n\n"
            f"Want to filter further by brand, or tell me your maximum budget?"
        )

    if has_prior:
        if is_vi:
            return (
                f"Dựa trên cuộc trò chuyện của chúng ta, đây là kết quả tìm được:\n\n"
                f"{products}\n\n"
                f"Bạn muốn lọc kỹ hơn không?"
            )
        return (
            f"Based on our conversation, here's what I found:\n\n"
            f"{products}\n\nWould you like to refine these results?"
        )

    if is_vi:
        return (
            f"Mình tìm được vài sản phẩm hợp với \"{query}\":\n\n"
            f"{products}\n\nBạn muốn mình lọc kỹ hơn theo hãng, màu, hoặc mức giá sát hơn không?"
        )
    return (
        f"Here are a few products that match \"{query}\":\n\n"
        f"{products}\n\nWould you like me to narrow these down by brand, color, or a tighter budget?"
    )


def generate_follow_ups(query: str, context: str, is_vi: bool = False) -> List[str]:
    """
    Return 2–3 contextual follow-up question suggestions based on the query and
    retrieved context. These are heuristic — no LLM call required.
    """
    q_lower = query.lower()
    suggestions: List[str] = []

    # Detect what type of query this is
    is_price_query = any(kw in q_lower for kw in ('price', 'giá', 'rẻ', 'cheap', 'budget', 'tiền'))
    is_compare = any(kw in q_lower for kw in ('vs', 'compare', 'so sánh', 'khác', 'better', 'tốt hơn'))
    is_policy = '[Store Knowledge Base]' in context

    if is_policy:
        if is_vi:
            suggestions += ['Thời gian giao hàng mất bao lâu?', 'Tôi có thể đổi trả hàng không?']
        else:
            suggestions += ['How long does shipping take?', 'What is your return policy?']
    elif is_compare:
        if is_vi:
            suggestions += ['Sản phẩm nào có pin tốt hơn?', 'Loại nào phù hợp cho sinh viên?']
        else:
            suggestions += ['Which one has better battery life?', 'Which is better for students?']
    elif is_price_query:
        if is_vi:
            suggestions += ['Có khuyến mãi nào đang áp dụng không?', 'Sản phẩm nào tốt nhất trong tầm giá này?']
        else:
            suggestions += ['Are there any ongoing promotions?', 'What is the best option in this price range?']
    else:
        if is_vi:
            suggestions += ['Sản phẩm nào bán chạy nhất?', 'Có màu sắc hoặc kiểu dáng nào khác không?']
        else:
            suggestions += ['What are the most popular options?', 'Are there other colors or styles available?']

    # Always offer to filter/compare if there are product results
    if context and '[ID:' in context:
        if is_vi:
            suggestions.append('So sánh các sản phẩm này với nhau?')
        else:
            suggestions.append('Can you compare these products for me?')

    return suggestions[:3]


def expand_query(query: str) -> str:
    """
    Expand Vietnamese shorthand and common abbreviations before retrieval
    to improve recall on short/informal queries.
    """
    normalized = _normalize_vi(query)
    expanded = normalized
    for shorthand, expansion in _VI_EXPANSIONS.items():
        if shorthand in normalized:
            expanded = expanded.replace(shorthand, expansion)
    # Return original query if no expansion matched (avoid mangling good queries)
    return expanded if expanded != normalized else query


def _sort_lines_by_price(lines: list) -> list:
    def _extract_price(line: str) -> float:
        m = re.search(r'(\d[\d,.]+)\s*VND', line, re.IGNORECASE)
        if m:
            try:
                return float(m.group(1).replace(',', '').replace('.', ''))
            except ValueError:
                pass
        return float('inf')
    return sorted(lines, key=_extract_price)


def _format_product_line(line: str) -> str:
    line = _strip_context_prefix(line)
    parts = [part.strip() for part in line.split('|') if part.strip()]
    if not parts:
        return ''

    name = parts[0]
    price = next((part for part in parts[1:] if _looks_like_price(part)), '')
    description = next(
        (part for part in parts[1:]
         if part != price and not _looks_like_category(part) and not _is_demo_description(part)),
        '',
    )

    summary = f"- {name}"
    if price:
        summary += f" - {price}"
    if description:
        summary += f"\n  {description}"
    return summary


def _strip_context_prefix(line: str) -> str:
    line = re.sub(r'^\d+\.\s*', '', line.strip())
    line = re.sub(r'\[ID:(\d+)\]\s*', '', line)
    return line


def _looks_like_price(text: str) -> bool:
    return (
        bool(re.search(r'\b(VND|₫|USD|\$)\b', text, re.IGNORECASE))
        or bool(re.search(r'\d[\d,.]*\s*(k|m)?$', text, re.IGNORECASE))
    )


def _looks_like_category(text: str) -> bool:
    categories = {'laptops', 'electronics', 'books', 'fashion', 'home', 'generic'}
    return text.strip().lower() in categories


def _is_demo_description(text: str) -> bool:
    lowered = text.lower()
    return 'generated for demo' in lowered or 'rag retrieval scenarios' in lowered


def _normalize_vi(text: str) -> str:
    """Lowercase + strip diacritics for Vietnamese shorthand matching."""
    text = unicodedata.normalize('NFD', text.lower())
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
    return re.sub(r'\s+', ' ', text).strip()


# Vietnamese-specific Unicode tone marks and characters not found in other Latin scripts.
_VI_DIACRITICS = re.compile(
    r'[àáảãạăắặằẳẵâấầẩẫậèéẻẽẹêếềểễệìíỉĩị'
    r'òóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ'
    r'ÀÁẢÃẠĂẮẶẰẲẴÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊ'
    r'ÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ]',
    re.UNICODE,
)

_VI_COMMON_WORDS = frozenset({
    'toi', 'ban', 'co', 'khong', 'duoc', 'san pham', 'mua', 'gia', 'hang',
    'tot', 'dep', 're', 'dat', 'muon', 'tim', 'kiem', 'tai nghe', 'dien thoai',
    'may tinh', 'laptop', 'ao', 'quan', 'giay', 'tui', 'balo',
})


def looks_vietnamese(text: str) -> bool:
    """
    Detect Vietnamese text using two complementary signals:
    1. Presence of Vietnamese-specific diacritical characters (ộ, ắ, ề, etc.)
    2. Presence of common Vietnamese words in their unaccented transliterations
    """
    if _VI_DIACRITICS.search(text):
        return True
    normalized = _normalize_vi(text)
    return any(word in normalized for word in _VI_COMMON_WORDS)


# Keep the old name as an alias so existing callers are not broken.
_looks_vietnamese = looks_vietnamese
