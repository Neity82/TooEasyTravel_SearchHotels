import re
import time
from typing import Dict

import telebot
from decouple import config
from loguru import logger
from telebot import types

from log import logging_decor
from botrequests.city_class import City
from botrequests.hotel_class import Hotel

TOKEN: str = config("TOKEN")
KEY: str = config("KEY")

bot = telebot.TeleBot(TOKEN)

COMPANY: str = '"Too Easy Travel"'
URL_BASIC: str = "https://hotels4.p.rapidapi.com/"
HEADERS: Dict = {
    'x-rapidapi-key': KEY,
    'x-rapidapi-host': "hotels4.p.rapidapi.com"
}

users: Dict = {}


@logging_decor
def new_user(chat_id) -> None:
    if chat_id not in users:
        users[chat_id] = City()
        logger.info("Новый пользователь добавлен в список, ID чата: {chat_id}".format(chat_id=chat_id))


@bot.message_handler(commands=['hello_world'])
@logging_decor
def hello_world(message) -> None:
    """
    Функция обрабатывает команду /hello_world.
    Выводит ответное сообщение пользователю.
    """
    new_user(message.chat.id)

    bot.send_message(message.from_user.id, "Привет Мир!")


@bot.message_handler(commands=['start'])
@logging_decor
def start_message(message) -> None:
    """
    Функция обрабатывает команду /start.
    Выводит стартовое сообщение пользователю.
    """
    new_user(message.chat.id)

    bot.send_message(message.from_user.id, "Привет, {user}! Я бот компании {name}. Я могу помочь Вам найти "
                                           "самые дешевые или самые дорогие отели по всему миру, "
                                           "подобрать наиболее подходящий для Вас отель по цене и расположению."
                                           "\n\nЧтобы узнать подробнее о моих возможностях - нажмите "
                                           "/help.".format(user=message.from_user.first_name,
                                                           name=COMPANY))


@bot.message_handler(commands=['help'])
@logging_decor
def help_message(message) -> None:
    """
    Функция обрабатывает команду /help.
    Выводит список команд пользователю.
    """
    new_user(message.chat.id)

    bot.send_message(message.from_user.id, "Бот {name} может:\n\n"
                                           "/lowprice - подобрать топ самых дешёвых отелей в городе\n"
                                           "/highprice - подобрать топ самых дорогих отелей в городе\n"
                                           "/bestdeal -подобрать топ отелей, наиболее подходящих по цене и "
                                           "расположению от центра(самые дешёвые и находятся ближе всего к "
                                           "центру)".format(name=COMPANY))


@bot.message_handler(commands=['lowprice'])
@logging_decor
@logger.catch
def command_lowprice(message) -> None:
    """
    Функция обрабатывает команду /lowprice.
    Запрашивает у пользователя город для поиска.
    """
    new_user(message.chat.id)

    users[message.chat.id].sort_order = "PRICE"
    bot.send_message(message.chat.id, 'Введите название города')
    bot.register_next_step_handler(message, search_for_city)


@bot.message_handler(commands=['highprice'])
@logging_decor
@logger.catch
def command_higprice(message) -> None:
    """
    Функция обрабатывает команду /highprice.
    Запрашивает у пользователя город для поиска.
    """
    new_user(message.chat.id)

    users[message.chat.id].sort_order = "PRICE_HIGHEST_FIRST"
    bot.send_message(message.chat.id, 'Введите название города')
    bot.register_next_step_handler(message, search_for_city)


@logging_decor
@logger.catch
def search_for_city(message) -> None:
    """
    Предлагает варианты городов для поиска
    Обрабатывает ошибку, если города нет.
    """
    users[message.chat.id].name = message.text
    try:
        cities_list = users[message.chat.id].search_all_id_for_name(URL_BASIC=URL_BASIC, HEADERS=HEADERS)
        if not cities_list:
            raise KeyError
        else:
            if len(cities_list) > 1:
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                key_list = [types.InlineKeyboardButton(text=i_name, callback_data=i_id)
                            for i_id, i_name in cities_list.items()]
                keyboard.add(*key_list)
                bot.send_message(message.chat.id, text="Выберите город из списка:", reply_markup=keyboard)
            else:
                users[message.chat.id].city_id = [i_id for i_id in cities_list][0]
                query_total_hotels(message)
    except KeyError:
        logger.error("Город отсутствует в базе данных: {val}".format(val=message.text))
        bot.send_message(message.chat.id, "В моей базе нет такого города.")
        time.sleep(2)
        command_lowprice(message)


@bot.callback_query_handler(func=lambda call: True)
@logging_decor
@logger.catch
def callback_worker(call) -> None:
    """
    Обработчик Inline клавиатуры
    """
    users[call.message.chat.id].city_id = call.data
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    query_total_hotels(call.message)


@logging_decor
@logger.catch
def query_total_hotels(message) -> None:
    """
    Функция запрашивает у пользователя какое количество отелей необходимо отобразить.
    """
    bot.send_message(message.chat.id, "Сколько отелей показать? (не более 25)")
    bot.register_next_step_handler(message, check_errors_in_total_hotels)


@logging_decor
@logger.catch
def check_errors_in_total_hotels(message) -> None:
    """
    Функция обрабатывает ошибки, связанные
    с некорректным вводом количества отелей пользователем
    Если ошибок не найдено отправляет запрос на поиск отелей,
    создает список из объектов класса Hotel
    """
    try:
        if not message.text.isdigit():
            raise TypeError
        elif int(message.text) not in range(1, 26):
            raise ValueError
        else:
            users[message.chat.id].total_hotels = message.text

    except TypeError:
        logger.error("Неверные формат ввода: {val}".format(val=message.text))
        bot.send_message(message.chat.id, "Вводите цифрами!")
        query_total_hotels(message)
    except ValueError:
        logger.error("Значение находится за пределами допустимого интервала: {val}".format(val=message.text))
        bot.send_message(message.chat.id, "Количество отелей не может быть меньше 0 и больше 25!")
        query_total_hotels(message)

    else:
        bot.send_message(message.chat.id, "Подбираю отели. Ожидайте...")
        hotels = users[message.chat.id].search_hotels(URL_BASIC=URL_BASIC, HEADERS=HEADERS)
        hotels_object_list = list()
        for i_hotel in hotels.get("data", {}).get("body", {}).get("searchResults", {}).get("results", ''):
            hotels_object_list.append(Hotel(all_info=i_hotel))
        try:
            if not hotels_object_list:
                raise ValueError

        except ValueError:
            logger.error("Отелей не найдено")
            bot.send_message(message.chat.id, "По вашему запросу ничего не найдено")

        get_info(message, hotels_object_list)


@logging_decor
@logger.catch
def get_info(message, hotels_list) -> None:
    """
    Функция из списка отелей формирует инфо и выдает в телеграмм пользователю
    """
    for i_object in hotels_list:
        bot.send_message(chat_id=message.chat.id, text=i_object, parse_mode="Markdown")


@bot.message_handler(content_types=['text'])
@logging_decor
def say_hello(message) -> None:
    """
    Функция обрабатывает сообщения от пользователя (Привет, Спасибо) и
    отвечает на них соответствующей фразой
    """
    new_user(message)

    if re.search(r"\bпривет\w*", message.text, flags=re.IGNORECASE):
        bot.send_message(message.chat.id, "Привет, чем я могу Вам помочь?\n\nЧтобы узнать подробнее о моих "
                                          "возможностях - нажмите /help.")
    elif re.search(r"\bспасибо\w*", message.text, flags=re.IGNORECASE):
        bot.send_message(message.chat.id, "Я рад, что смог Вам помочь!")
    else:
        bot.send_message(message.chat.id, "Я Вас не понимаю.\nЕсли хотите узнать, что я умею нажмите /help.")


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
