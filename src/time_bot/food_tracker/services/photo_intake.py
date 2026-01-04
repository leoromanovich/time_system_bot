from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import aiohttp


@dataclass(slots=True)
class PhotoIntakeConfig:
    url: str
    token: str | None
    timeout_seconds: float = 30.0


class PhotoIntakeService:
    def __init__(self, config: PhotoIntakeConfig) -> None:
        self._config = config

    async def classify_image(self, image: bytes) -> Literal["dish", "ingredients"]:
        payload = await self._post_image(image)
        return self._parse_kind(payload)

    async def dish_to_ingredients(self, image: bytes) -> list[str]:
        payload = await self._post_image(image)
        return self._parse_ingredients(payload)

    async def ocr_ingredients(self, image: bytes) -> list[str]:
        payload = await self._post_image(image)
        return self._parse_ingredients(payload)

    async def _post_image(self, image: bytes) -> dict:
        headers = {"Accept": "application/json"}
        if self._config.token:
            headers["Authorization"] = f"Bearer {self._config.token}"
        timeout = aiohttp.ClientTimeout(total=self._config.timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            form = aiohttp.FormData()
            form.add_field("file", image, filename="photo.jpg", content_type="image/jpeg")
            async with session.post(
                self._config.url,
                data=form,
                headers=headers,
            ) as response:
                response.raise_for_status()
                return await response.json()

    @staticmethod
    def _parse_kind(payload: dict) -> Literal["dish", "ingredients"]:
        kind = payload.get("kind")
        if kind == "ingredients":
            return "ingredients"
        return "dish"

    @staticmethod
    def _parse_ingredients(payload: dict) -> list[str]:
        items = payload.get("ingredients")
        if isinstance(items, list):
            return [str(item).strip() for item in items if str(item).strip()]
        return []


class PhotoIntakeStubService(PhotoIntakeService):
    def __init__(self) -> None:
        super().__init__(PhotoIntakeConfig(url="http://localhost", token=None))

    async def classify_image(self, _: bytes) -> Literal["dish", "ingredients"]:
        return "dish"

    async def dish_to_ingredients(self, _: bytes) -> list[str]:
        return []

    async def ocr_ingredients(self, _: bytes) -> list[str]:
        return []
