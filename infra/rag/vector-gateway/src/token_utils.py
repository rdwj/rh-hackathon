"""Lightweight token estimation utilities.

We only need approximate counts to enforce prompt/context budgets before
calling an LLM. If `tiktoken` is available we use it; otherwise we fall back to
a simple heuristic of ~4 characters per token.
"""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=4)
def _get_encoding(encoding_name: str):
    """Get tiktoken encoding, cached for performance."""
    try:
        import tiktoken
        return tiktoken.get_encoding(encoding_name)
    except Exception:
        return None


def estimate_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Estimate the number of tokens in a text string.

    Uses tiktoken if available for accurate counts, otherwise falls back
    to a heuristic of ~4 characters per token.
    """
    if not text:
        return 1

    enc = _get_encoding(encoding_name)
    if enc is not None:
        try:
            return len(enc.encode(text))
        except Exception:
            pass

    # Heuristic fallback: average 4 characters per token for English-ish text.
    return max(1, len(text) // 4)
