# RAG Ingestion Scripts

Utility scripts for ingesting content into the Griot RAG system.

## Scripts

### ingest-audio.py

Ingests audio files through the full pipeline:

```
Audio File → Whisper ASR → Chunker Service → Vector Gateway
```

**Usage:**

```bash
# Install dependencies
pip install -r requirements.txt

# Dry run (transcribe and chunk, skip vector ingestion)
python ingest-audio.py /path/to/audio.mp3 --dry-run

# Full ingestion (requires Milvus)
python ingest-audio.py /path/to/audio.mp3 --collection griot

# With speaker diarization (for interviews)
python ingest-audio.py /path/to/interview.mp3 --diarize --dry-run

# Save intermediate outputs
python ingest-audio.py /path/to/audio.mp3 --output-dir ./outputs --dry-run
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--collection` | `griot` | Target vector collection |
| `--diarize` | off | Enable speaker diarization |
| `--chunk-size` | 500 | Chunk size in characters |
| `--chunk-overlap` | 50 | Overlap between chunks |
| `--dry-run` | off | Skip vector ingestion |
| `--output-dir` | none | Save transcript and chunks to files |

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `WHISPER_ASR_API_URL` | `https://whisper-api-griot-grits...` | Whisper ASR endpoint |
| `CHUNKER_SERVICE_URL` | `https://chunker-service-gng-user50...` | Chunker service endpoint |
| `VECTOR_GATEWAY_URL` | `https://vector-gateway-gng-user50...` | Vector gateway endpoint |

## Example: Process Test Audio

```bash
# From repository root
cd infra/rag/scripts
pip install -r requirements.txt

# Process the sample audio file
python ingest-audio.py ../../../docs/rag/test_files/sample_two_people.mp3 \
  --diarize \
  --dry-run \
  --output-dir ./test-output
```

This will:
1. Transcribe the audio using Whisper (with speaker diarization)
2. Chunk the transcript
3. Save outputs to `./test-output/`
4. Skip vector ingestion (dry run)

Once Milvus is available, remove `--dry-run` to complete ingestion.
