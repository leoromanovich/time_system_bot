from __future__ import annotations

import os
from pathlib import Path

import aiofiles


class FileStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def resolve(self, relative_path: str | Path) -> Path:
        return self.base_dir.joinpath(relative_path)

    async def ensure_file(self, relative_path: str | Path, default_content: str = "") -> Path:
        target = self.resolve(relative_path)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            await self._write_atomic(target, default_content)
        return target

    async def write_text(self, relative_path: str | Path, content: str) -> Path:
        target = self.resolve(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        await self._write_atomic(target, content)
        return target

    async def _write_atomic(self, target: Path, content: str) -> None:
        tmp_path = target.with_suffix(target.suffix + ".tmp")
        async with aiofiles.open(tmp_path, "w", encoding="utf-8") as tmp_file:
            await tmp_file.write(content)
        os.replace(tmp_path, target)
