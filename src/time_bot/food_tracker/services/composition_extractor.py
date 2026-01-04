from __future__ import annotations

import asyncio
import base64
import json
import os
from typing import List

import requests


class CompositionExtractor:
    def __init__(
        self,
        *,
        model: str | None = None,
        endpoint: str | None = None,
        recognize_prompt: str | None = None,
        guess_text_prompt: str | None = None,
        guess_image_prompt: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or "openai/gpt-5-nano"
        self.endpoint = endpoint or "https://openrouter.ai/api/v1/chat/completions"
        self.api_key = api_key
        self.recognize_prompt = recognize_prompt or (
            "На изображении текст состава продукта. Верни ингредиенты построчно, "
            "как они перечислены, без нумерации и лишних символов."
        )
        self.guess_text_prompt = guess_text_prompt or (
            "По названию блюда предположи его состав (список основных ингредиентов). "
            "Верни только список, по одному ингредиенту в строке без лишнего текста."
        )
        self.guess_image_prompt = guess_image_prompt or (
            "На фото блюдо. Предположи его состав и верни ингредиенты построчно без комментариев."
        )
        self.system_prompt = (
            "Ты помогаешь определять состав блюд и продуктов. "
            "Отвечай только списком ингредиентов, по одному пункту на строку."
        )

    def _load_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        return key

    def _encode_image(self, data: bytes, mime: str) -> str:
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{encoded}"

    def _send_request(self, messages: List[dict]) -> str:
        api_key = self._load_api_key()
        payload = {"model": self.model, "messages": messages}
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/leoromanovich/food_calendar",
            "Content-Type": "application/json",
        }
        response = requests.post(
            self.endpoint,
            headers=headers,
            data=json.dumps(payload),
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    async def _run(self, messages: List[dict]) -> str:
        return await asyncio.to_thread(self._send_request, messages)

    async def recognize_from_image(
        self, data: bytes, *, prompt: str | None = None, mime: str = "image/jpeg"
    ) -> str:
        prompt_text = prompt or self.recognize_prompt
        encoded = self._encode_image(data, mime)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": encoded}},
                ],
            },
        ]
        return await self._run(messages)

    async def guess_from_text(self, dish_name: str, prompt: str | None = None) -> str:
        dish = dish_name.strip()
        if not dish:
            raise ValueError("Dish name is empty")
        prompt_text = prompt or self.guess_text_prompt
        user_text = f"{prompt_text}\n\nБлюдо: {dish}"
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": [{"type": "text", "text": user_text}]},
        ]
        return await self._run(messages)

    async def guess_from_image(
        self, data: bytes, *, prompt: str | None = None, mime: str = "image/jpeg"
    ) -> str:
        prompt_text = prompt or self.guess_image_prompt
        encoded = self._encode_image(data, mime)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": encoded}},
                ],
            },
        ]
        return await self._run(messages)

    async def extract(
        self, data: bytes, *, prompt: str | None = None, mime: str = "image/jpeg"
    ) -> str:
        return await self.recognize_from_image(data, prompt=prompt, mime=mime)
