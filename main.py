import asyncio

import requests
from PIL import Image
from moviepy.video.io.VideoFileClip import VideoFileClip
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
import aiofiles as aiof

# python modules
from tqdm import tqdm
import logging
from typing import Optional
import time
import re
import os

# telethon
from telethon import TelegramClient

# aiogram
from aiogram import Dispatcher, Bot, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import ContentType, input_file

# including files
from kb import kb, kb_back
from states import ImageState, YouTextState, YouAudioState


bot = Bot(token='')
ds = MemoryStorage()
dp = Dispatcher(bot, storage=ds)

# telethon

api_id = 0
api_hash = ''
phone = ''

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands="start", state='*')
async def start_handler(message: types.Message, state: FSMContext):
    await bot.send_message(
        message.from_user.id,
        f"Hello, {message.from_user.username}!",
        reply_markup=kb
    )


@dp.message_handler(Text(endswith='cancel', ignore_case=True), state='*')
@dp.message_handler(commands='cancel', state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    # await bot.edit_message_reply_markup(message.from_user.id, message.message_id, reply_markup=kb)
    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.send_message(
        message.from_user.id,
        'Successfully canceled! ✅',
        reply_markup=kb
    )


@dp.message_handler(Text(equals='🖼️ Convert to sticker sizes'), state='*')
async def button_image_handler(message: types.Message, state: FSMContext):
    await bot.delete_message(message.from_user.id, message.message_id)
    await ImageState.pressed_image.set()
    await bot.send_message(
        message.from_user.id,
        "🖼️ Send me pls image and I will reformat it for telegram`s requirements",
        reply_markup=kb_back
    )


@dp.message_handler(state=ImageState.pressed_image, content_types=[ContentType.PHOTO, ContentType.DOCUMENT])
async def image_handler(message: types.Message, state: FSMContext):
    if message.document:
        if re.search(r"\.([a-zA-Z]+)$", message.document["file_name"])[1] != 'jpg' \
                and re.search(r"\.([a-zA-Z]+)$", message.document["file_name"])[1] != 'png' \
                and re.search(r"\.([a-zA-Z]+)$", message.document["file_name"][1].lower()) != 'webp':
            await message.reply("Image must be jpg or png, please try to send not as file")
            return
    await types.ChatActions.upload_document()
    photo_id = 0
    if message.photo:
        photo_id = message.photo[-1].file_id
    else:
        photo_id = message.document.file_id
    await bot.download_file_by_id(photo_id, f"{message.from_user.id}.png")
    convert(f"{message.from_user.id}.png")
    await state.finish()
    await bot.send_document(message.from_user.id, input_file.InputFile(f"{message.from_user.id}.png"), reply_markup=kb)
    try:
        os.remove(f"{message.from_user.id}.png")
    except NotImplementedError as e:
        logging.warning(e)


def convert(path: str):
    try:
        img = Image.open(path)
    except OSError as e:
        logging.info(e)
        return
    if not (img.size[0] <= 512 and img.size[1] <= 512):
        img = img.resize((512, 178))
    img.save(path)


@dp.message_handler(Text(equals='📝 Youtube to text'), state='*')
async def button_to_text_handler(message: types.Message, state: FSMContext):
    await YouTextState.pressed_to_text.set()
    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.send_message(
        message.from_user.id,
        "Send me link on the youtube video",
        reply_markup=kb_back
    )


@dp.message_handler(state=YouTextState.pressed_to_text)
async def youtube_to_text(message: types.Message, state: FSMContext):
    await types.ChatActions.upload_document()
    video_id = get_video_id(message.text)
    if video_id is None:
        await bot.send_message(message.from_user.id, "Unfortunately this type of link is not supported")
        return
    try:
        subtitles = YouTubeTranscriptApi.get_transcript(video_id, languages=['ru', 'en', 'de', 'uk', 'es'])
    except Exception as e:
        await bot.send_message(message.from_user.id, "Sorry, it is impossible to download subtitles from this video 😢")
        return
    async with aiof.open(f"{message.from_user.id}.txt", 'w') as file:
        for i in subtitles:
            await file.write(i['text'] + '\n')
            await file.flush()

    await bot.send_document(
        message.from_user.id,
        input_file.InputFile(f"{message.from_user.id}.txt"),
        reply_markup=kb
    )

    await state.finish()
    try:
        os.remove(f"{message.from_user.id}.txt")
    except NotImplementedError as e:
        logging.warning(e)


@dp.message_handler(Text(equals='🎵 Youtube to audio'))
async def pressed_button_to_audio(message: types.Message, state: FSMContext):
    await YouAudioState.pressed_to_audio.set()
    await bot.delete_message(message.from_user.id, message.message_id)
    await bot.send_message(
        message.from_user.id,
        "Please, send me YouTube url",
        reply_markup=kb_back
    )


@dp.message_handler(state=YouAudioState.pressed_to_audio)
async def video_handler(message: types.Message, state: FSMContext):
    # time
    first_tic = time.perf_counter()
    # time

    video_id = get_video_id(message.text)
    if video_id is None:
        await bot.send_message(message.from_user.id, "Unfortunately this type of link is not supported")
        return

    tmp = await bot.send_message(message.from_user.id, "Wait...")
    yt = YouTube(message.text)
    print(str(yt.streams.get_by_itag(139).url))

    # time
    download_time = time.perf_counter()
    # time

    # async with aiohttp.ClientSession() as session:
    #     yt = YouTube(message.text)
    #     stream = yt.streams.get_by_itag(139)
    #     async with session.get(stream.url) as resp:
    #         with open(f'{yt.title}.mp4', 'wb') as f:
    #             while True:
    #                 chunk = await resp.content.read(1024)
    #                 if not chunk:
    #                     break
    #                 f.write(chunk)
    #     print(f'{yt.title} downloaded successfully')
    # yt.streams.get_by_itag(139).download(filename=f"{video_id}p139.mp3")

    # time
    print(f"downloaded for :{time.perf_counter() - download_time}s.")
    send_time = time.perf_counter()
    # time

    # # send file by client to bot
    # with open(f"{video_id}p139.mp3", 'rb') as file:
    #     await client.send_file(
    #         "eu_gene_learn_bot",
    #         file,
    #         progress_callback=callback
    #     )

    # await bot.send_audio(
    #     message.from_user.id,
    #     # input_file.InputFile(f"{message.from_user.id}.webm")
    #     audio=open(f"{message.from_user.id}p139.webm", 'rb'),
    # )

    # time
    print(f"sended for: {time.perf_counter() - send_time}s.")
    # time

    await bot.delete_message(message.from_user.id, tmp.message_id)
    # os.remove(f"{message.from_user.id}p139.webm")
    await state.finish()
    await start_handler(message, state)


def callback(current, total):
    print('Uploaded', current, 'out of', total,
          'bytes: {:.2%}'.format(current / total))


def get_video_id(url: str) :
    regex_pattern = r"(?:\/|%3D|v=)([a-zA-Z0-9_-]{11})"
    # regeg:
    # (?:v=|\/)([0-9A-Za-z_-]{11}).*
    # res:
    # v=gvYGIhuiJQI&ab_channel=PythonToday
    video_id = re.search(regex_pattern, url)
    if video_id:
        video_id = video_id.group(0)
    else:
        return None

    while len(video_id) > 11:
        video_id = video_id[1:]

    return video_id


if __name__ == '__main__':
    client = TelegramClient("test", api_id, api_hash)
    client.connect()
    if not client.is_user_authorized():
        # client.send_code_request(phone) #for first start - uncomment, after sign in for avoid FloodWait - should be
        # commented
        client.sign_in(phone, input('Enter code: '))
    client.start()
    executor.start_polling(dp, skip_updates=True)
