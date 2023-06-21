from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton


kb = ReplyKeyboardMarkup(resize_keyboard=True)
to_stiker = KeyboardButton('🖼️ Convert to sticker sizes')
youtube_to_text = KeyboardButton('📝 Youtube to text')
youtube_to_audio = KeyboardButton('🎵 Youtube to audio')

kb.add(to_stiker)
kb.add(youtube_to_audio, youtube_to_text)

kb_back = ReplyKeyboardMarkup(resize_keyboard=True)
kb_back.add(KeyboardButton('⬅️ Cancel'))
