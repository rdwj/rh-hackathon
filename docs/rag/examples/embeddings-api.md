# Nomic Embed Text v1.5 - Embeddings API

This document shows how to use the Nomic Embed Text v1.5 model via the Red Hat AI MaaS endpoint.

## Configuration

```bash
NOMIC_API_URL=https://nomic-embed-text-v1-5-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443
NOMIC_MODEL=/mnt/models
NOMIC_API_KEY=<your-api-key>
```

## API Endpoint

```
POST {NOMIC_API_URL}/v1/embeddings
```

## Single Text Embedding

### curl Command

```bash
curl -s -X POST 'https://nomic-embed-text-v1-5-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/embeddings' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": "The Great Migration brought many families from Mississippi to northern cities.",
    "model": "/mnt/models"
  }'
```

### Response

```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "embedding": [
        0.027854342,
        0.039076407,
        -0.2092265,
        -0.054905422,
        -0.020246964,
        ... (768 dimensions total)
      ],
      "index": 0
    }
  ],
  "model": "/mnt/models",
  "usage": {
    "prompt_tokens": 14,
    "total_tokens": 14
  }
}
```

### Response Summary (using jq)

```bash
curl -s -X POST 'https://nomic-embed-text-v1-5-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/embeddings' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{"input": "The Great Migration brought many families from Mississippi to northern cities.", "model": "/mnt/models"}' \
  | jq '{
    model: .model,
    usage: .usage,
    embedding_dims: (.data[0].embedding | length),
    first_5_dims: (.data[0].embedding[:5])
  }'
```

Output:

```json
{
  "model": "/mnt/models",
  "usage": {
    "prompt_tokens": 14,
    "total_tokens": 14
  },
  "embedding_dims": 768,
  "first_5_dims": [
    0.027854342,
    0.039076407,
    -0.2092265,
    -0.054905422,
    -0.020246964
  ]
}
```

## Batch Embedding (Multiple Texts)

You can embed multiple texts in a single request by passing an array to `input`.

### curl Command

```bash
curl -s -X POST 'https://nomic-embed-text-v1-5-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/embeddings' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "input": [
      "First document about oral history.",
      "Second document about cultural preservation.",
      "Third document about family traditions."
    ],
    "model": "/mnt/models"
  }'
```

### Response Summary

```bash
curl -s -X POST 'https://nomic-embed-text-v1-5-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/embeddings' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{"input": ["First document about oral history.", "Second document about cultural preservation."], "model": "/mnt/models"}' \
  | jq '{
    model: .model,
    usage: .usage,
    num_embeddings: (.data | length),
    dims: [.data[].embedding | length]
  }'
```

Output:

```json
{
  "model": "/mnt/models",
  "usage": {
    "prompt_tokens": 16,
    "total_tokens": 16
  },
  "num_embeddings": 2,
  "dims": [
    768,
    768
  ]
}
```

## Python Example

```python
import httpx
import os
from typing import Union

NOMIC_API_URL = os.getenv("NOMIC_API_URL")
NOMIC_API_KEY = os.getenv("NOMIC_API_KEY")
NOMIC_MODEL = os.getenv("NOMIC_MODEL", "/mnt/models")

async def embed(texts: Union[str, list[str]]) -> list[list[float]]:
    """
    Generate embeddings for one or more texts.

    Args:
        texts: Single string or list of strings to embed

    Returns:
        List of embedding vectors (768 dimensions each)
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOMIC_API_URL}/v1/embeddings",
            headers={
                "Authorization": f"Bearer {NOMIC_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "input": texts,
                "model": NOMIC_MODEL,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()

        # Return embeddings sorted by index
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]

# Example usage
import asyncio

# Single text
embedding = asyncio.run(embed("Hello world"))
print(f"Dimensions: {len(embedding[0])}")  # 768

# Batch
embeddings = asyncio.run(embed(["Text one", "Text two", "Text three"]))
print(f"Count: {len(embeddings)}, Dims: {len(embeddings[0])}")  # 3, 768
```

## Similarity Search Example

```python
import numpy as np

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

async def find_similar(query: str, documents: list[str], top_k: int = 3):
    """Find most similar documents to a query."""
    # Embed query and documents together for efficiency
    all_texts = [query] + documents
    embeddings = await embed(all_texts)

    query_embedding = embeddings[0]
    doc_embeddings = embeddings[1:]

    # Calculate similarities
    similarities = [
        (i, cosine_similarity(query_embedding, doc_emb))
        for i, doc_emb in enumerate(doc_embeddings)
    ]

    # Sort by similarity (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Return top-k results
    return [
        {"document": documents[i], "score": score}
        for i, score in similarities[:top_k]
    ]

# Example
documents = [
    "The Great Migration was a movement of African Americans from the South.",
    "Jazz music originated in New Orleans in the early 20th century.",
    "Many families left Mississippi seeking better opportunities in the North.",
]

results = asyncio.run(find_similar("migration from Mississippi", documents))
for r in results:
    print(f"{r['score']:.4f}: {r['document'][:50]}...")
```

## Model Details

| Property | Value |
|----------|-------|
| Model | Nomic Embed Text v1.5 |
| Dimensions | 768 |
| Max tokens | ~8192 |
| Similarity metric | Cosine similarity recommended |
| Multilingual | Yes (good support) |

## Integration with Milvus

When storing embeddings in Milvus, use these settings:

```python
from pymilvus import CollectionSchema, FieldSchema, DataType

# Schema for Milvus collection
fields = [
    FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),  # Nomic = 768
]
schema = CollectionSchema(fields=fields)
```

## Error Handling

Common errors:

| Status | Meaning | Solution |
|--------|---------|----------|
| 401 | Invalid API key | Check `NOMIC_API_KEY` |
| 400 | Invalid input | Ensure `input` is string or array of strings |
| 413 | Payload too large | Reduce batch size or text length |
| 429 | Rate limited | Add retry with backoff |

## Notes

- The endpoint is OpenAI-compatible (`/v1/embeddings`)
- Returns 768-dimensional vectors
- Model name is `/mnt/models` (not the HuggingFace name)
- Batch embedding is more efficient than single requests
- Vectors are normalized (unit length) for cosine similarity
