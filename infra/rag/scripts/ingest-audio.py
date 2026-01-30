#!/usr/bin/env python3
"""
Audio Ingestion Pipeline for Griot & Grits

Pipeline: Audio File → Whisper ASR → Chunker → Vector Gateway (when Milvus ready)

Usage:
    python ingest-audio.py <audio_file> [--collection griot] [--dry-run]

Example:
    python ingest-audio.py docs/rag/test_files/sample_two_people.mp3 --dry-run
"""

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

# Service URLs (defaults for gng-user50 namespace)
WHISPER_URL = os.getenv(
    "WHISPER_ASR_API_URL",
    "https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org"
)
CHUNKER_URL = os.getenv(
    "CHUNKER_SERVICE_URL",
    "https://chunker-service-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com"
)
VECTOR_GATEWAY_URL = os.getenv(
    "VECTOR_GATEWAY_URL",
    "https://vector-gateway-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com"
)

# Chunking configuration
DEFAULT_CHUNK_SIZE = 500  # characters
DEFAULT_CHUNK_OVERLAP = 50


def transcribe_audio(audio_path: Path, diarize: bool = False) -> dict:
    """Transcribe audio file using Whisper ASR.

    Args:
        audio_path: Path to audio file
        diarize: Enable speaker diarization for multi-speaker audio

    Returns:
        Transcription result with segments and timestamps
    """
    print(f"📝 Transcribing: {audio_path.name}")

    params = {"output": "json"}
    if diarize:
        params["diarize"] = "true"

    with open(audio_path, "rb") as f:
        response = httpx.post(
            f"{WHISPER_URL}/asr",
            params=params,
            files={"audio_file": (audio_path.name, f)},
            timeout=300.0,  # 5 minutes for long audio
        )

    response.raise_for_status()
    result = response.json()

    # Calculate stats
    num_segments = len(result.get("segments", []))
    total_text = " ".join(seg.get("text", "").strip() for seg in result.get("segments", []))
    duration = result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0

    print(f"   ✓ Language: {result.get('language', 'unknown')}")
    print(f"   ✓ Segments: {num_segments}")
    print(f"   ✓ Duration: {duration:.1f}s")
    print(f"   ✓ Characters: {len(total_text)}")

    return result


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
    metadata: dict = None,
) -> list[dict]:
    """Chunk text using the Chunker Service.

    Args:
        text: Text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap between chunks
        metadata: Optional metadata to attach to chunks

    Returns:
        List of chunk objects
    """
    print(f"✂️  Chunking text ({len(text)} chars, window={chunk_size}, overlap={overlap})")

    request_body = {
        "text": text,
        "plan": {
            "window_size": chunk_size,
            "overlap": overlap,
            "mode": "chars",
        },
        "meta": metadata or {},
    }

    response = httpx.post(
        f"{CHUNKER_URL}/chunk",
        json=request_body,
        timeout=60.0,
    )

    response.raise_for_status()
    chunks = response.json()

    print(f"   ✓ Created {len(chunks)} chunks")

    return chunks


def ingest_chunks(
    chunks: list[dict],
    collection: str,
    source_id: str,
    source_metadata: dict,
) -> dict:
    """Ingest chunks into vector database via Vector Gateway.

    Args:
        chunks: List of chunk objects from chunker
        collection: Target collection name
        source_id: Unique identifier for the source document
        source_metadata: Metadata about the source (filename, duration, etc.)

    Returns:
        Ingestion result
    """
    print(f"📥 Ingesting {len(chunks)} chunks into collection '{collection}'")

    # Prepare documents for upsert
    documents = []
    for i, chunk in enumerate(chunks):
        doc = {
            "id": f"{source_id}_chunk_{i}",
            "text": chunk.get("text", ""),
            "metadata": {
                **source_metadata,
                "chunk_index": i,
                "start_index": chunk.get("start_index"),
                "end_index": chunk.get("end_index"),
            },
        }
        documents.append(doc)

    response = httpx.post(
        f"{VECTOR_GATEWAY_URL}/upsert",
        json={
            "collection": collection,
            "documents": documents,
        },
        timeout=120.0,
    )

    response.raise_for_status()
    result = response.json()

    print(f"   ✓ Ingested successfully")

    return result


def process_audio(
    audio_path: Path,
    collection: str = "griot",
    diarize: bool = False,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    dry_run: bool = False,
    output_dir: Path = None,
) -> dict:
    """Process an audio file through the full ingestion pipeline.

    Args:
        audio_path: Path to audio file
        collection: Target collection name
        diarize: Enable speaker diarization
        chunk_size: Chunk size in characters
        chunk_overlap: Overlap between chunks
        dry_run: If True, skip vector ingestion
        output_dir: Directory to save intermediate outputs

    Returns:
        Pipeline result with transcript, chunks, and ingestion status
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    source_id = audio_path.stem

    print(f"\n{'='*60}")
    print(f"Audio Ingestion Pipeline")
    print(f"{'='*60}")
    print(f"File: {audio_path}")
    print(f"Collection: {collection}")
    print(f"Dry run: {dry_run}")
    print(f"{'='*60}\n")

    # Step 1: Transcribe
    transcript = transcribe_audio(audio_path, diarize=diarize)

    # Save transcript if output_dir specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = output_dir / f"{source_id}_transcript.json"
        with open(transcript_path, "w") as f:
            json.dump(transcript, f, indent=2)
        print(f"   💾 Saved transcript to {transcript_path}")

    # Step 2: Extract full text from segments
    full_text = " ".join(
        seg.get("text", "").strip()
        for seg in transcript.get("segments", [])
    )

    if not full_text.strip():
        print("⚠️  No text extracted from audio")
        return {"status": "empty", "transcript": transcript, "chunks": []}

    # Step 3: Chunk the text
    source_metadata = {
        "source_file": audio_path.name,
        "source_type": "audio_transcript",
        "language": transcript.get("language", "unknown"),
        "duration_seconds": transcript.get("segments", [{}])[-1].get("end", 0),
    }

    chunks = chunk_text(
        full_text,
        chunk_size=chunk_size,
        overlap=chunk_overlap,
        metadata=source_metadata,
    )

    # Save chunks if output_dir specified
    if output_dir:
        chunks_path = output_dir / f"{source_id}_chunks.json"
        with open(chunks_path, "w") as f:
            json.dump(chunks, f, indent=2)
        print(f"   💾 Saved chunks to {chunks_path}")

    # Step 4: Ingest (unless dry run)
    ingestion_result = None
    if dry_run:
        print(f"\n🔸 DRY RUN: Skipping vector ingestion")
        print(f"   Would ingest {len(chunks)} chunks into '{collection}'")
    else:
        try:
            ingestion_result = ingest_chunks(
                chunks,
                collection=collection,
                source_id=source_id,
                source_metadata=source_metadata,
            )
        except httpx.HTTPStatusError as e:
            print(f"\n⚠️  Ingestion failed: {e}")
            print(f"   (Milvus may not be available yet)")
            ingestion_result = {"status": "failed", "error": str(e)}

    # Summary
    print(f"\n{'='*60}")
    print(f"Pipeline Complete")
    print(f"{'='*60}")
    print(f"Transcript segments: {len(transcript.get('segments', []))}")
    print(f"Total characters: {len(full_text)}")
    print(f"Chunks created: {len(chunks)}")
    if dry_run:
        print(f"Ingestion: SKIPPED (dry run)")
    elif ingestion_result and ingestion_result.get("status") != "failed":
        print(f"Ingestion: SUCCESS")
    else:
        print(f"Ingestion: FAILED (Milvus not available?)")
    print(f"{'='*60}\n")

    return {
        "status": "success",
        "source_file": str(audio_path),
        "transcript": transcript,
        "chunks": chunks,
        "ingestion": ingestion_result,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Ingest audio files into the Griot RAG system"
    )
    parser.add_argument(
        "audio_file",
        type=Path,
        help="Path to audio file (mp3, wav, m4a, etc.)",
    )
    parser.add_argument(
        "--collection",
        default="griot",
        help="Target collection name (default: griot)",
    )
    parser.add_argument(
        "--diarize",
        action="store_true",
        help="Enable speaker diarization for multi-speaker audio",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Chunk size in characters (default: {DEFAULT_CHUNK_SIZE})",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Chunk overlap in characters (default: {DEFAULT_CHUNK_OVERLAP})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without vector ingestion",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to save intermediate outputs (transcript, chunks)",
    )

    args = parser.parse_args()

    try:
        result = process_audio(
            args.audio_file,
            collection=args.collection,
            diarize=args.diarize,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            dry_run=args.dry_run,
            output_dir=args.output_dir,
        )

        # Exit with appropriate code
        if result.get("status") == "success":
            sys.exit(0)
        else:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
