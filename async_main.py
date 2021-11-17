import logging
import asyncio
import csv
import aioschedule
import random
import os
import psycopg2
from time import sleep
from aiogram import Bot, Dispatcher, executor, types

# урл базы данных
DATABASE_URL = os.environ['DATABASE_URL']

# токен нужного нам бота
API_TOKEN = os.environ.get('API_TOKEN')

# конфигурация логина
logging.basicConfig(level=logging.INFO)

# инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# действие когда новый пользователь появился в чате
@dp.message_handler(content_types=['new_chat_members'])
async def greeting(message: types.message):
    user = message.new_chat_members[0]
    print(f"Новый пользователь {user.id} в группе {message.chat.id}")
    mess = f"Привет, [{user.first_name}](tg://user?id={str(user.id)}) 🖖" \
           "\n\nДобро пожаловать в чат аниматоров!" \
           "\n\nПрежде всего, прошу вас изучить [правила чата](https://t.me/c/1110658596/1371)." \
           "\n\nА вот [заветный кодек FFmpeg](https://t.me/c/1110658596/16707), который вы наверняка искали." \
           "\n\nПока на этом все. Прекрасных вам анимаций! "
    # print(f"group_id = {message.chat.id}")
    await message.answer(mess, parse_mode="Markdown")
    print(f"Поздоровался с ним, имя {user.first_name}")


# отправка одного отзыва из OTZIVI.csv
async def send_feedback():
    group_id = os.environ.get('GROUP_ID')
    # todo: - 600 человек, осторожно!
    # group_id = os.environ.get('DEBUG_GROUP_ID')
    # todo: - для дебага
    await bot.send_chat_action(chat_id=group_id, action="typing")
    sleep(2)

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT post_index FROM tab;")
    n = cur.fetchone()[0]

    # проверка все ли ок с файлом с отзывами
    try:
        f = open("OTZIVI.csv", encoding='utf-8')
    except FileNotFoundError:
        print("***Ошибка*** Не найден OTZIVI.csv")
        print("Без него никак, пост небыл отправлен")
    else:
        with open("OTZIVI.csv", encoding='utf-8') as f:
            reader = csv.DictReader(f)
            post = list(reader)[n]

        try:
            f = open("add_text-2.txt", encoding='utf-8')
        except FileNotFoundError:
            print("***Ошибка*** Не найден add_text-2.txt")
            print("Без него никак, пост небыл отправлен")
        else:
            lines = open('add_text-2.txt', encoding='utf-8').read().splitlines()
            myline = random.choice(lines)
            text = "[Мультфильм дня для вашего вдохновения](" + post["Файлы поста"] + ") 👈 \n\n" + post["Текст поста"] + "\n\n👇👇👇\n\n" + str(myline)
            await bot.send_message(group_id, text, parse_mode="Markdown")
            print(f"Отправил пост номер {n} в группу с айди {group_id}")

            cur.execute("TRUNCATE tab;")
            if n == 30:
                cur.execute(f"INSERT INTO tab (post_index) VALUES ({0});")
                conn.commit()
                print("***Посты закончились, записываю в базу 0")
            else:
                cur.execute(f"INSERT INTO tab (post_index) VALUES ({n + 1});")
                conn.commit()
            cur.close()
            conn.close()


# отправка отзыва по рассписанию
async def scheduler():
    # вот тут нужно выставить время, будет постить раз в день
    # todo: придется ставить время на 3 часа раньше МСК, если сервер Heroku в штатах
    # aioschedule.every(20).seconds.do(send_feedback)
    aioschedule.every().day.at("7:00").do(send_feedback)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(2)


# создание таска по расписанию
async def on_startup(_):
    asyncio.create_task(scheduler())


# запуск бота, основная функция
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False, on_startup=on_startup)
