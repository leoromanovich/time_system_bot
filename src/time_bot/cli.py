"""Simple CLI for manual testing of the pipeline."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from time_bot.pipeline import process_message_text


async def run_cli(text: str, *, dry_run: bool = False, output_dir: Path | None = None) -> None:
    result = await process_message_text(text, output_dir=output_dir)
    if dry_run:
        print(result.markdown)
        return
    print(f"Saved note to {result.note_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual CLI entry point for time_system_bot")
    parser.add_argument("text", help="Message to parse")
    parser.add_argument("--dry-run", action="store_true", help="Print markdown instead of writing file")
    parser.add_argument("--output-dir", type=Path, help="Override Obsidian vault path")
    args = parser.parse_args()

    asyncio.run(run_cli(args.text, dry_run=args.dry_run, output_dir=args.output_dir))


if __name__ == "__main__":
    main()
