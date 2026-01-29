"""Embedding implementation for Vector Gateway using Nomic embedding endpoint.

This module provides embedding functionality using the Nomic embedding model
served via OpenAI-compatible API (MaaS - Model as a Service).

The Nomic embed-text-v1.5 model produces 768-dimensional vectors.
"""
from __future__ import annotations

import logging
import os
from typing import Iterable, List, Optional

from openai import OpenAI

from .token_utils import estimate_tokens

logger = logging.getLogger(__name__)


def _get_embedding_client() -> OpenAI:
    """Get an OpenAI client configured for the Nomic embedding endpoint."""
    api_key = os.environ.get("NOMIC_API_KEY") or os.environ.get("EMBEDDING_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No API key found. Set NOMIC_API_KEY, EMBEDDING_API_KEY, or OPENAI_API_KEY")

    base_url = os.environ.get("NOMIC_API_URL") or os.environ.get("EMBEDDING_BASE_URL")
    if not base_url:
        raise RuntimeError("No embedding API URL found. Set NOMIC_API_URL or EMBEDDING_BASE_URL")

    return OpenAI(api_key=api_key, base_url=base_url)


def _get_embedding_model() -> str:
    """Get the embedding model name."""
    return os.environ.get("NOMIC_MODEL") or os.environ.get("EMBEDDING_MODEL") or "/mnt/models"


def embed_texts(
    texts: Iterable[str],
    model: Optional[str] = None,
    encoding_format: Optional[str] = None,
    prefer_service: bool = True,  # Kept for API compatibility, not used
) -> List[List[float]]:
    """Generate embeddings for a list of texts using the Nomic embedding endpoint.

    Args:
        texts: Iterable of texts to embed. None values are converted to "".
        model: Model name override. If not specified, uses NOMIC_MODEL env var.
        encoding_format: Optional encoding format (e.g., "float", "base64").
        prefer_service: Kept for API compatibility with rag_core, not used.

    Returns:
        List of embedding vectors, one per input text.
        Empty list if no texts provided.
    """
    clean_texts = [t if t is not None else "" for t in texts]
    if not clean_texts:
        return []

    client = _get_embedding_client()
    chosen_model = model or _get_embedding_model()

    # Conservative batch limits
    max_tokens_per_batch = 3500
    max_input_tokens = 7500

    vectors: List[List[float]] = []
    batch: List[str] = []
    current_tokens = 0

    for text in clean_texts:
        est = estimate_tokens(text)

        # Truncate if single text exceeds limit
        if est > max_input_tokens:
            keep_ratio = max_input_tokens / est
            text = text[: max(1, int(len(text) * keep_ratio))]
            est = estimate_tokens(text)
            logger.debug("Truncated text to %d tokens", est)

        # Flush batch if adding this text would exceed limit
        if batch and current_tokens + est > max_tokens_per_batch:
            kwargs = {"model": chosen_model, "input": batch}
            if encoding_format:
                kwargs["encoding_format"] = encoding_format

            response = client.embeddings.create(**kwargs)
            vectors.extend([item.embedding for item in response.data])
            batch = []
            current_tokens = 0

        batch.append(text)
        current_tokens += est

    # Embed remaining batch
    if batch:
        kwargs = {"model": chosen_model, "input": batch}
        if encoding_format:
            kwargs["encoding_format"] = encoding_format

        response = client.embeddings.create(**kwargs)
        vectors.extend([item.embedding for item in response.data])

    return vectors
