"""Deprecated compatibility wrapper for older imports."""
from .sequence_model_service import get_sequence_model_scores


def get_lstm_scores(user_id: int, top_k: int = 20):
    return get_sequence_model_scores(user_id=user_id, top_k=top_k)
