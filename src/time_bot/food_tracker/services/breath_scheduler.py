from __future__ import annotations

import asyncio

from aiogram import Bot

from ..ui.keyboards import breath_severity_keyboard
from .breath_reminder_service import BreathReminderService
from .time_service import TimeService


class BreathReminderScheduler:
    def __init__(
        self,
        reminder_service: BreathReminderService,
        time_service: TimeService,
    ):
        self.reminder_service = reminder_service
        self.time_service = time_service
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self, bot: Bot) -> None:
        if self._task:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(bot))

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:  # pragma: no cover - shutdown path
                pass
            self._task = None

    async def _loop(self, bot: Bot) -> None:
        while self._running:
            now = self.time_service.now()
            time_str = now.strftime("%H:%M")
            date_str = now.strftime("%Y-%m-%d")
            stamp = now.strftime("%Y-%m-%d_%H:%M:%S")
            due_regular = await self.reminder_service.get_due(time_str, date_str)
            due_one_shot = await self.reminder_service.get_due_one_shot(stamp)
            for reminder in [*due_regular, *due_one_shot]:
                try:
                    await bot.send_message(
                        reminder.chat_id,
                        "Был ли запах изо рта?",
                        reply_markup=breath_severity_keyboard(include_skip=True),
                    )
                    await self.reminder_service.mark_sent(reminder, date_str)
                except Exception:
                    continue
            await asyncio.sleep(60)
