from aiogram.fsm.state import StatesGroup, State

class CreateContestSG(StatesGroup):
    title = State()
    description = State()
    winner_count = State()
    duration_days = State()
    max_participants = State()
    sponsors = State()
    button_text = State()


