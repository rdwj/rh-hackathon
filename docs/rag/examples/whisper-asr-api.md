# Whisper ASR - Speech Recognition API

This document shows how to use the Whisper ASR (Automatic Speech Recognition) service for transcribing audio files.

## Configuration

```bash
WHISPER_ASR_API_URL=https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org
WHISPER_ASR_API_DOCS=https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/docs
```

**Note:** This endpoint does not require an API key.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/asr` | POST | Transcribe audio file |
| `/asr/{job_id}` | GET | Get async job status |
| `/detect-language` | POST | Detect language in audio |

## Transcribe Audio

### Basic Transcription (Plain Text)

```bash
curl -s -X POST 'https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/asr?output=txt' \
  -F 'audio_file=@/path/to/audio.wav'
```

#### Response

```
Hello, this is a test of the whisper speech recognition system.
The Great Migration brought many African-American families from the south to northern cities.
```

### JSON Output (with timestamps and word-level detail)

```bash
curl -s -X POST 'https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/asr?output=json' \
  -F 'audio_file=@/path/to/audio.wav' | jq .
```

#### Response

```json
{
  "segments": [
    {
      "start": 0.031,
      "end": 3.375,
      "text": " Hello, this is a test of the whisper speech recognition system.",
      "words": [
        {
          "word": "Hello,",
          "start": 0.031,
          "end": 0.394,
          "score": 0.934
        },
        {
          "word": "this",
          "start": 0.857,
          "end": 1.018,
          "score": 0.859
        }
        // ... more words
      ]
    },
    {
      "start": 3.737,
      "end": 8.37,
      "text": "The Great Migration brought many African-American families from the south to northern cities.",
      "words": [
        // ... word-level timestamps
      ]
    }
  ],
  "word_segments": [
    // Flat list of all words with timestamps
  ],
  "language": "en"
}
```

### SRT Subtitle Format

```bash
curl -s -X POST 'https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/asr?output=srt' \
  -F 'audio_file=@/path/to/audio.wav'
```

#### Response

```
1
00:00:00,031 --> 00:00:03,375
Hello, this is a test of the whisper speech recognition system.

2
00:00:03,737 --> 00:00:08,370
The Great Migration brought many African-American families from the south to northern cities.
```

### VTT Subtitle Format

```bash
curl -s -X POST 'https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/asr?output=vtt' \
  -F 'audio_file=@/path/to/audio.wav'
```

## Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output` | string | `txt` | Output format: `txt`, `json`, `srt`, `vtt`, `tsv` |
| `task` | string | `transcribe` | Task: `transcribe` or `translate` (to English) |
| `language` | string | auto | Source language code (e.g., `en`, `es`, `fr`) |
| `encode` | boolean | `true` | Pre-process audio through ffmpeg |
| `diarize` | boolean | `false` | Enable speaker diarization |
| `min_speakers` | integer | - | Minimum speakers (for diarization) |
| `max_speakers` | integer | - | Maximum speakers (for diarization) |
| `initial_prompt` | string | - | Prompt to guide transcription style |
| `async_job` | boolean | `false` | Run as async job |

## Speaker Diarization

For interviews and multi-speaker recordings:

```bash
curl -s -X POST 'https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/asr?output=json&diarize=true&min_speakers=2&max_speakers=4' \
  -F 'audio_file=@/path/to/interview.wav'
```

## Language Detection

Detect the language of an audio file without full transcription:

```bash
curl -s -X POST 'https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/detect-language' \
  -F 'audio_file=@/path/to/audio.wav' | jq .
```

#### Response

```json
{
  "detected_language": "english",
  "language_code": "en",
  "confidence": 1.0
}
```

## Async Jobs (Long Audio)

For long audio files, use async processing:

### Submit Job

```bash
curl -s -X POST 'https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/asr?async_job=true&output=json' \
  -F 'audio_file=@/path/to/long-audio.wav'
```

#### Response

```json
{
  "job_id": "abc123",
  "status": "pending"
}
```

### Check Job Status

```bash
curl -s 'https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/asr/abc123' | jq .
```

## Supported Languages

The model supports 99 languages including:

| Code | Language | Code | Language |
|------|----------|------|----------|
| `en` | English | `es` | Spanish |
| `fr` | French | `de` | German |
| `it` | Italian | `pt` | Portuguese |
| `zh` | Chinese | `ja` | Japanese |
| `ko` | Korean | `ar` | Arabic |
| `hi` | Hindi | `ru` | Russian |

Full list available in the [OpenAPI spec](https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org/openapi.json).

## Supported Audio Formats

- WAV (recommended)
- MP3
- M4A
- FLAC
- OGG
- Most formats supported by ffmpeg

## Python Example

```python
import httpx
import os
from pathlib import Path

WHISPER_API_URL = os.getenv("WHISPER_ASR_API_URL", "https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org")

async def transcribe(
    audio_path: str,
    output: str = "json",
    language: str = None,
    diarize: bool = False,
) -> dict | str:
    """
    Transcribe an audio file using Whisper ASR.

    Args:
        audio_path: Path to audio file
        output: Output format (txt, json, srt, vtt, tsv)
        language: Source language code (auto-detect if None)
        diarize: Enable speaker diarization

    Returns:
        Transcription result (dict for json, str for others)
    """
    params = {"output": output}
    if language:
        params["language"] = language
    if diarize:
        params["diarize"] = "true"

    async with httpx.AsyncClient() as client:
        with open(audio_path, "rb") as f:
            response = await client.post(
                f"{WHISPER_API_URL}/asr",
                params=params,
                files={"audio_file": (Path(audio_path).name, f)},
                timeout=300.0,  # 5 minutes for long audio
            )
        response.raise_for_status()

        if output == "json":
            return response.json()
        return response.text

async def detect_language(audio_path: str) -> dict:
    """Detect the language of an audio file."""
    async with httpx.AsyncClient() as client:
        with open(audio_path, "rb") as f:
            response = await client.post(
                f"{WHISPER_API_URL}/detect-language",
                files={"audio_file": (Path(audio_path).name, f)},
                timeout=60.0,
            )
        response.raise_for_status()
        return response.json()

# Example usage
import asyncio

# Basic transcription
result = asyncio.run(transcribe("/path/to/audio.wav", output="json"))
print(f"Detected language: {result['language']}")
for segment in result["segments"]:
    print(f"[{segment['start']:.1f}s] {segment['text']}")

# Language detection
lang = asyncio.run(detect_language("/path/to/audio.wav"))
print(f"Language: {lang['detected_language']} ({lang['confidence']:.0%})")
```

## Integration with RAG

For the Griot project, transcribe audio artifacts and ingest the text:

```python
async def process_audio_artifact(audio_path: str, artifact_id: str) -> str:
    """
    Transcribe audio and prepare for RAG ingestion.

    Returns the transcript text for vector embedding.
    """
    # Transcribe with timestamps for citation
    result = await transcribe(audio_path, output="json")

    # Extract plain text
    transcript = " ".join(seg["text"].strip() for seg in result["segments"])

    # Store segment timestamps in MongoDB for citation linking
    # (artifact_id -> segments with timestamps)

    return transcript
```

## Error Handling

| Status | Meaning | Solution |
|--------|---------|----------|
| 400 | Invalid audio file | Check file format, ensure audio has content |
| 413 | File too large | Use async_job for large files |
| 422 | Validation error | Check parameter types |
| 500 | Processing error | Retry or check audio file integrity |

## Performance Notes

- Processing time is roughly proportional to audio length
- Short clips (< 30s): 2-5 seconds
- Long audio (> 10 min): Use `async_job=true`
- WAV format is fastest (no transcoding needed)
- Diarization adds processing time

## Notes

- No API key required for this endpoint
- Audio is processed through ffmpeg by default (`encode=true`)
- Word-level timestamps include confidence scores
- The `translate` task converts any language to English
- Speaker diarization identifies different speakers in recordings
