"""LLM answer generation with product context."""
from typing import List

SYSTEM_PROMPT = """You are a helpful e-commerce product advisor.
Using the product information provided, give a concise, personalised recommendation.
Always mention specific product names and key features.
If you cannot find relevant products, say so politely and suggest alternatives.
Respond in the same language the user used."""


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


def generate_fallback(query: str, context: str) -> str:
    if not context:
        return "I'm sorry, I couldn't find relevant products for your query."
    lines    = context.split('\n')[:3]
    products = '\n'.join(lines)
    return (
        f"Based on your query '{query}', here are some relevant products:\n\n"
        f"{products}\n\nWould you like more details about any of these?"
    )
