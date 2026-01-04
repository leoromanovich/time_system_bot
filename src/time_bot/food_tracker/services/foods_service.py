from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from ..domain.normalize import sanitize_filename
from .file_store import FileStore


class FoodsService:
    def __init__(self, file_store: FileStore, foods_dir: str = "Foods"):
        self.file_store = file_store
        self.foods_dir = foods_dir

    async def ensure_notes(self, foods: Iterable[str]) -> List[Path]:
        created_paths: List[Path] = []
        reserved_names: set[str] = set()
        for food in foods:
            path = self._select_unique_path(food, reserved_names)
            reserved_names.add(path.name)
            filename = path.name
            default_content = self._build_default_content(food, filename)
            result = await self.file_store.ensure_file(path, default_content=default_content)
            created_paths.append(result)
        return created_paths

    def _select_unique_path(self, food: str, reserved_names: set[str]) -> Path:
        base_name = sanitize_filename(food)
        filename = f"{base_name}.md"
        path = Path(self.foods_dir) / filename
        if self._path_matches_original(path, food):
            return path
        if not self.file_store.resolve(path).exists() and filename not in reserved_names:
            return path

        counter = 2
        while True:
            candidate_name = f"{base_name} ({counter}).md"
            candidate_path = Path(self.foods_dir) / candidate_name
            if self._path_matches_original(candidate_path, food):
                return candidate_path
            if not self.file_store.resolve(candidate_path).exists() and candidate_name not in reserved_names:
                return candidate_path
            counter += 1

    def _path_matches_original(self, relative_path: Path, food: str) -> bool:
        target = self.file_store.resolve(relative_path)
        if not target.exists():
            return False
        content = target.read_text(encoding="utf-8")
        original = self._extract_frontmatter_value(content, "original_name")
        return original == food

    @staticmethod
    def _extract_frontmatter_value(content: str, key: str) -> str | None:
        if not content.startswith("---"):
            return None
        lines = content.splitlines()
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if line.startswith(f"{key}:"):
                value = line.split(":", 1)[1].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
                    return value[1:-1]
                return value
        return None

    @staticmethod
    def _build_default_content(food: str, filename: str) -> str:
        escaped_food = food.replace('"', '\\"')
        escaped_filename = filename.replace('"', '\\"')
        return (
            "---\n"
            f'original_name: "{escaped_food}"\n'
            f'filename: "{escaped_filename}"\n'
            "---\n\n"
            f"# {food}\n\n"
            "#foodtracker\n"
        )
