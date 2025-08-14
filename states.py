from aiogram.fsm.state import State, StatesGroup

class AuthStates(StatesGroup):
    WAITING_FOR_NAME = State()
    WAITING_FOR_PHONE = State()

class SearchStates(StatesGroup):
    WAITING_FOR_QUERY = State()

class RubrikaStates(StatesGroup):
    WAITING_FOR_RUBRIKA = State()
    WAITING_FOR_ARTICLE = State()