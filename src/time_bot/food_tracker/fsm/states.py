from aiogram.fsm.state import State, StatesGroup


class FoodLogStates(StatesGroup):
    adding_foods = State()
    confirm_finish = State()
    ask_condition_bloating = State()
    ask_condition_diarrhea = State()
    ask_condition_well_being = State()
    persisting = State()
    waiting_photo = State()
    guess_input = State()


class ConditionStandaloneStates(StatesGroup):
    ask_bloating = State()
    ask_diarrhea = State()
    ask_well_being = State()
