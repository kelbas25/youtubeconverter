from aiogram.dispatcher.filters.state import StatesGroup, State


class ImageState(StatesGroup):
    pressed_image = State()


class YouTextState(StatesGroup):
    pressed_to_text = State()


class YouAudioState(StatesGroup):
    pressed_to_audio = State()