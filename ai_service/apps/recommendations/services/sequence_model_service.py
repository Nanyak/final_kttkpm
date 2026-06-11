"""
Sequence-model inference service.

Loads the active next-item model (rnn / lstm / bilstm / gru / narm / sasrec /
bert4rec) and returns next-item probability scores for a user's recent
behaviour sequence.

The active model is controlled by the ACTIVE_MODEL Django setting.
"""
from functools import lru_cache
from pathlib import Path
from typing import Dict

import torch


@lru_cache(maxsize=1)
def _load_model():
    from django.conf import settings
    import importlib

    model_type = getattr(settings, 'ACTIVE_MODEL', 'gru').lower()
    model_dir = Path(settings.MODEL_DIR) / model_type

    weight_file = model_dir / f'{model_type}.pt'
    if not weight_file.exists():
        return None, None, None

    trainer = importlib.import_module(f'ml.{model_type}.trainer')
    return trainer.load(model_dir)


def get_sequence_model_scores(user_id: int, top_k: int = 20) -> Dict[int, float]:
    """
    Returns {product_id: normalised_score} for the top_k most likely
    next interactions predicted by the active sequence model.
    """
    model, proc, meta = _load_model()
    if model is None:
        return {}

    from apps.behavior.models import UserBehavior

    seq_len = meta.get('seq_len', 20)

    qs = (
        UserBehavior.objects
        .filter(user_id=user_id)
        .order_by('timestamp')
        .values_list('product__product_id', flat=True)
    )
    raw_seq = list(qs)
    if not raw_seq:
        return {}

    encoded_seq = [proc.encode(pid) for pid in raw_seq if proc.encode(pid)]
    if not encoded_seq:
        return {}

    if len(encoded_seq) >= seq_len:
        encoded_seq = encoded_seq[-seq_len:]
    else:
        encoded_seq = [0] * (seq_len - len(encoded_seq)) + encoded_seq

    device = next(model.parameters()).device
    x = torch.tensor([encoded_seq], dtype=torch.long).to(device)

    model_type = meta.get('model_type', getattr(model, 'model_type', 'gru'))

    with torch.no_grad():
        if model_type == 'bert4rec':
            x[0, -1] = model.mask_token
            output = model(x)
            probs = torch.softmax(output[0, -1], dim=0)
        else:
            output = model(x)
            probs = torch.softmax(output[0], dim=0)

    scores: Dict[int, float] = {}
    topk_vals, topk_idxs = torch.topk(probs, k=min(top_k, probs.shape[0]))
    for val, idx in zip(topk_vals.tolist(), topk_idxs.tolist()):
        pid = proc.decode(idx)
        if pid > 0:
            scores[pid] = val

    if scores:
        mx = max(scores.values())
        if mx > 0:
            scores = {k: v / mx for k, v in scores.items()}

    return scores
