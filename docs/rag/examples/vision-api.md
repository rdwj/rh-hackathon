# Granite Vision 3.2 2B - Vision API

This document shows how to use the Granite Vision 3.2 2B model via the Red Hat AI MaaS endpoint.

## Configuration

```bash
GRANITE_VISION_API_URL=https://granite-vision-3-2-2b-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443
GRANITE_VISION_MODEL=granite-vision-3-2
GRANITE_VISION_API_KEY=<your-api-key>
```

## API Endpoint

```
POST {GRANITE_VISION_API_URL}/v1/chat/completions
```

## Image Analysis Request

The vision model uses the OpenAI-compatible chat completions API with image content.

### Using Base64 Encoded Image

For images stored locally, encode them as base64 and include in the request:

#### Step 1: Encode Image

```bash
# Encode image to base64
IMAGE_BASE64=$(base64 -i /path/to/image.png)
```

#### Step 2: Create Request File

Due to the large size of base64-encoded images, use a request file:

```bash
# Create request JSON file
IMAGE_BASE64=$(base64 -i /path/to/image.png)

cat > /tmp/vision-request.json << EOF
{
  "model": "granite-vision-3-2",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image in detail. What do you see?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,${IMAGE_BASE64}"}}
      ]
    }
  ],
  "max_tokens": 500
}
EOF
```

#### Step 3: Send Request

```bash
curl -s -X POST 'https://granite-vision-3-2-2b-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/chat/completions' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d @/tmp/vision-request.json | jq .
```

### Response

```json
{
  "id": "chatcmpl-fd90581597f84653bc751c1291666297",
  "object": "chat.completion",
  "created": 1769728061,
  "model": "granite-vision-3-2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "reasoning_content": null,
        "content": "A cleverly rendered VR image showcases a domestic scene where two clothes washers, an eco-friendly EcoAneuse model with the capability to handle 100 cycles at 40% of the usual load, and a cutting-edge Twin R-AII described as \"Eco-friendly & powerful, Level D energy efficiency & 90% stable\" are equipped with colorful industrial electronic control boards inserted into their frames. These washing machines are shown against a textured floor, with scattered bags mimicking floor debris, all through which a well-constructed power cord is noticeable. They are connected with snaking tubes displayed at the base, encapsulating a concealment beneath their deceptive external facades. The models EcoAneuse and Twin R-AII are prominently marked at the top of the image.",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": null
    }
  ],
  "usage": {
    "prompt_tokens": 7431,
    "total_tokens": 7629,
    "completion_tokens": 198,
    "prompt_tokens_details": null
  },
  "prompt_logprobs": null,
  "kv_transfer_params": null
}
```

## Using Image URL

If the image is accessible via URL:

```bash
curl -s -X POST 'https://granite-vision-3-2-2b-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/chat/completions' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "granite-vision-3-2",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "What is in this image?"},
          {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
      }
    ],
    "max_tokens": 300
  }'
```

## Specific Analysis Prompts

### Extract Text from Image (OCR)

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Extract all text visible in this image. Return only the text, nothing else."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
      ]
    }
  ]
}
```

### Describe for Search Indexing

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image for a search index. Include: subjects, setting, time period (if apparent), any text visible, and notable details. Be concise but comprehensive."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
      ]
    }
  ]
}
```

### Historical Photo Analysis

```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "This is a historical photograph. Describe what you see, estimate the time period, and note any cultural or historical significance."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
      ]
    }
  ]
}
```

## Python Example

```python
import httpx
import base64
import os
from pathlib import Path

GRANITE_VISION_API_URL = os.getenv("GRANITE_VISION_API_URL")
GRANITE_VISION_API_KEY = os.getenv("GRANITE_VISION_API_KEY")
GRANITE_VISION_MODEL = os.getenv("GRANITE_VISION_MODEL", "granite-vision-3-2")

async def analyze_image(
    image_path: str = None,
    image_url: str = None,
    prompt: str = "Describe this image in detail."
) -> str:
    """
    Analyze an image using Granite Vision.

    Args:
        image_path: Path to local image file
        image_url: URL of remote image
        prompt: Question or instruction about the image

    Returns:
        Model's description/analysis of the image
    """
    if image_path:
        # Read and encode local image
        image_data = Path(image_path).read_bytes()
        base64_image = base64.b64encode(image_data).decode("utf-8")

        # Determine MIME type
        suffix = Path(image_path).suffix.lower()
        mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif"}
        mime_type = mime_types.get(suffix, "image/png")

        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
        }
    elif image_url:
        image_content = {
            "type": "image_url",
            "image_url": {"url": image_url}
        }
    else:
        raise ValueError("Must provide either image_path or image_url")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{GRANITE_VISION_API_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GRANITE_VISION_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GRANITE_VISION_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            image_content,
                        ]
                    }
                ],
                "max_tokens": 500,
            },
            timeout=120.0,  # Vision requests can take longer
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

# Example usage
import asyncio

# Analyze local image
description = asyncio.run(analyze_image(
    image_path="/path/to/photo.png",
    prompt="Describe this historical photograph. Who is in it? What are they doing?"
))
print(description)
```

## Integration with RAG

Use vision analysis to enrich image artifacts with searchable text:

```python
async def enrich_image_for_rag(image_path: str, artifact_metadata: dict) -> dict:
    """
    Generate searchable description for an image artifact.

    Returns metadata enriched with AI-generated description.
    """
    # Generate description for search
    description = await analyze_image(
        image_path=image_path,
        prompt="""Analyze this image for a cultural heritage archive.
        Describe: subjects, setting, apparent time period, visible text,
        and any culturally significant elements. Be detailed but concise."""
    )

    # Add to metadata
    artifact_metadata["ai_description"] = description
    artifact_metadata["searchable_text"] = description

    return artifact_metadata
```

## Supported Image Formats

| Format | MIME Type | Notes |
|--------|-----------|-------|
| PNG | image/png | Best for screenshots, diagrams |
| JPEG | image/jpeg | Best for photographs |
| GIF | image/gif | Static only (first frame) |
| WebP | image/webp | May work, test first |

## Error Handling

Common errors:

| Status | Meaning | Solution |
|--------|---------|----------|
| 401 | Invalid API key | Check `GRANITE_VISION_API_KEY` |
| 400 | Invalid image | Check base64 encoding, MIME type |
| 413 | Image too large | Resize image before encoding |
| 504 | Timeout | Increase timeout, image may be too complex |

## Performance Notes

- Vision requests take longer than text-only requests (10-30 seconds typical)
- Large images consume more tokens (see `prompt_tokens` in response)
- Consider resizing large images before analysis
- Base64 encoding increases payload size by ~33%

## Notes

- The endpoint is OpenAI Vision-compatible (`/v1/chat/completions`)
- Model name is `granite-vision-3-2`
- Images can be base64-encoded or referenced by URL
- Token usage includes image tokens (can be high for large images)
- Useful for enriching image artifacts with searchable descriptions
