# Llama-4-Scout-17B - Chat Completions API

This document shows how to use the Llama-4-Scout-17B model via the Red Hat AI MaaS endpoint.

## Configuration

```bash
LLAMA_API_URL=https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443
LLAMA_MODEL=llama-4-scout-17b-16e-w4a16
LLAMA_API_KEY=<your-api-key>
```

## API Endpoint

```
POST {LLAMA_API_URL}/v1/chat/completions
```

## Basic Chat Request

### curl Command

```bash
curl -s -X POST 'https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/chat/completions' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "llama-4-scout-17b-16e-w4a16",
    "messages": [
      {"role": "user", "content": "Hello, respond with just one sentence."}
    ],
    "max_tokens": 100
  }'
```

### Response

```json
{
  "id": "chatcmpl-f4ef5290b4cc47758616234134c06f07",
  "object": "chat.completion",
  "created": 1769726837,
  "model": "llama-4-scout-17b-16e-w4a16",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "reasoning_content": null,
        "content": "Hello!",
        "tool_calls": []
      },
      "logprobs": null,
      "finish_reason": "stop",
      "stop_reason": null
    }
  ],
  "usage": {
    "prompt_tokens": 18,
    "total_tokens": 21,
    "completion_tokens": 3,
    "prompt_tokens_details": null
  },
  "prompt_logprobs": null,
  "kv_transfer_params": null
}
```

## Chat with System Prompt

### curl Command

```bash
curl -s -X POST 'https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/chat/completions' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "llama-4-scout-17b-16e-w4a16",
    "messages": [
      {"role": "system", "content": "You are The Griot, an AI oral historian. Answer questions based only on provided context."},
      {"role": "user", "content": "What stories do you have about the Great Migration?"}
    ],
    "max_tokens": 200
  }'
```

## Tool Calling (Function Calling)

The model supports OpenAI-compatible tool calling, which is essential for the Griot Agent.

### curl Command

```bash
curl -s -X POST 'https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/chat/completions' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "llama-4-scout-17b-16e-w4a16",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant. Use the search tool when asked about information."},
      {"role": "user", "content": "Search for information about the Great Migration."}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "rag_search",
          "description": "Search the document collection for relevant information",
          "parameters": {
            "type": "object",
            "properties": {
              "query": {"type": "string", "description": "The search query"},
              "top_k": {"type": "integer", "description": "Number of results to return", "default": 5}
            },
            "required": ["query"]
          }
        }
      }
    ],
    "max_tokens": 200
  }'
```

### Response (Tool Call)

```json
{
  "id": "chatcmpl-d4794dc0897c4a55b4b627a3625dc039",
  "object": "chat.completion",
  "created": 1769726846,
  "model": "llama-4-scout-17b-16e-w4a16",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "reasoning_content": null,
        "content": null,
        "tool_calls": [
          {
            "id": "chatcmpl-tool-3cf5971e60944798a833d65bda895561",
            "type": "function",
            "function": {
              "name": "rag_search",
              "arguments": "{\"query\": \"Great Migration\"}"
            }
          }
        ]
      },
      "logprobs": null,
      "finish_reason": "tool_calls",
      "stop_reason": null
    }
  ],
  "usage": {
    "prompt_tokens": 204,
    "total_tokens": 213,
    "completion_tokens": 9,
    "prompt_tokens_details": null
  },
  "prompt_logprobs": null,
  "kv_transfer_params": null
}
```

**Key observations:**
- `content` is `null` when a tool call is made
- `tool_calls` array contains the function call details
- `finish_reason` is `"tool_calls"` (not `"stop"`)
- `arguments` is a JSON string that needs to be parsed

## Handling Tool Call Results

After receiving a tool call, execute the tool and send the result back:

```bash
curl -s -X POST 'https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1/chat/completions' \
  -H 'Authorization: Bearer <your-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "llama-4-scout-17b-16e-w4a16",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Search for information about the Great Migration."},
      {"role": "assistant", "content": null, "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "rag_search", "arguments": "{\"query\": \"Great Migration\"}"}}]},
      {"role": "tool", "tool_call_id": "call_123", "content": "Found 3 documents: 1) Interview with Mary Johnson (1985) discusses her family leaving Mississippi in 1942. 2) Oral history from James Williams describes the train journey north. 3) Photo collection showing arrival in Chicago."}
    ],
    "max_tokens": 300
  }'
```

## Python Example

```python
import httpx
import os

LLAMA_API_URL = os.getenv("LLAMA_API_URL")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama-4-scout-17b-16e-w4a16")

async def chat(messages: list[dict], tools: list[dict] = None) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LLAMA_API_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {LLAMA_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": LLAMA_MODEL,
                "messages": messages,
                "tools": tools,
                "max_tokens": 500,
            },
            timeout=60.0,
        )
        response.raise_for_status()
        return response.json()

# Example usage
import asyncio

messages = [
    {"role": "user", "content": "Hello!"}
]
result = asyncio.run(chat(messages))
print(result["choices"][0]["message"]["content"])
```

## Error Handling

Common errors:

| Status | Meaning | Solution |
|--------|---------|----------|
| 401 | Invalid API key | Check `LLAMA_API_KEY` |
| 429 | Rate limited | Add retry with backoff |
| 500 | Server error | Retry or contact admin |
| 503 | Service unavailable | Model may be scaling up, retry |

## Notes

- The endpoint is OpenAI-compatible (`/v1/chat/completions`)
- Tool calling works correctly with `finish_reason: "tool_calls"`
- Model name must match exactly: `llama-4-scout-17b-16e-w4a16`
- Add `/v1` to the base URL for API calls
