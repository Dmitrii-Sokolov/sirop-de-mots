"""
Generate audio files for Anki cards using Azure TTS.

Usage:
    # Create .env file in project root with:
    # AZURE_SPEECH_KEY=your_key
    # AZURE_SPEECH_REGION=your_region (e.g., canadacentral)
    #
    # Or set environment variables directly.

    # Generate audio for all content:
    python scripts/09_generate_audio.py

    # Generate for specific file:
    python scripts/09_generate_audio.py --input content/quebecismes/all.csv

    # Dry run (show what would be generated):
    python scripts/09_generate_audio.py --dry-run

    # Limit number of items:
    python scripts/09_generate_audio.py --limit 10
"""

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterator

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables directly

# Azure Speech SDK - install with: pip install azure-cognitiveservices-speech
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    print("Warning: azure-cognitiveservices-speech not installed.")
    print("Install with: pip install azure-cognitiveservices-speech")

from config import (
    PROJECT_ROOT,
    AZURE_TTS_VOICES,
    AZURE_TTS_FORMAT,
    AZURE_TTS_REQUESTS_PER_SECOND,
    AZURE_TTS_RETRY_ATTEMPTS,
)

# =============================================================================
# Paths
# =============================================================================

CONTENT_DIR = PROJECT_ROOT / "content"
AUDIO_BASE_DIR = CONTENT_DIR / "audio"

# Content files to process (order: expressions, quebecismes, then vocabulary by level)
CONTENT_FILES = [
    CONTENT_DIR / "expressions" / "all.csv",
    CONTENT_DIR / "quebecismes" / "all.csv",
    CONTENT_DIR / "vocabulary" / "a1_a2.csv",
    CONTENT_DIR / "vocabulary" / "b1.csv",
    CONTENT_DIR / "vocabulary" / "b2.csv",
    CONTENT_DIR / "vocabulary" / "c1.csv",
    CONTENT_DIR / "vocabulary" / "autres.csv",
]


def get_audio_dirs(source_file: Path) -> tuple[Path, Path]:
    """
    Get audio directories for a source CSV file.

    Examples:
        expressions/all.csv -> audio/expressions/words/, audio/expressions/examples/
        vocabulary/a1_a2.csv -> audio/vocabulary/a1_a2/words/, audio/vocabulary/a1_a2/examples/
    """
    rel_path = source_file.relative_to(CONTENT_DIR)
    parent = rel_path.parent.name  # "expressions" or "vocabulary"

    if parent == "vocabulary":
        audio_subdir = Path(parent) / rel_path.stem  # vocabulary/a1_a2
    else:
        audio_subdir = Path(parent)  # expressions

    return (
        AUDIO_BASE_DIR / audio_subdir / "words",
        AUDIO_BASE_DIR / audio_subdir / "examples",
    )

# =============================================================================
# Helpers
# =============================================================================

def slugify(text: str) -> str:
    """
    Convert French text to filename-safe slug.

    Examples:
        "une maison" -> "une_maison"
        "l'homme" -> "l_homme"
        "aujourd'hui" -> "aujourd_hui"
        "être" -> "etre"
    """
    # Normalize apostrophes
    text = text.replace("'", "_").replace("'", "_")

    # Remove accents for filename (keep original for TTS)
    accent_map = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'à': 'a', 'â': 'a', 'ä': 'a',
        'ù': 'u', 'û': 'u', 'ü': 'u',
        'î': 'i', 'ï': 'i',
        'ô': 'o', 'ö': 'o',
        'ç': 'c',
        'œ': 'oe', 'æ': 'ae',
    }
    slug = text.lower()
    for accented, plain in accent_map.items():
        slug = slug.replace(accented, plain)

    # Replace spaces and special chars with underscore
    slug = re.sub(r'[^a-z0-9]+', '_', slug)

    # Remove leading/trailing underscores
    slug = slug.strip('_')

    # Collapse multiple underscores
    slug = re.sub(r'_+', '_', slug)

    return slug


def strip_html(text: str) -> str:
    """Remove HTML tags like <b>...</b> from text."""
    return re.sub(r'<[^>]+>', '', text)


def get_voice(index: int) -> str:
    """Get voice name, cycling through available voices."""
    return AZURE_TTS_VOICES[index % len(AZURE_TTS_VOICES)]


class AudioGenerator:
    """Azure TTS audio generator with rate limiting and retry logic."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.speech_config = None
        self.request_count = 0
        self.last_request_time = 0
        self.voice_index = 0

        if not dry_run and AZURE_SDK_AVAILABLE:
            self._init_azure()

    def _init_azure(self):
        """Initialize Azure Speech SDK."""
        key = os.environ.get("AZURE_SPEECH_KEY")
        region = os.environ.get("AZURE_SPEECH_REGION")

        if not key or not region:
            raise ValueError(
                "Azure credentials not set. Please set environment variables:\n"
                "  AZURE_SPEECH_KEY=your_key\n"
                "  AZURE_SPEECH_REGION=your_region"
            )

        self.speech_config = speechsdk.SpeechConfig(
            subscription=key,
            region=region
        )
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3
        )

    def _rate_limit(self):
        """Apply rate limiting between requests."""
        if self.dry_run:
            return

        min_interval = 1.0 / AZURE_TTS_REQUESTS_PER_SECOND
        elapsed = time.time() - self.last_request_time

        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        self.last_request_time = time.time()

    def _synthesize(self, text: str, output_path: Path, voice: str) -> bool:
        """
        Synthesize speech and save to file.

        Returns True on success, False on failure.
        """
        if self.dry_run:
            print(f"  [DRY RUN] Would generate: {output_path.name}")
            return True

        if not AZURE_SDK_AVAILABLE:
            print("  [SKIP] Azure SDK not available")
            return False

        self.speech_config.speech_synthesis_voice_name = voice

        for attempt in range(AZURE_TTS_RETRY_ATTEMPTS):
            try:
                self._rate_limit()

                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=self.speech_config,
                    audio_config=None  # We'll get raw audio data
                )

                result = synthesizer.speak_text_async(text).get()

                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    # Save audio data to file
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(result.audio_data)
                    return True

                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation = result.cancellation_details
                    print(f"  [ERROR] Synthesis canceled: {cancellation.reason}")
                    if cancellation.error_details:
                        print(f"  [ERROR] Details: {cancellation.error_details}")

                    # Retry on transient errors
                    if attempt < AZURE_TTS_RETRY_ATTEMPTS - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        print(f"  [RETRY] Waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    return False

            except Exception as e:
                print(f"  [ERROR] Exception: {e}")
                if attempt < AZURE_TTS_RETRY_ATTEMPTS - 1:
                    wait_time = 2 ** attempt
                    print(f"  [RETRY] Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                return False

        return False

    def generate_for_entry(
        self,
        french: str,
        example_french: str | None,
        words_dir: Path,
        examples_dir: Path,
        skip_existing: bool = True
    ) -> tuple[bool, bool]:
        """
        Generate audio for a vocabulary entry.

        Returns (word_success, example_success) tuple.
        """
        slug = slugify(french)
        voice = get_voice(self.voice_index)
        self.voice_index += 1

        word_path = words_dir / f"{slug}.mp3"
        example_path = examples_dir / f"{slug}_ex.mp3"

        word_success = False
        example_success = False

        # Generate word audio
        if skip_existing and word_path.exists():
            print(f"  [SKIP] Word already exists: {word_path.name}")
            word_success = True
        else:
            print(f"  [WORD] {french} -> {word_path.name} ({voice})")
            word_success = self._synthesize(french, word_path, voice)

        # Generate example audio
        if example_french:
            example_clean = strip_html(example_french)

            if skip_existing and example_path.exists():
                print(f"  [SKIP] Example already exists: {example_path.name}")
                example_success = True
            else:
                print(f"  [EXAMPLE] -> {example_path.name}")
                example_success = self._synthesize(example_clean, example_path, voice)
        else:
            example_success = True  # No example to generate

        return word_success, example_success


def read_content_file(path: Path) -> Iterator[dict]:
    """Read CSV file and yield rows as dicts."""
    if not path.exists():
        print(f"Warning: File not found: {path}")
        return

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def process_file(
    generator: AudioGenerator,
    file_path: Path,
    limit: int | None = None,
    skip_existing: bool = True
) -> tuple[int, int, int]:
    """
    Process a content CSV file and generate audio.

    Returns (total, success, failed) counts.
    """
    print(f"\n{'='*60}")
    try:
        display_path = file_path.relative_to(PROJECT_ROOT)
    except ValueError:
        display_path = file_path.name
    print(f"Processing: {display_path}")

    # Get audio directories for this source file
    words_dir, examples_dir = get_audio_dirs(file_path)
    words_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)
    print(f"Audio: {words_dir.relative_to(PROJECT_ROOT)}")
    print('='*60)

    total = 0
    success = 0
    failed = 0

    for row in read_content_file(file_path):
        if limit and total >= limit:
            print(f"\nLimit of {limit} reached.")
            break

        french = row.get('French', '').strip()
        example = row.get('ExampleFrench', '').strip()

        if not french:
            continue

        total += 1
        print(f"\n[{total}] {french}")

        word_ok, example_ok = generator.generate_for_entry(
            french, example, words_dir, examples_dir, skip_existing
        )

        if word_ok and example_ok:
            success += 1
        else:
            failed += 1

    return total, success, failed


def main():
    parser = argparse.ArgumentParser(
        description="Generate audio files for Anki cards using Azure TTS"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        help="Process specific CSV file instead of all content files"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be generated without making API calls"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        help="Limit number of entries to process per file"
    )
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="Regenerate existing files instead of skipping"
    )

    args = parser.parse_args()

    # Check SDK availability for non-dry-run mode
    if not args.dry_run and not AZURE_SDK_AVAILABLE:
        print("Error: Azure SDK required for audio generation.")
        print("Install with: pip install azure-cognitiveservices-speech")
        print("Or use --dry-run to preview without generating audio.")
        return 1

    # Initialize generator
    try:
        generator = AudioGenerator(dry_run=args.dry_run)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    # Determine files to process
    if args.input:
        # Resolve relative path to absolute
        files = [Path(args.input).resolve()]
    else:
        files = [f for f in CONTENT_FILES if f.exists()]

    if not files:
        print("No content files found to process.")
        print("Expected files:")
        for f in CONTENT_FILES:
            status = "OK" if f.exists() else "MISSING"
            print(f"  [{status}] {f.relative_to(PROJECT_ROOT)}")
        return 1

    # Process files
    total_all = 0
    success_all = 0
    failed_all = 0

    for file_path in files:
        total, success, failed = process_file(
            generator,
            file_path,
            limit=args.limit,
            skip_existing=not args.no_skip
        )
        total_all += total
        success_all += success
        failed_all += failed

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total entries:  {total_all}")
    print(f"Success:        {success_all}")
    print(f"Failed:         {failed_all}")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually generated.")

    return 0 if failed_all == 0 else 1


if __name__ == "__main__":
    exit(main())
