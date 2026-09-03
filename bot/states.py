from aiogram.fsm.state import StatesGroup, State

class CreateContestSG(StatesGroup):
    title = State()
    description = State()
    winner_count = State()
    sponsors = State()
    button_text = State()

