"""
Evaluation helpers for next-item recommendation models.

The project trains sequence models as next-item classifiers.  For a fair
comparison we use a leave-one-out split per user: the last interaction is the
held-out target and the earlier interactions are used for training/context.
"""
import csv
import json
import math
import zlib
from collections import defaultdict
from pathlib import Path
from struct import pack
from typing import Dict, Iterable, List, Sequence, Tuple

Behavior = Tuple[int, int]
TestCase = Tuple[int, List[int], int]


def leave_one_out_split(
    behaviors: Sequence[Behavior],
    min_train_events: int = 3,
) -> Tuple[List[Behavior], List[TestCase]]:
    """Return train behaviors and test cases using each user's last item."""
    per_user: Dict[int, List[int]] = defaultdict(list)
    for user_id, product_id in behaviors:
        per_user[int(user_id)].append(int(product_id))

    train: List[Behavior] = []
    tests: List[TestCase] = []
    for user_id, seq in per_user.items():
        if len(seq) <= min_train_events:
            train.extend((user_id, pid) for pid in seq)
            continue
        context = seq[:-1]
        target = seq[-1]
        train.extend((user_id, pid) for pid in context)
        tests.append((user_id, context, target))

    return train, tests


def evaluate_model(
    model,
    proc,
    tests: Sequence[TestCase],
    seq_len: int,
    top_k: int = 5,
) -> Dict[str, float]:
    """
    Compute next-item metrics for one trained model.

    With one relevant target per test row:
      - accuracy@k == hit-rate@k
      - precision@k is 1/k when the target appears in the top-k, else 0
      - recall@k is 1 when hit, else 0
    """
    if not tests:
        return _empty_metrics(top_k)

    import torch

    device = next(model.parameters()).device
    hits_at_1 = hits_at_k = 0
    precision_sum = recall_sum = f1_sum = mrr_sum = ndcg_sum = 0.0
    evaluated = 0

    model.eval()
    with torch.no_grad():
        for _, context, target_pid in tests:
            target_idx = proc.encode(target_pid)
            if target_idx <= 0:
                continue

            encoded = [proc.encode(pid) for pid in context if proc.encode(pid)]
            if not encoded:
                continue

            x_values = proc.pad_sequence(encoded, seq_len)
            x = torch.tensor([x_values], dtype=torch.long, device=device)

            if getattr(model, 'mask_token', None) is not None:
                x[0, -1] = model.mask_token
                logits = model(x)[0, -1]
            else:
                logits = model(x)[0]

            logits = logits.clone()
            logits[0] = float('-inf')
            if getattr(model, 'mask_token', None) is not None and model.mask_token < logits.numel():
                logits[model.mask_token] = float('-inf')

            _, indices = torch.topk(logits, k=min(top_k, logits.numel()))
            ranked = indices.tolist()
            evaluated += 1

            if ranked and ranked[0] == target_idx:
                hits_at_1 += 1

            if target_idx in ranked:
                rank = ranked.index(target_idx) + 1
                hits_at_k += 1
                precision = 1.0 / top_k
                recall = 1.0
                precision_sum += precision
                recall_sum += recall
                f1_sum += (2 * precision * recall) / (precision + recall)
                mrr_sum += 1.0 / rank
                ndcg_sum += 1.0 / math.log2(rank + 1)

    if evaluated == 0:
        return _empty_metrics(top_k)

    return {
        'test_cases': evaluated,
        'accuracy@1': round(hits_at_1 / evaluated, 6),
        f'accuracy@{top_k}': round(hits_at_k / evaluated, 6),
        f'precision@{top_k}': round(precision_sum / evaluated, 6),
        f'recall@{top_k}': round(recall_sum / evaluated, 6),
        f'f1@{top_k}': round(f1_sum / evaluated, 6),
        f'mrr@{top_k}': round(mrr_sum / evaluated, 6),
        f'ndcg@{top_k}': round(ndcg_sum / evaluated, 6),
    }


def save_metrics(metrics: Dict[str, dict], output_dir: Path) -> None:
    """Persist metrics as JSON and CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / 'model_metrics.json').open('w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    fields = ['model']
    for values in metrics.values():
        for key in values:
            if key not in fields:
                fields.append(key)

    with (output_dir / 'model_metrics.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for model_name, values in metrics.items():
            row = {'model': model_name}
            row.update(values)
            writer.writerow(row)


def render_metric_chart(
    metrics: Dict[str, dict],
    metric: str,
    output_path: Path,
    title: str,
) -> None:
    """Render a small PNG bar chart without third-party plotting packages."""
    values = [(name.upper(), float(row.get(metric, 0.0) or 0.0)) for name, row in metrics.items()]
    _draw_bar_chart(values, output_path, title, metric)


def _empty_metrics(top_k: int) -> Dict[str, float]:
    return {
        'test_cases': 0,
        'accuracy@1': 0.0,
        f'accuracy@{top_k}': 0.0,
        f'precision@{top_k}': 0.0,
        f'recall@{top_k}': 0.0,
        f'f1@{top_k}': 0.0,
        f'mrr@{top_k}': 0.0,
        f'ndcg@{top_k}': 0.0,
    }


_FONT = {
    ' ': ['000', '000', '000', '000', '000', '000', '000'],
    '.': ['000', '000', '000', '000', '000', '110', '110'],
    '@': ['01110', '10001', '10111', '10101', '10111', '10000', '01111'],
    '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],
    '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
    '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
    '2': ['01110', '10001', '00001', '00010', '00100', '01000', '11111'],
    '3': ['11110', '00001', '00001', '01110', '00001', '00001', '11110'],
    '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
    '5': ['11111', '10000', '10000', '11110', '00001', '00001', '11110'],
    '6': ['01110', '10000', '10000', '11110', '10001', '10001', '01110'],
    '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
    '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],
    '9': ['01110', '10001', '10001', '01111', '00001', '00001', '01110'],
}

for _ch, _rows in {
    'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
    'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
    'C': ['01111', '10000', '10000', '10000', '10000', '10000', '01111'],
    'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
    'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
    'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
    'G': ['01111', '10000', '10000', '10011', '10001', '10001', '01111'],
    'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
    'I': ['11111', '00100', '00100', '00100', '00100', '00100', '11111'],
    'J': ['00111', '00010', '00010', '00010', '00010', '10010', '01100'],
    'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
    'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
    'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
    'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
    'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
    'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
    'Q': ['01110', '10001', '10001', '10001', '10101', '10010', '01101'],
    'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
    'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
    'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
    'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
    'W': ['10001', '10001', '10001', '10101', '10101', '10101', '01010'],
    'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
    'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
    'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
}.items():
    _FONT[_ch] = _rows
    _FONT[_ch.lower()] = _rows


def _draw_bar_chart(values: List[Tuple[str, float]], output_path: Path, title: str, metric: str) -> None:
    width, height = 1100, 680
    bg = (248, 250, 252)
    ink = (15, 23, 42)
    grid = (203, 213, 225)
    colors = [
        (37, 99, 235), (5, 150, 105), (217, 119, 6), (220, 38, 38),
        (124, 58, 237), (8, 145, 178), (219, 39, 119),
    ]
    img = [[bg for _ in range(width)] for _ in range(height)]

    _text(img, 50, 28, title.upper(), ink, scale=4)
    _text(img, 50, 78, metric.upper(), (71, 85, 105), scale=3)

    left, top, right, bottom = 90, 135, 1040, 560
    _line(img, left, top, left, bottom, ink)
    _line(img, left, bottom, right, bottom, ink)

    for step in range(0, 6):
        y = bottom - int((bottom - top) * step / 5)
        _line(img, left, y, right, y, grid)
        _text(img, 25, y - 9, f'{step / 5:.1f}', (71, 85, 105), scale=2)

    if not values:
        _text(img, 380, 320, 'NO DATA', ink, scale=5)
        _write_png(output_path, img)
        return

    bar_gap = 22
    slot = (right - left) / len(values)
    bar_w = max(34, int(slot - bar_gap))
    for i, (label, value) in enumerate(values):
        value = max(0.0, min(1.0, value))
        x0 = int(left + i * slot + (slot - bar_w) / 2)
        x1 = x0 + bar_w
        y0 = bottom - int((bottom - top) * value)
        color = colors[i % len(colors)]
        _rect(img, x0, y0, x1, bottom - 1, color)
        _text(img, x0 + 2, y0 - 26, f'{value:.3f}', ink, scale=2)
        short = label[:8]
        _text(img, x0 + max(0, (bar_w - len(short) * 12) // 2), bottom + 18, short, ink, scale=2)

    _write_png(output_path, img)


def _rect(img, x0, y0, x1, y1, color):
    h, w = len(img), len(img[0])
    for y in range(max(0, y0), min(h, y1 + 1)):
        for x in range(max(0, x0), min(w, x1 + 1)):
            img[y][x] = color


def _line(img, x0, y0, x1, y1, color):
    if y0 == y1:
        _rect(img, min(x0, x1), y0, max(x0, x1), y0, color)
    elif x0 == x1:
        _rect(img, x0, min(y0, y1), x0, max(y0, y1), color)


def _text(img, x, y, text, color, scale=2):
    cursor = x
    for ch in text:
        rows = _FONT.get(ch, _FONT.get(ch.upper(), _FONT[' ']))
        for row_i, row in enumerate(rows):
            for col_i, bit in enumerate(row):
                if bit == '1':
                    _rect(
                        img,
                        cursor + col_i * scale,
                        y + row_i * scale,
                        cursor + (col_i + 1) * scale - 1,
                        y + (row_i + 1) * scale - 1,
                        color,
                    )
        cursor += (len(rows[0]) + 1) * scale


def _write_png(path: Path, img) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    height = len(img)
    width = len(img[0])
    raw = bytearray()
    for row in img:
        raw.append(0)
        for r, g, b in row:
            raw.extend((r, g, b))

    def chunk(tag, data):
        payload = tag + data
        return pack('>I', len(data)) + payload + pack('>I', zlib.crc32(payload) & 0xFFFFFFFF)

    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(bytes(raw), level=9))
    png += chunk(b'IEND', b'')
    path.write_bytes(png)
