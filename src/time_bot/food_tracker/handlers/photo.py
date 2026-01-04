from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..domain.models import FoodEventDraft
from ..fsm.states import FoodLogStates
from ..services.photo_intake import PhotoIntakeService
from ..services.time_service import TimeService
from ..ui.keyboards import adding_foods_keyboard

router = Router()

_photo_intake_service_instance: PhotoIntakeService | None = None
_time_service_instance: TimeService | None = None


def setup_dependencies(
    photo_intake_service: PhotoIntakeService, time_service: TimeService
) -> None:
    global _photo_intake_service_instance, _time_service_instance
    _photo_intake_service_instance = photo_intake_service
    _time_service_instance = time_service


def _photo_intake_service() -> PhotoIntakeService:
    if _photo_intake_service_instance is None:  # pragma: no cover - wiring issue
        raise RuntimeError("PhotoIntakeService is not configured")
    return _photo_intake_service_instance


def _time_service() -> TimeService:
    if _time_service_instance is None:  # pragma: no cover - wiring issue
        raise RuntimeError("TimeService is not configured")
    return _time_service_instance


@router.message(lambda message: bool(message.photo))
async def handle_photo(message: Message, state: FSMContext) -> None:
    if message.bot is None:
        await message.answer("Не удалось обработать фото: бот не инициализирован.")
        return

    if not message.photo:
        await message.answer("Не удалось обработать фото: снимок не найден.")
        return

    try:
        file = await message.bot.get_file(message.photo[-1].file_id)
        photo_bytes = await message.bot.download_file(file.file_path)
        image_bytes = photo_bytes.read()
    except Exception:
        await message.answer(
            "Не смог загрузить фото. Попробуйте отправить ещё раз или используйте /add."
        )
        return

    try:
        kind = await _photo_intake_service().classify_image(image_bytes)
        if kind == "ingredients":
            ingredients = await _photo_intake_service().ocr_ingredients(image_bytes)
        else:
            ingredients = await _photo_intake_service().dish_to_ingredients(image_bytes)
    except Exception:
        await message.answer(
            "Сервис распознавания недоступен. Попробуйте позже или используйте /add."
        )
        return

    if not ingredients:
        await message.answer(
            "Не удалось извлечь ингредиенты. Попробуйте другое фото или используйте /add."
        )
        return

    draft = FoodEventDraft(started_at=_time_service().now())
    draft.append_foods(ingredients)
    await state.clear()
    await state.update_data(draft=draft.model_dump())
    await state.set_state(FoodLogStates.adding_foods)
    await message.answer(
        "Распознал ингредиенты. Проверьте список и продолжайте:\n"
        + "\n".join(f"• {item}" for item in ingredients),
        reply_markup=adding_foods_keyboard(),
    )
